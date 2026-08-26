"""Tests CURSOR-810 — Automatizaciones y programador V1."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.automation_models import Automation, AutomationRun
from app.enums import AutomationRunStatus, AutomationStatus, AutomationTriggerType, ScheduleType
from app.models import Organization, User
from app.orchestration_models import ApprovalRequest, FinOpsRecord, WorkPlan
from app.security import hash_password
from app.services.automation_scheduler import _tick
from app.services.automation_service import (
    activate_automation,
    create_automation,
    pause_automation,
    recalculate_all_active,
    refresh_next_run,
    run_now,
    sync_run_from_work_plan,
    trigger_internal_event,
    trigger_run,
)
from app.services.recurrence import compute_next_run, occurrence_key
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


def _automation_payload(**overrides) -> AutomationCreate:
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


def test_create_edit_activate_pause(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_automation_payload().model_dump(mode="json"))
    assert res.status_code == 201
    auto = res.json()
    assert auto["status"] == "DRAFT"

    res = client.put(
        f"/api/automations/{auto['id']}",
        headers=auth_headers,
        json={"name": "Auto actualizada"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Auto actualizada"

    res = client.post(f"/api/automations/{auto['id']}/activate", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"
    assert res.json()["next_run_at"] is not None

    res = client.post(f"/api/automations/{auto['id']}/pause", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "PAUSED"


def test_run_now_orchestrator_integration(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_automation_payload().model_dump(mode="json"))
    auto_id = res.json()["id"]
    client.post(f"/api/automations/{auto_id}/activate", headers=auth_headers)

    res = client.post(f"/api/automations/{auto_id}/run-now", headers=auth_headers)
    assert res.status_code == 200
    run = res.json()
    assert run["work_plan_id"]
    assert run["status"] in ("SUCCEEDED", "WAITING_APPROVAL", "FAILED")

    db = TestingSessionLocal()
    try:
        plan = db.query(WorkPlan).filter(WorkPlan.id == run["work_plan_id"]).first()
        assert plan is not None
    finally:
        db.close()


def test_recurrence_types():
    now = datetime.now(timezone.utc)
    nxt = compute_next_run(
        schedule_type=ScheduleType.DAILY,
        tz_name="UTC",
        start_at=now,
        end_at=None,
        recurrence_config={"hour": 12, "minute": 0},
        after=now,
    )
    assert nxt and nxt > now

    one = compute_next_run(
        schedule_type=ScheduleType.ONE_TIME,
        tz_name="UTC",
        start_at=now + timedelta(hours=2),
        end_at=None,
        recurrence_config={},
        after=now,
    )
    assert one is not None


def test_idempotency_no_double_execution():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Idem Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        when = datetime.now(timezone.utc)
        r1 = trigger_run(db, automation=auto, user_id=user.id, trigger_source="MANUAL", scheduled_for=when)
        r2 = trigger_run(db, automation=auto, user_id=user.id, trigger_source="MANUAL", scheduled_for=when)
        assert r1.id == r2.id
    finally:
        db.close()


def test_max_runs_per_day_skipped():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Limit Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_automation_payload(max_runs_per_day=1),
        )
        activate_automation(db, auto, user.id)
        run_now(db, auto, user.id)
        skipped = run_now(db, auto, user.id)
        assert skipped.status == AutomationRunStatus.SKIPPED
    finally:
        db.close()


def test_tenant_isolation(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b, user_b = _create_org_user(db, "Org B")
        auto_b = create_automation(db, org_id=org_b.id, user_id=user_b.id, data=_automation_payload())
        auto_b_id = auto_b.id
    finally:
        db.close()

    res = client.get(f"/api/automations/{auto_b_id}", headers=auth_headers)
    assert res.status_code == 404


def test_permissions_viewer_denied_create(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Viewer Org")
        user.role = "viewer"
        db.commit()
        login = client.post("/api/auth/login", json={"username": user.username, "password": "Admin2026*"})
        token = login.json()["access_token"]
        headers = auth_header(token)
    finally:
        db.close()

    res = client.post("/api/automations", headers=headers, json=_automation_payload().model_dump(mode="json"))
    assert res.status_code == 403


def test_audit_trail_on_create(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_automation_payload().model_dump(mode="json"))
    assert res.status_code == 201
    logs = client.get("/api/audit/logs", headers=auth_headers)
    assert any("automation.created" in row["action"] for row in logs.json())


def test_list_runs_and_get_run(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_automation_payload().model_dump(mode="json"))
    auto_id = res.json()["id"]
    run_res = client.post(f"/api/automations/{auto_id}/run-now", headers=auth_headers)
    run_id = run_res.json()["id"]

    runs = client.get(f"/api/automations/{auto_id}/runs", headers=auth_headers)
    assert runs.status_code == 200
    assert len(runs.json()) >= 1

    one = client.get(f"/api/automation-runs/{run_id}", headers=auth_headers)
    assert one.status_code == 200


def test_scheduler_tick_due_automation():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Sched Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
        _tick()
        runs = db.query(AutomationRun).filter(AutomationRun.automation_id == auto.id).all()
        assert len(runs) >= 1
    finally:
        db.close()


def test_recalculate_next_run_on_activate():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Recalc Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        assert auto.next_run_at is not None
        pause_automation(db, auto, user.id)
        assert auto.next_run_at is None
    finally:
        db.close()


def test_occurrence_key_stable():
    dt = datetime(2026, 8, 24, 10, 0, tzinfo=timezone.utc)
    assert occurrence_key(dt) == "20260824T100000Z"


def test_weekly_monthly_interval_recurrence():
    now = datetime.now(timezone.utc)
    weekly = compute_next_run(
        schedule_type=ScheduleType.WEEKLY,
        tz_name="UTC",
        start_at=now,
        end_at=None,
        recurrence_config={"hour": 8, "minute": 30, "weekdays": [0, 2, 4]},
        after=now,
    )
    assert weekly and weekly > now

    monthly = compute_next_run(
        schedule_type=ScheduleType.MONTHLY,
        tz_name="UTC",
        start_at=now,
        end_at=None,
        recurrence_config={"hour": 9, "minute": 0, "day_of_month": 15},
        after=now,
    )
    assert monthly and monthly > now

    interval = compute_next_run(
        schedule_type=ScheduleType.INTERVAL,
        tz_name="UTC",
        start_at=now,
        end_at=None,
        recurrence_config={"interval_minutes": 30},
        after=now,
        last_run_at=now,
    )
    assert interval and interval > now


def test_timezone_recurrence():
    now = datetime.now(timezone.utc)
    nxt = compute_next_run(
        schedule_type=ScheduleType.DAILY,
        tz_name="America/Bogota",
        start_at=now,
        end_at=None,
        recurrence_config={"hour": 7, "minute": 0},
        after=now,
    )
    assert nxt is not None


def test_missed_run_skip_on_recalculate():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Missed Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_automation_payload(missed_run_policy="SKIP"),
        )
        activate_automation(db, auto, user.id)
        auto.next_run_at = datetime.now(timezone.utc) - timedelta(days=2)
        db.commit()
        recalculate_all_active(db)
        db.refresh(auto)
        now = datetime.now(timezone.utc)
        next_run = auto.next_run_at
        if next_run is not None and next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=timezone.utc)
        assert next_run is None or next_run > now
    finally:
        db.close()


def test_internal_event_trigger():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Event Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_automation_payload(
                trigger_type=AutomationTriggerType.INTERNAL_EVENT,
                schedule_type=None,
                recurrence={"event_type": "rips.validated"},
            ),
        )
        activate_automation(db, auto, user.id)
        runs = trigger_internal_event(db, org_id=org.id, event_type="rips.validated", user_id=user.id)
        assert len(runs) == 1
        assert runs[0].trigger_source == AutomationTriggerType.INTERNAL_EVENT
    finally:
        db.close()


def test_duplicate_automation(client: TestClient, auth_headers):
    res = client.post("/api/automations", headers=auth_headers, json=_automation_payload().model_dump(mode="json"))
    auto_id = res.json()["id"]
    dup = client.post(f"/api/automations/{auto_id}/duplicate", headers=auth_headers)
    assert dup.status_code == 201
    assert dup.json()["status"] == "DRAFT"
    assert "copia" in dup.json()["name"].lower()


def test_approval_sync_from_work_plan():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Approval Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        if run.status == AutomationRunStatus.WAITING_APPROVAL and run.work_plan_id:
            synced = sync_run_from_work_plan(db, work_plan_id=run.work_plan_id, plan_status="COMPLETED")
            assert synced and synced.status == AutomationRunStatus.SUCCEEDED
    finally:
        db.close()


def test_finops_linkage_on_run():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "FinOps Org")
        auto = create_automation(db, org_id=org.id, user_id=user.id, data=_automation_payload())
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        if run.work_plan_id:
            db.add(
                FinOpsRecord(
                    organization_id=org.id,
                    work_plan_id=run.work_plan_id,
                    cost=1.25,
                    model_name="test-model",
                    provider="test",
                )
            )
            db.commit()
            synced = sync_run_from_work_plan(db, work_plan_id=run.work_plan_id, plan_status="COMPLETED")
            assert synced and synced.cost_reference == 1.25
    finally:
        db.close()


def test_retry_on_failure():
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Retry Org")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_automation_payload(max_retries=1, retry_delay_seconds=0, workflow={"tool": "missing-tool"}),
        )
        activate_automation(db, auto, user.id)
        run = run_now(db, auto, user.id)
        assert run.attempt >= 1
    finally:
        db.close()
