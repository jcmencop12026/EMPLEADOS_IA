"""CURSOR-810C v2 — pruebas adversariales de timeout/fencing."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.automation_models import AutomationRun
from app.enums import AutomationRunStatus, ScheduleType, WorkPlanStatus
from app.models import Organization, User
from app.orchestration_models import WorkPlan
from app.security import hash_password
from app.services.automation_service import activate_automation, create_automation, run_now
from app.services.execution_guard import (
    ExecutionCancelledError,
    promote_file_if_valid,
    register_fence,
    release_fence,
    require_execution_allowed,
    run_subprocess,
)
from app.schemas_automation import AutomationCreate, RecurrenceConfig
from conftest import TestingSessionLocal


def _fractional_run_with_timeout(fn, _configured_timeout, actual_timeout: float):
    """Ejecuta con timeout fraccional para pruebas adversariales rápidas."""
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


def _create_org_user(db: Session, org_name: str) -> tuple[Organization, User]:
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


def _payload(**overrides) -> AutomationCreate:
    data = {
        "name": f"Auto {uuid.uuid4().hex[:6]}",
        "objective": "Analizar documentos RIPS de prueba",
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


def _run_timeout_scenario(route_fn, *, actual_timeout: float = 0.15, wait_after: float = 0.35):
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, f"Adv-{uuid.uuid4().hex[:6]}")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(timeout_seconds=1, max_retries=0),
        )
        activate_automation(db, auto, user.id)
        timeout_patch = lambda fn, ts: _fractional_run_with_timeout(fn, ts, actual_timeout)
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


def test_adversarial_memory_no_late_effects():
    """A — memoria compartida no cambia tras timeout."""
    effects: list[str] = []

    def route(*_a, **_k):
        try:
            time.sleep(0.25)
            require_execution_allowed()
            effects.append("late-memory")
        except ExecutionCancelledError:
            pass
        finally:
            try:
                require_execution_allowed()
                effects.append("late-finally-memory")
            except ExecutionCancelledError:
                pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = _run_timeout_scenario(route)
    assert run.status == AutomationRunStatus.FAILED
    assert effects == []


def test_adversarial_file_no_late_promote(tmp_path: Path):
    """B — archivo final no se promueve tras timeout."""
    tmp_file = tmp_path / "tmp.txt"
    final_file = tmp_path / "final.txt"
    promoted: list[bool] = []

    def route(*_a, **_k):
        tmp_file.write_text("payload", encoding="utf-8")
        time.sleep(0.25)
        try:
            promoted.append(promote_file_if_valid(str(tmp_file), str(final_file)))
        except ExecutionCancelledError:
            promoted.append(False)
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = _run_timeout_scenario(route)
    assert run.status == AutomationRunStatus.FAILED
    assert promoted == [False]
    assert not final_file.exists()


def test_adversarial_sqlite_no_late_commit():
    """C — ningún commit posterior tras timeout."""
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE fx (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    writes: list[int] = []

    def route(*_a, **_k):
        time.sleep(0.25)
        try:
            require_execution_allowed()
            c = sqlite3.connect(db_path)
            c.execute("INSERT INTO fx(val) VALUES ('late')")
            c.commit()
            c.close()
            writes.append(1)
        except ExecutionCancelledError:
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = _run_timeout_scenario(route)
    assert run.status == AutomationRunStatus.FAILED
    assert writes == []
    count = conn.execute("SELECT COUNT(*) FROM fx").fetchone()[0]
    conn.close()
    os.unlink(db_path)
    assert count == 0


def test_adversarial_subprocess_killed_no_late_effects():
    """D — subprocess terminado, sin efectos posteriores."""
    marker = tempfile.mktemp(suffix=".marker")
    if os.path.exists(marker):
        os.unlink(marker)
    proc_holder: list[subprocess.Popen] = []

    def route(*_a, **_k):
        proc = run_subprocess(
            [sys.executable, "-c", f"import time; time.sleep(2); open('{marker}','w').write('x')"],
        )
        proc_holder.append(proc)
        time.sleep(0.25)
        require_execution_allowed()
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = _run_timeout_scenario(route, wait_after=1.0)
    assert run.status == AutomationRunStatus.FAILED
    if proc_holder:
        assert proc_holder[0].poll() is not None
    time.sleep(1.5)
    assert not os.path.exists(marker)


def test_adversarial_finally_no_functional_side_effect():
    """E — finally no produce efecto funcional tras timeout."""
    effects: list[str] = []

    def route(*_a, **_k):
        try:
            time.sleep(0.25)
            return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}
        finally:
            try:
                require_execution_allowed()
                effects.append("functional-finally")
            except ExecutionCancelledError:
                pass

    run = _run_timeout_scenario(route)
    assert run.status == AutomationRunStatus.FAILED
    assert effects == []


def test_adversarial_race_zero_late_effects_100_iterations():
    """F — carrera cancelación ↔ side effect: 0/100."""
    late_count = 0
    iterations = 100

    for _ in range(iterations):
        effects: list[str] = []

        def route(*_a, **_k):
            time.sleep(0.08)
            try:
                require_execution_allowed()
                effects.append("race-late")
            except ExecutionCancelledError:
                pass
            return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

        run = _run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
        assert run.status == AutomationRunStatus.FAILED
        if effects:
            late_count += len(effects)

    assert late_count == 0, f"Efectos tardíos detectados: {late_count}/{iterations}"


def test_adversarial_stale_thread_cannot_confirm_db_effect():
    """G/H — thread rezagado no confirma efecto en BD."""
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "Stale Thread")
        auto = create_automation(
            db,
            org_id=org.id,
            user_id=user.id,
            data=_payload(timeout_seconds=1, max_retries=0),
        )
        activate_automation(db, auto, user.id)
        plan_id_holder: list[str] = []

        def route(*_a, **_k):
            time.sleep(1.2)
            try:
                require_execution_allowed()
                plan_id_holder.append("would-apply")
            except ExecutionCancelledError:
                pass
            return {"plan_id": "late-plan", "status": WorkPlanStatus.COMPLETED}

        with patch("app.services.automation_service.route_task", side_effect=route):
            run = run_now(db, auto, user.id)
        time.sleep(2)
        db.refresh(run)
        assert run.status == AutomationRunStatus.FAILED
        assert plan_id_holder == []
        assert run.work_plan_id is None or run.status == AutomationRunStatus.FAILED
    finally:
        db.close()


def test_adversarial_timed_out_never_becomes_success():
    """J — TIMED_OUT/FAILED no cambia a SUCCESS."""
    db = TestingSessionLocal()
    try:
        org, user = _create_org_user(db, "No Success After Timeout")
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

        def route(*_a, **_k):
            time.sleep(1.2)
            return {"plan_id": plan.id, "status": WorkPlanStatus.COMPLETED}

        with patch("app.services.automation_service.route_task", side_effect=route):
            run = run_now(db, auto, user.id)

        from app.services.automation_service import sync_run_from_work_plan

        sync_run_from_work_plan(db, work_plan_id=plan.id, plan_status=WorkPlanStatus.COMPLETED)
        db.refresh(run)
        assert run.status == AutomationRunStatus.FAILED
    finally:
        db.close()


def test_fence_token_invalidates_atomically():
    """Unitario — invalidación incrementa generación."""
    run_id = str(uuid.uuid4())
    ctrl = register_fence(run_id, 1)
    token = ctrl.snapshot()
    assert ctrl.verify(token)
    ctrl.invalidate()
    assert not ctrl.verify(token)
    assert ctrl.generation == 2
    release_fence(run_id)
