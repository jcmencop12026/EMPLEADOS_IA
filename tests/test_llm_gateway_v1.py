"""Tests LLM Gateway V1 — Paquete B."""

from __future__ import annotations

import json
import os
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient

from app.finops_models import FinOpsRate
from app.gateway.adapters.ollama_adapter import OllamaAdapter
from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.gateway.errors import LlmErrorCategory
from app.gateway.gateway import complete
from app.gateway.secrets import build_env_secret_ref, mask_secret, resolve_secret, sanitize_for_log
from app.gateway.types import GatewayRequest, LlmMessage
from app.llm_models import LlmInferenceLog, LlmProviderConfig
from app.models import User
from app.orchestration_models import AIEmployee, EmployeeModelPolicy
from app.schemas_llm import LlmProviderCreate
from app.services.llm_execution import is_llm_provider, run_llm_for_task, should_use_llm
from app.services.llm_provider_service import create_provider
from conftest import TestingSessionLocal, auth_header


def _openai_mock(request: httpx.Request) -> httpx.Response:
    if "api.openai.com" in str(request.url):
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-mock",
                "choices": [{"message": {"content": "OK desde OpenAI"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
            },
        )
    return httpx.Response(404)


def _openai_auth_error(request: httpx.Request) -> httpx.Response:
    return httpx.Response(401, json={"error": {"message": "Invalid API key", "code": "invalid_api_key"}})


def _openai_rate_limit(request: httpx.Request) -> httpx.Response:
    return httpx.Response(429, json={"error": {"message": "Rate limit", "code": "rate_limit_exceeded"}})


def _ollama_mock(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/api/chat"):
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "OK desde Ollama"},
                "done": True,
                "prompt_eval_count": 5,
                "eval_count": 3,
            },
        )
    return httpx.Response(404)


def _ollama_unavailable(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused")


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def org_user(db):
    user = db.query(User).filter(User.username == "admin").one()
    return user.organization_id, user.id


def test_secret_masking_and_sanitize():
    assert mask_secret("sk-abcdefghijklmnop") == "sk-a…op"
    assert "***" in sanitize_for_log("api_key=sk-abcdefghijklmnop12345")


def test_is_llm_provider():
    assert is_llm_provider("openai")
    assert is_llm_provider("ollama")
    assert not is_llm_provider("rule-engine")
    assert not is_llm_provider(None)


def test_openai_adapter_success():
    transport = httpx.MockTransport(_openai_mock)
    adapter = OpenAIAdapter(transport=transport)
    req = GatewayRequest(
        provider="openai",
        model="gpt-4o-mini",
        messages=[LlmMessage(role="user", content="Hola")],
        timeout_seconds=10,
        trace_id="trace-1",
    )
    res = adapter.complete(req, api_key="sk-test-key-1234567890")
    assert res.success
    assert res.text == "OK desde OpenAI"
    assert res.tokens_in == 12
    assert res.tokens_out == 8


def test_openai_adapter_auth_error():
    transport = httpx.MockTransport(_openai_auth_error)
    adapter = OpenAIAdapter(transport=transport)
    req = GatewayRequest(provider="openai", model="gpt-4o-mini", messages=[LlmMessage(role="user", content="x")], timeout_seconds=5)
    res = adapter.complete(req, api_key="bad-key")
    assert not res.success
    assert res.error.category == LlmErrorCategory.AUTH_ERROR


def test_openai_adapter_rate_limit():
    transport = httpx.MockTransport(_openai_rate_limit)
    adapter = OpenAIAdapter(transport=transport)
    req = GatewayRequest(provider="openai", model="gpt-4o-mini", messages=[LlmMessage(role="user", content="x")], timeout_seconds=5)
    res = adapter.complete(req, api_key="sk-test")
    assert res.error.category == LlmErrorCategory.RATE_LIMIT


def test_openai_adapter_no_key():
    adapter = OpenAIAdapter()
    req = GatewayRequest(provider="openai", model="gpt-4o-mini", messages=[LlmMessage(role="user", content="x")])
    res = adapter.complete(req, api_key=None)
    assert res.error.category == LlmErrorCategory.CONFIGURATION_ERROR


def test_ollama_adapter_success():
    transport = httpx.MockTransport(_ollama_mock)
    adapter = OllamaAdapter(transport=transport)
    req = GatewayRequest(
        provider="ollama",
        model="llama3.2",
        messages=[LlmMessage(role="user", content="Hola")],
        endpoint="http://127.0.0.1:11434",
        timeout_seconds=10,
    )
    res = adapter.complete(req)
    assert res.success
    assert "Ollama" in res.text


def test_ollama_adapter_unavailable():
    transport = httpx.MockTransport(_ollama_unavailable)
    adapter = OllamaAdapter(transport=transport)
    req = GatewayRequest(
        provider="ollama",
        model="llama3.2",
        messages=[LlmMessage(role="user", content="x")],
        endpoint="http://127.0.0.1:11434",
        timeout_seconds=5,
    )
    res = adapter.complete(req)
    assert res.error.category == LlmErrorCategory.PROVIDER_UNAVAILABLE


def test_gateway_fallback_openai_to_ollama(db, org_user):
    org_id, _ = org_user
    os.environ["OPENAI_API_KEY"] = "sk-test-fallback-key"

    openai_cfg = db.query(LlmProviderConfig).filter(
        LlmProviderConfig.organization_id == org_id,
        LlmProviderConfig.provider_type == "openai",
    ).first()
    ollama_cfg = db.query(LlmProviderConfig).filter(
        LlmProviderConfig.organization_id == org_id,
        LlmProviderConfig.provider_type == "ollama",
    ).first()
    assert openai_cfg and ollama_cfg

    def handler(request: httpx.Request) -> httpx.Response:
        if "api.openai.com" in str(request.url):
            return httpx.Response(429, json={"error": {"message": "rate", "code": "rate_limit_exceeded"}})
        if request.url.path.endswith("/api/chat"):
            return httpx.Response(
                200,
                json={"message": {"content": "fallback ok"}, "done": True, "prompt_eval_count": 1, "eval_count": 1},
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="test fallback")],
        preferred_provider="openai",
        preferred_model="gpt-4o-mini",
        transport=transport,
    )
    assert res.success
    assert res.fallback_used
    assert res.provider == "ollama"
    assert res.initial_error is not None


def test_gateway_all_providers_failed(db, org_user):
    org_id, _ = org_user
    os.environ["OPENAI_API_KEY"] = "sk-test"

    def fail_handler(request: httpx.Request) -> httpx.Response:
        if "api.openai.com" in str(request.url):
            return httpx.Response(429, json={"error": {"message": "rate", "code": "rate_limit_exceeded"}})
        if request.url.path.endswith("/api/chat"):
            return httpx.Response(404, json={"error": "model not found"})
        return httpx.Response(500)

    transport = httpx.MockTransport(fail_handler)
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="fail")],
        preferred_provider="openai",
        transport=transport,
    )
    assert not res.success
    assert res.error.category == LlmErrorCategory.ALL_PROVIDERS_FAILED


def test_disabled_provider_not_used(db, org_user):
    org_id, _ = org_user
    openai_cfg = db.query(LlmProviderConfig).filter(
        LlmProviderConfig.organization_id == org_id,
        LlmProviderConfig.provider_type == "openai",
    ).one()
    openai_cfg.is_enabled = False
    db.commit()

    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="x")],
        preferred_provider="openai",
    )
    assert not res.success or res.provider != "openai"

    openai_cfg.is_enabled = True
    db.commit()


def test_finops_on_llm_execution(db, org_user):
    org_id, user_id = org_user
    os.environ["OPENAI_API_KEY"] = "sk-finops-test-key"

    employee = AIEmployee(
        organization_id=org_id,
        code="llm-emp-test",
        name="Empleado LLM Test",
        specialty="general",
        model_provider="openai",
        model_name="gpt-4o-mini",
        lifecycle_status="ACTIVE",
    )
    db.add(employee)
    db.flush()
    db.add(EmployeeModelPolicy(employee_id=employee.id, preferred_provider="openai", preferred_model="gpt-4o-mini"))
    db.add(
        FinOpsRate(
            organization_id=org_id,
            provider="openai",
            model_service="gpt-4o-mini",
            category="Modelo IA",
            price_input=Decimal("0.001"),
            price_output=Decimal("0.002"),
            currency="USD",
            active=True,
        )
    )
    db.commit()

    transport = httpx.MockTransport(_openai_mock)
    output = run_llm_for_task(
        db,
        organization_id=org_id,
        employee=employee,
        user_prompt="Calcular costo",
        user_id=user_id,
        transport=transport,
    )
    assert output.get("source") == "llm"
    assert output.get("response")
    assert output.get("tokens_total") == 20

    from app.orchestration_models import FinOpsRecord

    records = db.query(FinOpsRecord).filter(FinOpsRecord.employee_id == employee.id).all()
    assert len(records) >= 1
    assert records[-1].tokens_in == 12
    assert records[-1].tokens_out == 8


def test_coordinator_llm_employee(db, client: TestClient, token: str, org_user):
    org_id, _ = org_user
    employee = AIEmployee(
        organization_id=org_id,
        code="coord-llm",
        name="Coord LLM",
        specialty="general",
        model_provider="openai",
        model_name="gpt-4o-mini",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
    )
    db.add(employee)
    db.commit()
    os.environ["OPENAI_API_KEY"] = "sk-coord-test"

    from app.services.coordinator import _run_execution
    from app.orchestration_models import EmployeeTask, WorkPlan

    plan = WorkPlan(
        organization_id=org_id,
        user_id=db.query(User).filter(User.username == "admin").one().id,
        correlation_id="test-corr-llm",
        request="Analiza este caso",
        objective="test",
        status="RUNNING",
    )
    db.add(plan)
    db.flush()
    task = EmployeeTask(
        organization_id=org_id,
        work_plan_id=plan.id,
        employee_id=employee.id,
        title="LLM task",
        executor_type="AI_AGENT",
        status="RUNNING",
        inputs_json=json.dumps({"request": "Analiza este caso"}),
    )
    db.add(task)
    db.commit()

    from unittest.mock import patch

    transport = httpx.MockTransport(_openai_mock)
    with patch("app.gateway.gateway.get_adapter") as mock_get:
        mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(transport=httpx.MockTransport(_openai_mock))
        output = _run_execution(
            db,
            employee=employee,
            tool=None,
            tool_code="docint",
            inputs={"request": "Analiza este caso"},
            plan=plan,
            task=task,
            user_id=db.query(User).filter(User.username == "admin").one().id,
        )
    assert output.get("source") == "llm"
    assert output.get("response")


def test_api_providers_no_secret_exposed(client: TestClient, token: str):
    res = client.get("/api/llm/providers", headers=auth_header(token))
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    for item in items:
        body = json.dumps(item)
        assert "sk-" not in body or item.get("secret_masked")


def test_api_test_connection_mock(client: TestClient, token: str, db, org_user):
    org_id, _ = org_user
    os.environ["OPENAI_API_KEY"] = "sk-api-test-key"
    provider = db.query(LlmProviderConfig).filter(
        LlmProviderConfig.organization_id == org_id,
        LlmProviderConfig.provider_type == "openai",
    ).one()

    from unittest.mock import patch

    with patch(
        "app.gateway.gateway.get_adapter",
        lambda pt, transport=None: OpenAIAdapter(transport=httpx.MockTransport(_openai_mock)),
    ):
        res = client.post(f"/api/llm/providers/{provider.id}/test", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "disponible"


def test_inference_audit_log(db, org_user):
    org_id, _ = org_user
    os.environ["OPENAI_API_KEY"] = "sk-audit"
    transport = httpx.MockTransport(_openai_mock)
    complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="audit")],
        preferred_provider="openai",
        transport=transport,
    )
    logs = db.query(LlmInferenceLog).filter(LlmInferenceLog.organization_id == org_id).all()
    assert len(logs) >= 1
    assert logs[-1].trace_id
    assert logs[-1].tokens_total == 20


def test_should_use_llm_executor():
    from app.enums import ExecutorType

    assert should_use_llm(None, ExecutorType.AI_AGENT)
    emp = AIEmployee(
        organization_id="x",
        code="e",
        name="e",
        specialty="s",
        model_provider="openai",
    )
    assert should_use_llm(emp, ExecutorType.PYTHON)


def test_provider_create_service(db, org_user):
    org_id, user_id = org_user
    row = create_provider(
        db,
        org_id,
        LlmProviderCreate(
            name="Test Azure",
            provider_type="azure-openai",
            model_default="gpt-4",
            secret_env_var="AZURE_OPENAI_KEY",
        ),
        user_id=user_id,
    )
    assert row["provider_type"] == "azure-openai"
    assert row["secret_ref"] == build_env_secret_ref("AZURE_OPENAI_KEY")
    assert not resolve_secret(row["secret_ref"])  # env not set in test
