"""Correcciones pre-release V1 — providers, FinOps, onboarding, errores seguros."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.gateway.errors import LlmErrorCategory
from app.gateway.gateway import complete
from app.gateway.types import LlmMessage
from app.llm_models import LlmProviderConfig
from app.models import Organization, User
from app.orchestration_models import AIEmployee, EmployeeModelPolicy
from app.services.llm_execution import run_llm_for_task
from app.services.tenant_service import create_organization
from conftest import TestingSessionLocal, auth_header


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


def _openai_mock(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-pr",
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        },
    )


def _auth_error(request: httpx.Request) -> httpx.Response:
    return httpx.Response(401, json={"error": {"message": "Invalid API key", "code": "invalid_api_key"}})


@pytest.mark.parametrize("provider", ["anthropic", "gemini", "azure-openai"])
def test_non_executable_provider_returns_configuration_error(db, org_user, provider):
    org_id, _ = org_user
    db.add(
        LlmProviderConfig(
            organization_id=org_id,
            name=f"Prov {provider}",
            provider_type=provider,
            model_default="model-x",
            is_enabled=True,
            priority=1,
        )
    )
    db.commit()
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="hola")],
        preferred_provider=provider,
        require_explicit_preferred=True,
    )
    assert not res.success
    assert res.error is not None
    assert res.error.category == LlmErrorCategory.CONFIGURATION_ERROR
    assert "technical_detail" not in res.error.to_public_dict()


def test_invalid_explicit_preferred_provider_configuration_error(db, org_user):
    org_id, _ = org_user
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="hola")],
        preferred_provider="anthropic",
        require_explicit_preferred=True,
    )
    assert not res.success
    assert res.error.category == LlmErrorCategory.CONFIGURATION_ERROR


def test_finops_failure_is_audited_not_silent(db, org_user, monkeypatch):
    org_id, user_id = org_user
    monkeypatch.setenv("OPENAI_API_KEY", "sk-finops-audit-test-key")
    employee = AIEmployee(
        organization_id=org_id,
        code=f"finops-{uuid.uuid4().hex[:6]}",
        name="FinOps audit",
        specialty="general",
        model_provider="openai",
        model_name="gpt-4o-mini",
        lifecycle_status="ACTIVE",
    )
    db.add(employee)
    db.commit()
    with patch("app.services.llm_execution.registrar_consumo", side_effect=RuntimeError("finops down")):
        with patch("app.gateway.gateway.get_adapter") as mock_get:
            mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
                transport=httpx.MockTransport(_openai_mock)
            )
            output = run_llm_for_task(
                db,
                organization_id=org_id,
                employee=employee,
                user_prompt="test",
                user_id=user_id,
                transport=httpx.MockTransport(_openai_mock),
            )
    assert output.get("source") == "llm"
    assert output.get("finops_registration_failed") is True
    from app.models import AuditLog

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "finops.registration.failed")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit is not None
    assert "trace_id" in (audit.detail or "")
    assert "sk-" not in (audit.detail or "")


def test_public_error_hides_technical_detail(client: TestClient, token: str, db, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-public-error-test")
    with patch("app.gateway.gateway.get_adapter") as mock_get:
        mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
            transport=httpx.MockTransport(_auth_error)
        )
        res = client.post(
            "/api/llm/complete",
            headers=auth_header(token),
            json={"prompt": "hola", "include_knowledge": False},
        )
    assert res.status_code == 200
    body = res.json()
    assert body.get("error") is not None
    assert "technical_detail" not in body["error"]


@pytest.mark.parametrize(
    ("handler", "expected_category"),
    [
        (_auth_error, LlmErrorCategory.AUTH_ERROR),
        (
            lambda _req: httpx.Response(
                429, json={"error": {"message": "Rate limit", "code": "rate_limit_exceeded"}}
            ),
            LlmErrorCategory.RATE_LIMIT,
        ),
        (
            lambda _req: httpx.Response(404, json={"error": {"message": "model missing", "code": "model_not_found"}}),
            LlmErrorCategory.MODEL_NOT_FOUND,
        ),
        (
            lambda _req: httpx.Response(200, text="not-json {{{"),
            LlmErrorCategory.INVALID_RESPONSE,
        ),
    ],
)
def test_public_errors_hide_technical_detail_categories(
    db, org_user, monkeypatch, handler, expected_category
):
    org_id, _ = org_user
    monkeypatch.setenv("OPENAI_API_KEY", "sk-category-test-key")
    with patch("app.gateway.gateway.get_adapter") as mock_get:
        mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
            transport=httpx.MockTransport(handler)
        )
        res = complete(
            db,
            organization_id=org_id,
            messages=[LlmMessage(role="user", content="hola")],
            preferred_provider="openai",
            require_explicit_preferred=True,
            transport=httpx.MockTransport(handler),
            enable_fallback=False,
        )
    assert not res.success
    assert res.error is not None
    assert res.error.category == expected_category
    public = res.error.to_public_dict()
    assert "technical_detail" not in public
    assert "secret.internal" not in str(public)


def test_public_configuration_error_hides_technical_detail(db, org_user):
    org_id, _ = org_user
    res = complete(
        db,
        organization_id=org_id,
        messages=[LlmMessage(role="user", content="hola")],
        preferred_provider="anthropic",
        require_explicit_preferred=True,
    )
    assert not res.success
    assert res.error.category == LlmErrorCategory.CONFIGURATION_ERROR
    assert "technical_detail" not in res.error.to_public_dict()


def test_public_provider_unavailable_hides_technical_detail(db, org_user, monkeypatch):
    org_id, _ = org_user
    monkeypatch.setenv("OPENAI_API_KEY", "sk-unavailable-test")

    def unavailable(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with patch("app.gateway.gateway.get_adapter") as mock_get:
        mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
            transport=httpx.MockTransport(unavailable)
        )
        res = complete(
            db,
            organization_id=org_id,
            messages=[LlmMessage(role="user", content="hola")],
            preferred_provider="openai",
            require_explicit_preferred=True,
            transport=httpx.MockTransport(unavailable),
            enable_fallback=False,
        )
    assert not res.success
    assert res.error.category == LlmErrorCategory.PROVIDER_UNAVAILABLE
    assert "technical_detail" not in res.error.to_public_dict()


def test_onboarding_success_creates_org_admin_and_bootstrap(client: TestClient, token: str):
    slug = f"ok-{uuid.uuid4().hex[:8]}"
    res = client.post(
        "/api/platform/organizations",
        headers=auth_header(token),
        json={
            "name": f"Empresa OK {slug}",
            "slug": slug,
            "admin_username": f"adm-{slug}",
            "admin_password": "OkOnboard*1",
        },
    )
    assert res.status_code == 201
    db = TestingSessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == slug).one()
        admin = db.query(User).filter(User.username == f"adm-{slug}").one()
        from app.orchestration_models import Capability

        caps = db.query(Capability).filter(Capability.organization_id == org.id).count()
        assert caps > 0
        assert admin.organization_id == org.id
    finally:
        db.close()


def test_onboarding_rollback_on_admin_failure(db: Session):
    actor = db.query(User).filter(User.username == "admin").one()
    slug = f"rb-{uuid.uuid4().hex[:8]}"
    with patch("app.services.tenant_service.hash_password", side_effect=RuntimeError("admin fail")):
        with pytest.raises(RuntimeError):
            create_organization(
                db,
                name=f"Rollback {slug}",
                slug=slug,
                timezone="UTC",
                admin_username=f"adm-{slug}",
                admin_password="Rollback*1",
                admin_email=None,
                admin_full_name=None,
                actor_id=actor.id,
            )
    assert db.query(Organization).filter(Organization.slug == slug).count() == 0
    assert db.query(User).filter(User.username == f"adm-{slug}").count() == 0
    db.rollback()


def test_duplicate_slug_returns_409(client: TestClient, token: str):
    slug = f"dup-{uuid.uuid4().hex[:8]}"
    payload = {
        "name": f"Empresa A {slug}",
        "slug": slug,
        "admin_username": f"adm-a-{slug}",
        "admin_password": "DupTest*1",
    }
    first = client.post("/api/platform/organizations", headers=auth_header(token), json=payload)
    assert first.status_code == 201
    second = client.post(
        "/api/platform/organizations",
        headers=auth_header(token),
        json={
            "name": f"Empresa B {slug}",
            "slug": slug,
            "admin_username": f"adm-b-{slug}",
            "admin_password": "DupTest*1",
        },
    )
    assert second.status_code == 409
    assert "identificador" in second.json()["detail"].lower()


def test_explicit_policy_invalid_provider_no_silent_fallback(db, org_user):
    org_id, user_id = org_user
    employee = AIEmployee(
        organization_id=org_id,
        code=f"pol-{uuid.uuid4().hex[:6]}",
        name="Policy",
        specialty="general",
        model_provider="openai",
        model_name="gpt-4o-mini",
        lifecycle_status="ACTIVE",
    )
    db.add(employee)
    db.flush()
    db.add(
        EmployeeModelPolicy(
            employee_id=employee.id,
            preferred_provider="anthropic",
            preferred_model="claude",
        )
    )
    db.commit()
    output = run_llm_for_task(
        db,
        organization_id=org_id,
        employee=employee,
        user_prompt="test",
        user_id=user_id,
    )
    assert output.get("error") is not None
    assert output["error"]["category"] == LlmErrorCategory.CONFIGURATION_ERROR
