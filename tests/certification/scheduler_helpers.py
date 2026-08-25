"""Helpers compartidos para certificación scheduler/timeout (PR #6)."""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from unittest.mock import patch

from sqlalchemy.orm import Session

from app.enums import ScheduleType
from app.models import Organization, User
from app.security import hash_password
from app.services.automation_service import activate_automation, create_automation, run_now
from app.schemas_automation import AutomationCreate, RecurrenceConfig
from tests.conftest import TestingSessionLocal


def fractional_run_with_timeout(fn, _configured_timeout, actual_timeout: float):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        return future.result(timeout=actual_timeout)
    except FuturesTimeout as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise TimeoutError(f"timeout_seconds excedido ({actual_timeout}s)") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def create_org_user(db: Session, org_name: str) -> tuple[Organization, User]:
    org = Organization(name=org_name)
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        username=f"user-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Admin2026*"),
        role="admin",
    )
    db.add(user)
    db.commit()
    return org, user


def automation_payload(**overrides) -> AutomationCreate:
    data = {
        "name": f"Cert {uuid.uuid4().hex[:6]}",
        "objective": "Certificación timeout",
        "schedule_type": ScheduleType.DAILY,
        "timezone": "UTC",
        "recurrence": RecurrenceConfig(hour=10, minute=0),
        "workflow": {"tool": "docint", "estimated_cost": 0.5},
        "max_retries": 0,
        "retry_delay_seconds": 0,
        "timeout_seconds": 1,
        "max_runs_per_day": 5,
        "requires_approval": False,
    }
    data.update(overrides)
    return AutomationCreate(**data)


def run_timeout_scenario(
    route_fn,
    *,
    actual_timeout: float = 0.15,
    wait_after: float = 0.35,
):
    import time

    db = TestingSessionLocal()
    try:
        org, user = create_org_user(db, f"Cert-{uuid.uuid4().hex[:6]}")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=automation_payload(timeout_seconds=1, max_retries=0),
        )
        activate_automation(db, auto, user.id)
        timeout_patch = lambda fn, ts: fractional_run_with_timeout(fn, ts, actual_timeout)
        with patch("app.services.automation_service.route_task", side_effect=route_fn), patch(
            "app.services.automation_service._run_with_timeout",
            side_effect=timeout_patch,
        ):
            run = run_now(db, auto, user.id)
        time.sleep(wait_after)
        db.refresh(run)
        return run
    finally:
        db.close()
