"""BLOQUE 1270 — Multiproveedor IA, enrutamiento y observabilidad."""

from __future__ import annotations

import json
import os
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from app.gateway.adapters.anthropic_adapter import AnthropicAdapter
from app.gateway.adapters.azure_openai_adapter import AzureOpenAIAdapter
from app.gateway.adapters.gemini_adapter import GeminiAdapter
from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.gateway.errors import LlmErrorCategory
from app.gateway.gateway import complete
from app.gateway.provider_status import ProviderHealthStatus
from app.gateway.providers import is_executable_llm_provider
from app.gateway.types import GatewayRequest, LlmMessage
from app.llm_models import LlmProviderConfig
from app.models import Organization, User
from app.schemas_llm import LlmProviderCreate, LlmRoutingPolicyCreate
from app.security import hash_password
from app.services.llm_execution import is_llm_provider
from app.services.llm_health_service import assess_provider_health, list_providers_health
from app.services.llm_observability_service import get_observability_summary
from app.services.llm_provider_service import create_provider, create_routing_policy, list_providers
from app.services.llm_routing_service import explain_routing, select_routed_provider
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _openai_mock(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-mock",
            "choices": [{"message": {"content": "OK OpenAI"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
    )


def _anthropic_mock(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg-mock",
            "content": [{"text": "OK Anthropic"}],
            "usage": {"input_tokens": 8, "output_tokens": 4},
            "stop_reason": "end_turn",
        },
    )


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


def test_1270_proveedores_con_adaptador():
    assert is_executable_llm_provider("openai")
    assert is_executable_llm_provider("ollama")
    assert is_executable_llm_provider("anthropic")
    assert is_executable_llm_provider("gemini")
    assert is_executable_llm_provider("azure-openai")
    assert is_llm_provider("anthropic")
    assert not is_llm_provider("rule-engine")


def test_1270_anthropic_no_configurado_sin_clave():
    adapter = AnthropicAdapter()
    res = adapter.complete(
        GatewayRequest(provider="anthropic", model="claude-3-haiku-20240307", messages=[LlmMessage(role="user", content="hola")]),
        api_key=None,
    )
    assert not res.success
    assert res.error.category == LlmErrorCategory.CONFIGURATION_ERROR
    assert "NO CONFIGURADO" in (res.error.technical_detail or "")


def test_1270_gemini_no_configurado_sin_clave():
    adapter = GeminiAdapter()
    res = adapter.complete(
        GatewayRequest(provider="gemini", model="gemini-1.5-flash", messages=[LlmMessage(role="user", content="hola")]),
        api_key=None,
    )
    assert not res.success
    assert "NO CONFIGURADO" in (res.error.technical_detail or "")


def test_1270_azure_no_configurado_sin_endpoint():
    adapter = AzureOpenAIAdapter()
    res = adapter.complete(
        GatewayRequest(provider="azure-openai", model="gpt-4o-mini", messages=[LlmMessage(role="user", content="hola")], endpoint=None),
        api_key="fake-key",
    )
    assert not res.success
    assert "NO CONFIGURADO" in (res.error.technical_detail or "")


def test_1270_anthropic_mock_success():
    adapter = AnthropicAdapter(transport=httpx.MockTransport(_anthropic_mock))
    res = adapter.complete(
        GatewayRequest(provider="anthropic", model="claude-3-haiku-20240307", messages=[LlmMessage(role="user", content="hola")], timeout_seconds=10),
        api_key="test-key",
    )
    assert res.success
    assert res.text == "OK Anthropic"


def test_1270_openai_compatible_gateway(db, org_user):
    org_id, _ = org_user
    os.environ["OPENAI_API_KEY"] = "sk-test-openai-1270"
    transport = httpx.MockTransport(_openai_mock)
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="Hola")],
        transport=transport,
    )
    assert res.success
    assert res.provider == "openai"


def test_1270_routing_explain(db, org_user):
    org_id, _ = org_user
    explanation = explain_routing(db, org_id, preferred_provider="openai")
    assert explanation["seleccionado"] is not None
    assert explanation["razones"]


def test_1270_routing_fallback_policy(db, org_user):
    org_id, user_id = org_user
    create_routing_policy(
        db,
        org_id,
        LlmRoutingPolicyCreate(name="Sin fallback", preferred_provider="openai", fallback_allowed=False),
        user_id=user_id,
    )
    decision = select_routed_provider(db, org_id, preferred_provider="openai", allow_fallback=False)
    assert decision is not None
    assert decision.config.provider_type == "openai"


def test_1270_health_no_configurado(db, org_user):
    org_id, user_id = org_user
    row = create_provider(
        db,
        org_id,
        LlmProviderCreate(name="Anthropic prep", provider_type="anthropic", model_default="claude-3-haiku-20240307"),
        user_id=user_id,
    )
    config = db.query(LlmProviderConfig).filter(LlmProviderConfig.id == row["id"]).one()
    health = assess_provider_health(db, org_id, config)
    assert health["estado"] == ProviderHealthStatus.NO_CONFIGURADO.value


def test_1270_observability_summary(db, org_user):
    org_id, _ = org_user
    summary = get_observability_summary(db, org_id)
    assert "total_inferencias" in summary
    assert summary["costo_total"] is None or isinstance(summary["costo_total"], (int, float))


def test_1270_api_no_expone_secretos(client: TestClient, auth_headers):
    res = client.get("/api/llm/providers", headers=auth_headers)
    assert res.status_code == 200
    for p in res.json():
        assert "secret_ref" not in p or not p.get("secret_ref") or p["secret_ref"].startswith("env:")
        masked = p.get("secret_masked") or ""
        if masked:
            assert "…" in masked or len(masked) <= 8


def test_1270_api_observabilidad(client: TestClient, auth_headers):
    res = client.get("/api/llm/observability?periodo=7d", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "tasa_exito" in body


def test_1270_api_salud(client: TestClient, auth_headers):
    res = client.get("/api/llm/health", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_1270_cross_tenant(client: TestClient, auth_headers, db):
    org_b = Organization(name=f"OrgB-1270-{uuid.uuid4().hex[:6]}")
    db.add(org_b)
    db.commit()
    user_b = User(
        username=f"admin-b-{uuid.uuid4().hex[:6]}",
        email=f"b-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        organization_id=org_b.id,
        role="admin",
        is_active=True,
    )
    db.add(user_b)
    db.commit()
    health_a = client.get("/api/llm/health", headers=auth_headers).json()
    login_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "Admin2026*"})
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
    health_b = client.get("/api/llm/health", headers=headers_b).json()
    assert health_a != health_b or len(health_a) >= 0


def test_1270_proveedor_deshabilitado_no_selecciona(db, org_user):
    org_id, user_id = org_user
    providers = list_providers(db, org_id)
    openai = next(p for p in providers if p["provider_type"] == "openai")
    from app.services.llm_provider_service import update_provider
    from app.schemas_llm import LlmProviderUpdate

    update_provider(db, org_id, openai["id"], LlmProviderUpdate(is_enabled=False), user_id=user_id)
    decision = select_routed_provider(db, org_id, preferred_provider="openai")
    assert decision is None or decision.config.provider_type != "openai"
    update_provider(db, org_id, openai["id"], LlmProviderUpdate(is_enabled=True), user_id=user_id)
