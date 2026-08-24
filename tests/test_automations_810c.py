"""CURSOR-810C — correcciones post-auditoría Codex."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.automation_models import Automation, AutomationRun
from app.enums import AutomationRunStatus, AutomationTriggerType, ScheduleType, WorkPlanStatus
from app.models import Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.services.automation_service import (
    activate_automation,
    create_automation,
    run_now,
    sync_run_from_work_plan,
    trigger_internal_event,
    update_automation,
)
from app.schemas_automation import AutomationCreate, AutomationUpdate, RecurrenceConfig
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


def _payload(**overrides) -> AutomationCreate:
    data = {
        "name": f"Auto {uuid.uuid4().hex[:6]}",
        "objective": "Analizar documentos RIPS de prueba",
        "schedule_type": ScheduleType.DAILY,
        "timezone": "UTC",
        "recurrence": RecurrenceConfig(hour=10, minute=0),
        "workflow": {"tool": "docint", "estimated_cost": 0.5},
        "max_retries": 2,
        "retry_delay_seconds": 0,
        "timeout_seconds": 2,
        "max_runs_per_day": 5,
        "requires_approval": False,
    }
    data.update(overrides)
    return AutomationCreate(**data)


def test_timeout_marks_failed_not_running():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Timeout 810C")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(timeout_seconds=1, max_retries=2, retry_delay_seconds=0),
        )
        activate_automation(db, auto, user.id)

        def slow_route(*_args, **_kwargs):
            time.sleep(2)
            return {"plan_id": "slow-plan", "status": WorkPlanStatus.COMPLETED}

        with patch("app.services.automation_service.route_task", side_effect=slow_route):
            run = run_now(db, auto, user.id)
        assert run.status == AutomationRunStatus.FAILED
        assert run.finished_at is not None
        assert "timeout" in (run.error or "").lower()
        assert run.attempt == 1
    finally:
        db.close()


def test_late_result_does_not_change_timeout_state():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Late Result")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(timeout_seconds=1, max_retries=0),
        )
        activate_automation(db, auto, user.id)

        plan = WorkPlan(
            organization_id=org.id,
            user_id=user.id,
            correlation_id=str(uuid.uuid4()),
            request="late",
            objective="late",
            status=WorkPlanStatus.COMPLETED,
        )
        db.add(plan)
        db.flush()

        def slow_route(*_args, **_kwargs):
            time.sleep(2)
            return {"plan_id": plan.id, "status": WorkPlanStatus.COMPLETED}

        with patch("app.services.automation_service.route_task", side_effect=slow_route):
            run = run_now(db, auto, user.id)
        assert run.status == AutomationRunStatus.FAILED
        run.work_plan_id = plan.id
        db.commit()

        sync_run_from_work_plan(db, work_plan_id=plan.id, plan_status=WorkPlanStatus.COMPLETED)
        db.refresh(run)
        assert run.status == AutomationRunStatus.FAILED
    finally:
        db.close()


def test_timeout_audit_event(client, auth_headers):
    body = _payload(timeout_seconds=1, max_retries=0).model_dump(mode="json")

    def slow_route(*_args, **_kwargs):
        time.sleep(2)
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    created = client.post("/api/automations", headers=auth_headers, json=body)
    auto_id = created.json()["id"]
    client.post(f"/api/automations/{auto_id}/activate", headers=auth_headers)
    with patch("app.services.automation_service.route_task", side_effect=slow_route):
        client.post(f"/api/automations/{auto_id}/run-now", headers=auth_headers)
    logs = client.get("/api/audit/logs", headers=auth_headers).json()
    assert "automation.timeout" in {row["action"] for row in logs}


def test_retry_delay_respected():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Retry Delay")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(max_retries=1, retry_delay_seconds=1, timeout_seconds=None),
        )
        activate_automation(db, auto, user.id)
        timestamps: list[float] = []

        def fail_route(*_args, **_kwargs):
            timestamps.append(time.monotonic())
            return {"plan_id": "x", "status": WorkPlanStatus.FAILED, "error": "fallo"}

        with patch("app.services.automation_service.route_task", side_effect=fail_route):
            run = run_now(db, auto, user.id)
        assert run.attempt == 2
        assert len(timestamps) == 2
        gap = timestamps[1] - timestamps[0]
        assert gap >= 0.9, f"retry delay too short: {gap:.3f}s"
    finally:
        db.close()


def test_internal_event_duplicate_idempotent():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Idem Event")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "doc.validated"},
            ),
        )
        activate_automation(db, auto, user.id)
        payload = {"idempotency_key": "evt-001", "source": "test"}
        with patch("app.services.automation_service.route_task") as mock_route:
            mock_route.return_value = {"plan_id": "p1", "status": WorkPlanStatus.COMPLETED}
            trigger_internal_event(db, org_id=org.id, event_type="doc.validated", payload=payload, user_id=user.id)
            trigger_internal_event(db, org_id=org.id, event_type="doc.validated", payload=payload, user_id=user.id)
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).all()
        assert len(runs) == 1
        assert mock_route.call_count == 1
    finally:
        db.close()


def test_internal_event_different_payload_executes_twice():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Diff Event")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "doc.validated"},
            ),
        )
        activate_automation(db, auto, user.id)
        with patch("app.services.automation_service.route_task") as mock_route:
            mock_route.return_value = {"plan_id": "p1", "status": WorkPlanStatus.COMPLETED}
            trigger_internal_event(
                db, org_id=org.id, event_type="doc.validated",
                payload={"idempotency_key": "a"}, user_id=user.id,
            )
            trigger_internal_event(
                db, org_id=org.id, event_type="doc.validated",
                payload={"idempotency_key": "b"}, user_id=user.id,
            )
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).all()
        assert len(runs) == 2
        assert mock_route.call_count == 2
    finally:
        db.close()


def test_wizard_edit_preserves_config(client, auth_headers):
    body = _payload(
        max_retries=3,
        retry_delay_seconds=45,
        timeout_seconds=90,
        requires_approval=True,
        workflow={"tool": "rips", "estimated_cost": 1.25},
    ).model_dump(mode="json")
    created = client.post("/api/automations", headers=auth_headers, json=body)
    assert created.status_code in (200, 201)
    auto_id = created.json()["id"]

    updated = client.put(
        f"/api/automations/{auto_id}",
        headers=auth_headers,
        json={"name": "Nombre editado solamente"},
    )
    assert updated.status_code == 200
    detail = client.get(f"/api/automations/{auto_id}", headers=auth_headers).json()
    assert detail["name"] == "Nombre editado solamente"
    assert detail["max_retries"] == 3
    assert detail["retry_delay_seconds"] == 45
    assert detail["timeout_seconds"] == 90
    assert detail["requires_approval"] is True
    assert detail["workflow"]["tool"] == "rips"
    assert detail["workflow"]["estimated_cost"] == 1.25
    assert detail["max_runs_per_day"] == 5


def test_wizard_edit_recurrence_preserved(client, auth_headers):
    body = _payload().model_dump(mode="json")
    body["recurrence"] = {"hour": 14, "minute": 30}
    body["timezone"] = "America/Bogota"
    created = client.post("/api/automations", headers=auth_headers, json=body)
    auto_id = created.json()["id"]

    client.put(
        f"/api/automations/{auto_id}",
        headers=auth_headers,
        json={"description": "Solo descripción"},
    )
    detail = client.get(f"/api/automations/{auto_id}", headers=auth_headers).json()
    assert detail["recurrence"]["hour"] == 14
    assert detail["recurrence"]["minute"] == 30
    assert detail["timezone"] == "America/Bogota"
