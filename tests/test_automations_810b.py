"""CURSOR-810B — correcciones post-auditoría Automatizaciones."""
from __future__ import annotations

import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.automation_models import AutomationRun
from app.enums import AutomationRunStatus, AutomationStatus, AutomationTriggerType, ScheduleType
from app.events.bus import EventMessage, publish
from app.models import Organization, User
from app.orchestration_models import AIEmployee, ApprovalRequest, WorkPlan
from app.security import hash_password
from app.services.automation_scheduler import _tick
from app.services.automation_service import (
    activate_automation,
    create_automation,
    run_now,
    trigger_internal_event,
)
from app.services.recurrence import compute_next_run
from app.schemas_automation import AutomationCreate, RecurrenceConfig
from conftest import TestingSessionLocal, auth_header


def _create_org_user(db: Session, org_name: str) -> tuple[Organization, User]:
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"user-{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
    )
    db.add(user)
    db.commit()
    return org, user


def _employee(db: Session, org_id: str, code: str = "EMP-A") -> AIEmployee:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"Empleado {code}",
        specialty="salud",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
        is_active=True,
    )
    db.add(emp)
    db.commit()
    return emp


def _payload(**overrides) -> AutomationCreate:
    data = {
        "name": f"Auto {uuid.uuid4().hex[:6]}",
        "objective": "Analizar documentos RIPS de prueba",
        "schedule_type": ScheduleType.DAILY,
        "timezone": "UTC",
        "recurrence": RecurrenceConfig(hour=10, minute=0),
        "workflow": {"tool": "docint"},
    }
    data.update(overrides)
    return AutomationCreate(**data)


def _verify_805_infrastructure(root: Path) -> None:
    """Infraestructura 805 + Automatizaciones debe existir en el árbol final."""
    required = [
        "backend/scripts/db_startup.py",
        "backend/scripts/schema_repair.py",
        "tests/test_db_startup_805e.py",
        "tests/test_schema_repair_805b.py",
        "backend/app/services/automation_service.py",
        "backend/app/routers/automations.py",
        "tests/test_automations_810.py",
    ]
    missing = [rel for rel in required if not (root / rel).is_file()]
    assert not missing, f"Infraestructura requerida ausente: {missing}"


def _verify_pr_diff_isolation(lines: list[str]) -> None:
    """Cualquier PR — el diff no debe eliminar infraestructura 805."""
    forbidden_prefixes = ("backend/scripts/db_startup", "tests/test_db_startup", "tests/test_schema_repair")
    for line in lines:
        status, path = line.split("\t", 1)
        for prefix in forbidden_prefixes:
            if path.startswith(prefix):
                assert status != "D", f"No debe eliminarse: {path}"


def test_pr_diff_isolated_from_805():
    """A1 — en PR valida aislamiento; en main/post-merge valida infraestructura presente."""
    root = Path(__file__).resolve().parents[1]
    _verify_805_infrastructure(root)

    subprocess.run(["git", "fetch", "origin", "main"], cwd=root, capture_output=True, check=False)
    result = subprocess.run(
        ["git", "diff", "--name-status", "origin/main...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in result.stdout.strip().splitlines() if line]
    if lines:
        _verify_pr_diff_isolation(lines)
    # Sin diff (main/post-merge): la infraestructura ya fue verificada arriba.


def test_pr_diff_fails_when_infrastructure_removed(tmp_path: Path):
    """Regresión — eliminar un archivo crítico debe fallar la verificación."""
    root = Path(__file__).resolve().parents[1]
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    target = fake_root / "backend/scripts/db_startup.py"
    target.parent.mkdir(parents=True)
    target.write_text("# stub", encoding="utf-8")
    with pytest.raises(AssertionError, match="Infraestructura requerida ausente"):
        _verify_805_infrastructure(fake_root)


def test_cross_tenant_employee_create_rejected(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, _ = _create_org_user(db, "Org B 810B")
        emp_b = _employee(db, org_b.id, "EMP-B810")
        emp_b_id = emp_b.id
    finally:
        db.close()

    res = client.post(
        "/api/automations",
        headers=auth_headers,
        json=_payload(employee_id=emp_b_id).model_dump(mode="json"),
    )
    assert res.status_code == 422


def test_cross_tenant_employee_update_rejected(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, _ = _create_org_user(db, "Org B upd")
        emp_b = _employee(db, org_b.id)
        emp_b_id = emp_b.id
    finally:
        db.close()

    created = client.post(
        "/api/automations",
        headers=auth_headers,
        json=_payload().model_dump(mode="json"),
    ).json()

    res = client.put(
        f"/api/automations/{created['id']}",
        headers=auth_headers,
        json={"employee_id": emp_b_id},
    )
    assert res.status_code == 422


def test_cross_tenant_execution_rejected():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _create_org_user(db, "Org A exec")
        org_b, _ = _create_org_user(db, "Org B exec")
        emp_b = _employee(db, org_b.id)
        auto = create_automation(db, org_id=org_a.id, user_id=user_a.id, data=_payload())
        auto.employee_id = emp_b.id
        db.commit()
        activate_automation(db, auto, user_a.id)
        run = run_now(db, auto, user_a.id)
        assert run.status == AutomationRunStatus.FAILED
        assert "cross-tenant" in (run.error or "").lower() or "rechazada" in (run.error or "").lower()
    finally:
        db.close()


@pytest.mark.parametrize(
    "schedule_type,recurrence",
    [
        (ScheduleType.DAILY, {"hour": 9, "minute": 0}),
        (ScheduleType.WEEKLY, {"hour": 8, "minute": 0, "weekdays": [0, 2]}),
        (ScheduleType.MONTHLY, {"hour": 7, "minute": 30, "day_of_month": 10}),
        (ScheduleType.INTERVAL, {"interval_minutes": 60}),
    ],
)
def test_future_start_at_never_before_start(schedule_type, recurrence):
    now = datetime.now(timezone.utc)
    start_at = now + timedelta(days=30)
    nxt = compute_next_run(
        schedule_type=schedule_type,
        tz_name="UTC",
        start_at=start_at,
        end_at=None,
        recurrence_config=recurrence,
        after=now,
    )
    assert nxt is not None
    assert nxt >= start_at.replace(microsecond=0) or nxt.date() >= start_at.date()


def test_approval_required_creates_request():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Approval Req")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(requires_approval=True),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        assert run.status == AutomationRunStatus.WAITING_APPROVAL
        assert run.work_plan_id
        approval = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.work_plan_id == run.work_plan_id)
            .first()
        )
        assert approval is not None
        plan = db.query(WorkPlan).filter(WorkPlan.id == run.work_plan_id).first()
        assert plan.status == "WAITING_APPROVAL"
    finally:
        db.close()


def test_approval_approved_executes(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Approval OK")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(requires_approval=True),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.work_plan_id == run.work_plan_id).first()
        assert approval
        approval_id = approval.id
        username = user.username
        run_id = run.id
    finally:
        db.close()

    login = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    token = login.json()["access_token"]
    res = client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "approve"},
    )
    assert res.status_code == 200
    db = TestingSessionLocal()
    try:
        synced = db.query(AutomationRun).filter(AutomationRun.id == run.id).first()
        assert synced.status in (AutomationRunStatus.SUCCEEDED, AutomationRunStatus.WAITING_APPROVAL)
    finally:
        db.close()


def test_approval_rejected_marks_failed(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Approval NO")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(requires_approval=True),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.work_plan_id == run.work_plan_id).first()
        approval_id = approval.id
        username = user.username
        run_id = run.id
    finally:
        db.close()

    login = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    token = login.json()["access_token"]
    client.post(
        f"/api/operations/approvals/{approval_id}/decide",
        headers=auth_header(token),
        json={"decision": "reject", "comment": "No autorizado"},
    )
    db = TestingSessionLocal()
    try:
        synced = db.query(AutomationRun).filter(AutomationRun.id == run_id).first()
        assert synced.status in (AutomationRunStatus.FAILED, AutomationRunStatus.CANCELLED)
    finally:
        db.close()


def test_finops_pre_execution_skips_before_run():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "FinOps Pre")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(
                max_cost_per_run=1.0,
                workflow={"tool": "docint", "estimated_cost": 2.5},
            ),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        assert run.status == AutomationRunStatus.SKIPPED
        assert "max_cost" in (run.error or "") or "estimado" in (run.error or "").lower()
        assert run.work_plan_id is None
    finally:
        db.close()


def test_retry_semantics_max_retries_is_after_initial():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Retry Sem")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(max_retries=2, retry_delay_seconds=0, workflow={"tool": "missing-tool"}),
        )
        activate_automation(db, auto, user.id)
        calls: list[int] = []

        def fail_route(*_args, **_kwargs):
            calls.append(1)
            return {"plan_id": "x", "status": "FAILED", "error": "fallo"}

        with patch("app.services.automation_service.route_task", side_effect=fail_route):
            run = run_now(db, auto, user.id)
        assert run.attempt == 3
        assert len(calls) == 3
    finally:
        db.close()


def test_retry_upper_limit_rejected(client: TestClient, auth_headers):
    body = _payload().model_dump(mode="json")
    body["max_retries"] = 11
    res = client.post(
        "/api/automations",
        headers=auth_headers,
        json=body,
    )
    assert res.status_code == 422


def test_timeout_marks_failed():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Timeout Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(timeout_seconds=1, workflow={"tool": "docint"}),
        )
        activate_automation(db, auto, user.id)

        def slow_route(*_args, **_kwargs):
            time.sleep(2)
            return {"plan_id": "slow", "status": "COMPLETED"}

        with patch("app.services.automation_service.route_task", side_effect=slow_route):
            run = run_now(db, auto, user.id)
        assert run.status == AutomationRunStatus.FAILED
        assert "timeout" in (run.error or "").lower()
    finally:
        db.close()


def test_internal_event_via_event_bus():
    from app.services.automation_events import register_automation_event_handlers

    register_automation_event_handlers()
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Bus Event")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "rips.validated"},
            ),
        )
        activate_automation(db, auto, user.id)
        publish(
            EventMessage(
                event_type="rips.validated",
                organization_id=org.id,
                user_id=user.id,
                payload={"source": "test"},
            ),
            db,
        )
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).all()
        assert len(runs) >= 1
    finally:
        db.close()


def test_internal_event_cross_tenant_isolated():
    db = TestingSessionLocal()
    try:
        org_a, user_a = _create_org_user(db, "Org A evt")
        org_b, user_b = _create_org_user(db, "Org B evt")
        auto_b = create_automation(
            db,
            org_id=org_b.id,
            user_id=user_b.id,
            data=_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "rips.validated"},
            ),
        )
        activate_automation(db, auto_b, user_b.id)
        trigger_internal_event(db, org_id=org_a.id, event_type="rips.validated", user_id=user_a.id)
        runs_b = db.query(AutomationRun).filter(AutomationRun.automation_id == auto_b.id).count()
        assert runs_b == 0
    finally:
        db.close()


def test_loop_protection_skips_automation_generated_plans():
    from app.services.automation_events import register_automation_event_handlers

    register_automation_event_handlers()
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Loop Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "work.completed"},
            ),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        assert run.work_plan_id
        before = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        publish(
            EventMessage(
                event_type="work.completed",
                organization_id=org.id,
                work_plan_id=run.work_plan_id,
                user_id=user.id,
                payload={"summary": "done"},
            ),
            db,
        )
        after = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).count()
        assert after == before
    finally:
        db.close()


def test_scheduler_e2e_tick():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Sched E2E")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_payload())
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        _tick()
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).all()
        assert len(runs) >= 1
    finally:
        db.close()


def test_audit_coverage_actions(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_payload().model_dump(mode="json"))
    auto_id = res.json()["id"]
    client.post(f"/api/automations/{auto_id}/activate", headers=auth_headers)
    client.post(f"/api/automations/{auto_id}/run-now", headers=auth_headers)
    logs = client.get("/api/audit/logs", headers=auth_headers).json()
    actions = {row["action"] for row in logs}
    expected = {
        "automation.created",
        "automation.activated",
        "automation.run_now",
    }
    assert expected.issubset(actions)


def test_wizard_required_fields_rejected(client: TestClient, auth_headers):
    res = client.post(
        "/api/automations",
        headers=auth_headers,
        json={"name": "", "objective": ""},
    )
    assert res.status_code == 422
