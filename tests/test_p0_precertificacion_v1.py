"""P0 pre-certificación V1 — motor LLM y tenant inactivo en scheduler."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.automation_models import AutomationRun
from app.enums import ExecutorType
from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.llm_models import LlmInferenceLog
from app.models import Organization, User
from app.security import hash_password
from app.orchestration_models import AIEmployee, EmployeeTask, FinOpsRecord, WorkPlan
from app.services.automation_scheduler import _tick
from app.services.automation_service import activate_automation, create_automation, trigger_run
from app.services.coordinator import _run_execution
from app.services.llm_execution import is_llm_provider, should_use_llm
from app.schemas_automation import AutomationCreate, RecurrenceConfig
from app.enums import ScheduleType
from app.tenant_scope import ORG_STATUS_INACTIVE
from conftest import TestingSessionLocal, auth_header


def _openai_mock(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-p0",
            "choices": [{"message": {"content": "LLM OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
        },
    )


def _employee(
    db: Session,
    *,
    org_id: str,
    model_provider: str,
) -> AIEmployee:
    employee = AIEmployee(
        organization_id=org_id,
        code=f"p0-{uuid.uuid4().hex[:6]}",
        name="Empleado P0",
        specialty="general",
        model_provider=model_provider,
        model_name="gpt-4o-mini",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
    )
    db.add(employee)
    db.flush()
    return employee


def _execution_bundle(
    db: Session,
    *,
    executor_type: str,
    model_provider: str,
) -> tuple[str, AIEmployee, WorkPlan, EmployeeTask]:
    admin = db.query(User).filter(User.username == "admin").one()
    employee = _employee(db, org_id=admin.organization_id, model_provider=model_provider)
    plan = WorkPlan(
        organization_id=admin.organization_id,
        user_id=admin.id,
        correlation_id=str(uuid.uuid4()),
        request="Solicitud P0",
        objective="test",
        status="RUNNING",
    )
    db.add(plan)
    db.flush()
    task = EmployeeTask(
        organization_id=admin.organization_id,
        work_plan_id=plan.id,
        employee_id=employee.id,
        title="Tarea P0",
        executor_type=executor_type,
        status="RUNNING",
        inputs_json=json.dumps({"request": "Solicitud P0"}),
    )
    db.add(task)
    db.commit()
    return admin.id, employee, plan, task


def _llm_log_count(db: Session) -> int:
    return db.query(LlmInferenceLog).count()


def _llm_finops_count(db: Session) -> int:
    return db.query(FinOpsRecord).filter(FinOpsRecord.category == "Modelo IA").count()


def _run_and_assert_no_llm(db: Session, *, executor_type: str, model_provider: str) -> None:
    before_logs = _llm_log_count(db)
    before_finops = _llm_finops_count(db)
    user_id, employee, plan, task = _execution_bundle(
        db, executor_type=executor_type, model_provider=model_provider
    )
    output = _run_execution(
        db,
        employee=employee,
        tool=None,
        tool_code="docint",
        inputs={"request": "Solicitud P0"},
        plan=plan,
        task=task,
        user_id=user_id,
    )
    assert output.get("source") != "llm"
    assert _llm_log_count(db) == before_logs
    assert _llm_finops_count(db) == before_finops


def _automation_payload(**overrides) -> AutomationCreate:
    data = {
        "name": f"Auto P0 {uuid.uuid4().hex[:6]}",
        "objective": "Ejecución programada P0",
        "schedule_type": ScheduleType.DAILY,
        "timezone": "UTC",
        "recurrence": RecurrenceConfig(hour=10, minute=0),
        "workflow": {"tool": "docint"},
    }
    data.update(overrides)
    return AutomationCreate(**data)


def _create_org_user(db: Session, org_name: str) -> tuple[Organization, User]:
    org = Organization(name=org_name, slug=f"p0-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"p0-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("P0Tenant*1"),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user


@pytest.mark.parametrize(
    ("executor_type", "model_provider"),
    [
        (ExecutorType.RULE, "rule-engine"),
        (ExecutorType.PYTHON, "openai"),
        (ExecutorType.TOOL, "openai"),
        ("RULE", "docint"),
        ("PYTHON", "custom"),
    ],
    ids=["T-LLM-01", "T-LLM-02", "T-LLM-03", "T-LLM-04", "T-LLM-05"],
)
def test_t_llm_deterministic_executor_never_uses_llm(executor_type, model_provider):
    db = TestingSessionLocal()
    try:
        assert not should_use_llm(
            _employee(db, org_id=db.query(User).filter(User.username == "admin").one().organization_id, model_provider=model_provider),
            executor_type,
        )
        _run_and_assert_no_llm(db, executor_type=executor_type, model_provider=model_provider)
    finally:
        db.close()


def test_t_llm_06_ai_agent_openai_uses_llm():
    db = TestingSessionLocal()
    try:
        assert should_use_llm(
            _employee(
                db,
                org_id=db.query(User).filter(User.username == "admin").one().organization_id,
                model_provider="openai",
            ),
            ExecutorType.AI_AGENT,
        )
        user_id, employee, plan, task = _execution_bundle(
            db, executor_type=ExecutorType.AI_AGENT, model_provider="openai"
        )
        os.environ["OPENAI_API_KEY"] = "sk-p0-openai"
        before_logs = _llm_log_count(db)
        with patch("app.gateway.gateway.get_adapter") as mock_get:
            mock_get.side_effect = lambda pt, transport=None: OpenAIAdapter(
                transport=httpx.MockTransport(_openai_mock)
            )
            output = _run_execution(
                db,
                employee=employee,
                tool=None,
                tool_code="docint",
                inputs={"request": "Solicitud P0"},
                plan=plan,
                task=task,
                user_id=user_id,
            )
        assert output.get("source") == "llm"
        assert _llm_log_count(db) > before_logs
    finally:
        db.close()


def test_t_llm_07_ai_agent_ollama_uses_llm():
    db = TestingSessionLocal()
    try:
        assert is_llm_provider("ollama")
        assert should_use_llm(None, ExecutorType.AI_AGENT)
        user_id, employee, plan, task = _execution_bundle(
            db, executor_type=ExecutorType.AI_AGENT, model_provider="ollama"
        )
        employee.model_provider = "ollama"
        db.commit()

        def _ollama_mock(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "message": {"role": "assistant", "content": "Ollama OK"},
                    "done": True,
                    "prompt_eval_count": 3,
                    "eval_count": 2,
                },
            )

        from app.gateway.adapters.ollama_adapter import OllamaAdapter

        before_logs = _llm_log_count(db)
        with patch("app.gateway.gateway.get_adapter") as mock_get:
            mock_get.side_effect = lambda pt, transport=None: OllamaAdapter(
                transport=httpx.MockTransport(_ollama_mock)
            )
            output = _run_execution(
                db,
                employee=employee,
                tool=None,
                tool_code="docint",
                inputs={"request": "Solicitud P0"},
                plan=plan,
                task=task,
                user_id=user_id,
            )
        assert output.get("source") == "llm"
        assert _llm_log_count(db) > before_logs
    finally:
        db.close()


def test_t_llm_08_rule_python_tool_without_llm_provider():
    for provider in ("rule-engine", "python", "tool", None):
        assert not is_llm_provider(provider)
    db = TestingSessionLocal()
    try:
        _run_and_assert_no_llm(db, executor_type=ExecutorType.PYTHON, model_provider="rule-engine")
        _run_and_assert_no_llm(db, executor_type=ExecutorType.TOOL, model_provider="tool")
    finally:
        db.close()


def test_t_tenant_01_active_org_scheduler_creates_run():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "P0 Active Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        before = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        _tick()
        after = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        assert after > before
    finally:
        db.close()


def test_t_tenant_02_inactive_org_scheduler_skips_run():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "P0 Inactive Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        org.status = ORG_STATUS_INACTIVE
        db.commit()
        before = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        _tick()
        after = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        assert after == before
    finally:
        db.close()


def test_t_tenant_03_mixed_active_and_inactive_orgs():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _create_org_user(db, "P0 Mixed A")
        org_b, user_b = _create_org_user(db, "P0 Mixed B")
        auto_a = create_automation(db, org_id=org_a.id, user_id=user_a.id, data=_automation_payload())
        auto_b = create_automation(db, org_id=org_b.id, user_id=user_b.id, data=_automation_payload())
        activate_automation(db, auto_a, user_a.id)
        activate_automation(db, auto_b, user_b.id)
        auto_a.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        auto_b.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        org_b.status = ORG_STATUS_INACTIVE
        db.commit()
        before_a = db.query(AutomationRun).filter(AutomationRun.automation_id == auto_a.id).count()
        before_b = db.query(AutomationRun).filter(AutomationRun.automation_id == auto_b.id).count()
        _tick()
        after_a = db.query(AutomationRun).filter(AutomationRun.automation_id == auto_a.id).count()
        after_b = db.query(AutomationRun).filter(AutomationRun.automation_id == auto_b.id).count()
        assert after_a > before_a
        assert after_b == before_b
    finally:
        db.close()


def test_t_tenant_04_deactivate_after_create_skips_next_tick():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "P0 Deactivate Later")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        org.status = ORG_STATUS_INACTIVE
        db.commit()
        before = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        _tick()
        after = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        assert after == before
    finally:
        db.close()


def test_t_tenant_05_inactive_org_api_returns_403(client: TestClient, token: str):
    headers = auth_header(token)
    slug = f"p0-inact-{uuid.uuid4().hex[:6]}"
    created = client.post(
        "/api/platform/organizations",
        headers=headers,
        json={
            "name": f"Inactiva P0 {slug}",
            "slug": slug,
            "admin_username": f"adm-{slug}",
            "admin_password": "InactP0*1",
        },
    )
    assert created.status_code == 201
    org_id = created.json()["organization"]["id"]
    admin_username = created.json()["admin_username"]
    admin_token = client.post(
        "/api/auth/login",
        json={"username": admin_username, "password": "InactP0*1"},
    ).json()["access_token"]

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


def test_t_tenant_06_historical_runs_preserved_after_deactivation():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "P0 History Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        when = datetime.now(timezone.utc)
        historical = trigger_run(
            db,
            automation=auto,
            user_id=user.id,
            trigger_source="MANUAL",
            scheduled_for=when,
        )
        historical_id = historical.id
        org.status = ORG_STATUS_INACTIVE
        db.commit()
        preserved = db.query(AutomationRun).filter(AutomationRun.id == historical_id).one()
        assert preserved.id == historical_id
        before = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        _tick()
        after = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        assert after == before
    finally:
        db.close()
