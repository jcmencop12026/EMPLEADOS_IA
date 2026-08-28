"""Tests de integración V1 — convergencia paquetes A+B+C+D+E."""

from __future__ import annotations

import json
import os
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.llm_models import LlmInferenceLog
from app.models import Organization, Permission, Role, RolePermission, User
from app.orchestration_models import AIEmployee, FinOpsRecord, WorkPlan
from app.security import hash_password
from app.services.coordinator import _run_execution
from conftest import TestingSessionLocal, auth_header


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_limited_user(
    db: Session,
    *,
    permission_codes: set[str],
    org: Organization | None = None,
) -> tuple[str, str]:
    from app.seed_permissions import bootstrap_permissions

    bootstrap_permissions(db)
    if org is None:
        org = Organization(name=f"Int Org {uuid.uuid4().hex[:6]}", slug=f"int-{uuid.uuid4().hex[:8]}")
        db.add(org)
        db.flush()
    role_code = f"int-lim-{uuid.uuid4().hex[:6]}"
    role = Role(
        organization_id=org.id,
        code=role_code,
        name="Integración limitada",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()
    for code in permission_codes:
        perm = db.query(Permission).filter(Permission.code == code).first()
        assert perm is not None, code
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    username = f"int-{uuid.uuid4().hex[:6]}"
    password = "IntLim*2026"
    db.add(
        User(
            organization_id=org.id,
            username=username,
            password_hash=hash_password(password),
            role=role_code,
            status="ACTIVE",
            is_active=True,
        )
    )
    db.commit()
    return username, password


def _openai_mock(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-int",
            "choices": [{"message": {"content": "OK integración"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        },
    )


def test_a_superadmin_sees_companies(client: TestClient, token: str):
    res = client.get("/api/platform/organizations", headers=auth_header(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_b_user_without_permission_denied_companies(client: TestClient):
    db = TestingSessionLocal()
    try:
        username, password = _create_limited_user(db, permission_codes={"employee.view"})
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/platform/organizations", headers=headers)
    assert res.status_code == 403


def test_c_superadmin_sees_llm_providers(client: TestClient, token: str):
    res = client.get("/api/llm/providers", headers=auth_header(token))
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_d_unauthorized_user_denied_llm_providers(client: TestClient):
    db = TestingSessionLocal()
    try:
        username, password = _create_limited_user(db, permission_codes={"employee.view"})
    finally:
        db.close()
    headers = auth_header(_token(client, username, password))
    res = client.get("/api/llm/providers", headers=headers)
    assert res.status_code == 403


def test_e_tenant_a_cannot_see_tenant_b_llm_finops(client: TestClient):
    db = TestingSessionLocal()
    try:
        from app.seed_orchestration import bootstrap_orchestration
        from app.seed_permissions import bootstrap_permissions
        from app.seed_salud import bootstrap_salud

        def _create_tenant_user(db_sess, *, org_name: str):
            org = Organization(name=org_name, slug=f"tenant-{uuid.uuid4().hex[:8]}")
            db_sess.add(org)
            db_sess.flush()
            bootstrap_permissions(db_sess)
            bootstrap_orchestration(db_sess, org.id)
            bootstrap_salud(db_sess, org.id)
            user = User(
                organization_id=org.id,
                username=f"user-{uuid.uuid4().hex[:6]}",
                password_hash=hash_password("TenantC*Test1"),
                role="admin",
                status="ACTIVE",
                is_active=True,
            )
            db_sess.add(user)
            db_sess.commit()
            return org, user, "TenantC*Test1"

        org_a, user_a, _ = _create_tenant_user(db, org_name="LLM Fin A")
        org_b, user_b, password_b = _create_tenant_user(db, org_name="LLM Fin B")
        plan = WorkPlan(
            organization_id=org_a.id,
            user_id=user_a.id,
            correlation_id=str(uuid.uuid4()),
            request="req",
            objective="obj",
            status="READY",
        )
        db.add(plan)
        db.flush()
        db.add(
            FinOpsRecord(
                organization_id=org_a.id,
                work_plan_id=plan.id,
                provider="openai",
                category="Modelo IA",
                quantity=1,
                cost=5.5,
                tokens_in=10,
                tokens_out=5,
            )
        )
        db.add(
            LlmInferenceLog(
                organization_id=org_a.id,
                trace_id=str(uuid.uuid4()),
                provider="openai",
                model="gpt-4o-mini",
                tokens_in=10,
                tokens_out=5,
                tokens_total=15,
                status="OK",
            )
        )
        db.commit()
        plan_id = plan.id
        org_a_id = org_a.id
        username_b = user_b.username
    finally:
        db.close()

    headers_b = auth_header(_token(client, username_b, password_b))
    finops = client.get(
        "/api/finops/drill-down",
        headers=headers_b,
        params={"work_plan_id": plan_id},
    )
    assert finops.status_code == 404

    logs = client.get("/api/llm/inference-logs", headers=headers_b)
    assert logs.status_code == 200
    assert all(row.get("organization_id") != org_a_id for row in logs.json())


def test_f_llm_execution_preserves_organization_id(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        org_id = admin.organization_id
        employee = AIEmployee(
            organization_id=org_id,
            code=f"int-llm-{uuid.uuid4().hex[:6]}",
            name="Empleado integración",
            specialty="general",
            model_provider="openai",
            model_name="gpt-4o-mini",
            lifecycle_status="ACTIVE",
            status="DISPONIBLE",
        )
        db.add(employee)
        db.commit()
        employee_id = employee.id
    finally:
        db.close()

    os.environ["OPENAI_API_KEY"] = "sk-integration-test"
    from unittest.mock import patch

    with patch("app.gateway.gateway.get_adapter") as mock_get:
        mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
            transport=httpx.MockTransport(_openai_mock)
        )
        res = client.post(
            "/api/llm/complete",
            headers=auth_header(token),
            json={"prompt": "Hola integración", "employee_id": employee_id, "include_knowledge": False},
        )
    assert res.status_code == 200
    assert res.json().get("text")

    db = TestingSessionLocal()
    try:
        logs = (
            db.query(LlmInferenceLog)
            .filter(LlmInferenceLog.employee_id == employee_id)
            .order_by(LlmInferenceLog.created_at.desc())
            .all()
        )
        assert logs
        assert logs[0].organization_id == org_id
    finally:
        db.close()


def test_g_inactive_company_blocks_llm_api(client: TestClient, token: str):
    headers = auth_header(token)
    slug = f"llm-inact-{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={
            "name": f"Inactiva LLM {slug}",
            "slug": slug,
            "admin_username": f"adm-{slug}",
            "admin_password": "InactLLM*1",
        },
    )
    assert created.status_code == 201
    org_id = created.json()["organization"]["id"]
    admin_username = created.json()["admin_username"]
    admin_token = _token(client, admin_username, "InactLLM*1")

    deactivated = client.post(
        f"/api/platform/organizations/{org_id}/status",
        headers=headers,
        json={"status": "INACTIVE"},
    )
    assert deactivated.status_code == 200

    blocked = client.post(
        "/api/llm/complete",
        headers=auth_header(admin_token),
        json={"prompt": "No debe ejecutar", "include_knowledge": False},
    )
    assert blocked.status_code == 403
    assert "inactiva" in blocked.json()["detail"].lower()


def test_h_health_integrated(client: TestClient):
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "up"

    ready = client.get("/health/ready")
    assert ready.status_code in {200, 503}
    assert ready.json()["components"]["database"]["status"] == "up"

    health = client.get("/health")
    assert health.status_code in {200, 503}
    assert health.json()["components"]["database"]["status"] == "up"


def test_i_rule_python_tool_coexist(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        org_id = admin.organization_id
        rule_emp = AIEmployee(
            organization_id=org_id,
            code=f"rule-{uuid.uuid4().hex[:6]}",
            name="Rule engine",
            specialty="general",
            model_provider="rule-engine",
            lifecycle_status="ACTIVE",
            status="DISPONIBLE",
        )
        db.add(rule_emp)
        db.commit()
        provider = rule_emp.model_provider
    finally:
        db.close()

    from app.services.llm_execution import is_llm_provider, should_use_llm

    assert not is_llm_provider(provider)
    assert not should_use_llm(rule_emp)

    caps = client.get("/api/capabilities", headers=auth_header(token))
    assert caps.status_code == 200

    tools = client.get("/api/tools", headers=auth_header(token))
    assert tools.status_code == 200


def test_j_llm_path_with_mock_provider(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").one()
        org_id = admin.organization_id
        employee = AIEmployee(
            organization_id=org_id,
            code=f"coord-{uuid.uuid4().hex[:6]}",
            name="Coord integración",
            specialty="general",
            model_provider="openai",
            model_name="gpt-4o-mini",
            lifecycle_status="ACTIVE",
            status="DISPONIBLE",
        )
        db.add(employee)
        db.flush()
        plan = WorkPlan(
            organization_id=org_id,
            user_id=admin.id,
            correlation_id=str(uuid.uuid4()),
            request="Integración",
            objective="test",
            status="RUNNING",
        )
        db.add(plan)
        db.flush()
        from app.orchestration_models import EmployeeTask

        task = EmployeeTask(
            organization_id=org_id,
            work_plan_id=plan.id,
            employee_id=employee.id,
            title="LLM integración",
            executor_type="AI_AGENT",
            status="RUNNING",
            inputs_json=json.dumps({"request": "Integración"}),
        )
        db.add(task)
        db.commit()
        employee_id = employee.id
        plan_id = plan.id
        task_id = task.id
        user_id = admin.id
    finally:
        db.close()

    os.environ["OPENAI_API_KEY"] = "sk-coord-int"
    from unittest.mock import patch

    db = TestingSessionLocal()
    try:
        employee_obj = db.query(AIEmployee).filter(AIEmployee.id == employee_id).one()
        plan_obj = db.query(WorkPlan).filter(WorkPlan.id == plan_id).one()
        from app.orchestration_models import EmployeeTask

        task_obj = db.query(EmployeeTask).filter(EmployeeTask.id == task_id).one()
        with patch("app.gateway.gateway.get_adapter") as mock_get:
            mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
                transport=httpx.MockTransport(_openai_mock)
            )
            output = _run_execution(
                db=db,
                employee=employee_obj,
                tool=None,
                tool_code="docint",
                inputs={"request": "Integración"},
                plan=plan_obj,
                task=task_obj,
                user_id=user_id,
            )
    finally:
        db.close()
    assert output.get("source") == "llm"
    assert output.get("response")
