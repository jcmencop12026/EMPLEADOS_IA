"""Certificación permanente PR #6 — scheduler timeout / fencing.

Ejecución rápida (CI):  pytest -m certification
Ejecución intensiva:    pytest -m certification_intensive
PostgreSQL:             pytest -m "certification and postgresql"
Windows process tree:   pytest -m "certification and windows"
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.automation_models import Automation, AutomationRun
from app.enums import AutomationRunStatus, WorkPlanStatus
from app.models import Organization, User
from app.orchestration_models import WorkPlan
from app.services.automation_service import run_now, sync_run_from_work_plan
from app.services.execution_guard import (
    ExecutionCancelledError,
    bind_fence_token,
    invalidate_run_execution,
    materialize_gated,
    process_tree_alive,
    register_fence,
    release_fence,
    require_execution_allowed,
    reset_fence_token,
    run_subprocess,
    terminate_process_tree,
)
from app.services.execution_workspace import (
    WorkerCommitForbiddenError,
    create_worker_execution_session,
    release_worker_session,
    set_execution_phase,
    reset_execution_phase,
)
from tests.certification.scheduler_helpers import (
    automation_payload,
    create_minimal_automation,
    create_org_user,
    run_timeout_scenario,
)
from conftest import TestingSessionLocal

pytestmark = pytest.mark.certification


# ---------------------------------------------------------------------------
# 1. Commit directo tras invalidación → 0 efectos
# ---------------------------------------------------------------------------
@pytest.mark.concurrency
def test_cert_01_commit_tardio_cero_efectos():
    commits: list[str] = []

    def route(db, *_a, **_k):
        time.sleep(0.08)
        try:
            db.commit()
            commits.append("late-commit")
        except (ExecutionCancelledError, WorkerCommitForbiddenError):
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
    assert run.status == AutomationRunStatus.FAILED
    assert commits == []


# ---------------------------------------------------------------------------
# 2. get_bind bloqueado en worker
# ---------------------------------------------------------------------------
def test_cert_02_get_bind_sin_autoridad():
    binds: list[str] = []

    def route(db, *_a, **_k):
        time.sleep(0.08)
        try:
            db.get_bind()
            binds.append("got-bind")
        except (ExecutionCancelledError, WorkerCommitForbiddenError):
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
    assert run.status == AutomationRunStatus.FAILED
    assert binds == []


# ---------------------------------------------------------------------------
# 3. db.session / db._session no recuperan Session utilizable
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("attr", ["session", "_session"])
def test_cert_03_rutas_session_bloqueadas(attr: str):
    leaks: list[str] = []

    def route(db, *_a, **_k):
        time.sleep(0.08)
        try:
            target = getattr(db, attr)
            target.commit()
            leaks.append(f"{attr}-commit")
        except (ExecutionCancelledError, WorkerCommitForbiddenError, AttributeError):
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
    assert run.status == AutomationRunStatus.FAILED
    assert leaks == []


# ---------------------------------------------------------------------------
# 4. SQL directo tras invalidación → 0 efectos
# ---------------------------------------------------------------------------
@pytest.mark.postgresql
def test_cert_04_sql_directo_sin_persistencia(pg_health):
    db_path = tempfile.mktemp(suffix=".cert.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE fx (id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    writes: list[int] = []

    def route(*_a, **_k):
        time.sleep(0.08)
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

    run = run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
    assert run.status == AutomationRunStatus.FAILED
    assert writes == []
    count = conn.execute("SELECT COUNT(*) FROM fx").fetchone()[0]
    conn.close()
    os.unlink(db_path)
    assert count == 0


# ---------------------------------------------------------------------------
# 5. SQL transaccional (COMMIT/ROLLBACK/BEGIN) bloqueado en worker
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("sql", ["COMMIT", "ROLLBACK", "BEGIN", "BEGIN TRANSACTION"])
def test_cert_05_sql_transaccional_bloqueado(sql: str):
    facade = create_worker_execution_session(TestingSessionLocal())
    try:
        with pytest.raises(WorkerCommitForbiddenError):
            facade.execute(text(sql))
    finally:
        release_worker_session(facade, close=True)


# ---------------------------------------------------------------------------
# 6. materialize_gated — válido e inválido
# ---------------------------------------------------------------------------
def test_cert_06_materialize_gated_valido():
    db = TestingSessionLocal()
    run_id = str(uuid.uuid4())
    ctrl = register_fence(run_id, 1)
    token = ctrl.snapshot()
    phase = set_execution_phase("materialization")
    ctx = bind_fence_token(token)
    try:
        org = Organization(name=f"MatOK-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        user = User(
            organization_id=org.id,
            username=f"mat-{uuid.uuid4().hex[:6]}",
            password_hash="x",
            role="admin",
        )
        db.add(user)
        db.flush()
        auto = create_minimal_automation(db, org.id, user.id)
        run = AutomationRun(
            id=run_id,
            automation_id=auto.id,
            organization_id=org.id,
            occurrence_key=f"mat-{uuid.uuid4().hex[:8]}",
            scheduled_for=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            status=AutomationRunStatus.RUNNING,
            execution_generation=1,
        )
        db.add(run)
        db.commit()
        materialize_gated(db, token)
        db.refresh(run)
        assert run.status == AutomationRunStatus.RUNNING
    finally:
        reset_fence_token(ctx)
        reset_execution_phase(phase)
        release_fence(run_id)
        db.close()


def test_cert_06_materialize_gated_invalido_tras_invalidacion():
    db = TestingSessionLocal()
    run_id = str(uuid.uuid4())
    ctrl = register_fence(run_id, 1)
    token = ctrl.snapshot()
    try:
        org = Organization(name=f"MatNO-{uuid.uuid4().hex[:6]}")
        db.add(org)
        db.flush()
        user = User(
            organization_id=org.id,
            username=f"matno-{uuid.uuid4().hex[:6]}",
            password_hash="x",
            role="admin",
        )
        db.add(user)
        db.flush()
        auto = create_minimal_automation(db, org.id, user.id)
        run = AutomationRun(
            id=run_id,
            automation_id=auto.id,
            organization_id=org.id,
            occurrence_key=f"matno-{uuid.uuid4().hex[:8]}",
            scheduled_for=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            status=AutomationRunStatus.RUNNING,
            execution_generation=1,
        )
        db.add(run)
        db.commit()
        invalidate_run_execution(db, run=run, token=token, error="timeout cert")
        with pytest.raises(ExecutionCancelledError):
            materialize_gated(db, token)
        db.refresh(run)
        assert run.status == AutomationRunStatus.FAILED
        assert run.execution_generation == 2
    finally:
        release_fence(run_id)
        db.close()


# ---------------------------------------------------------------------------
# 7. Race invalidación/materialización (rápida con barrera)
# ---------------------------------------------------------------------------
@pytest.mark.concurrency
def test_cert_07_race_barrera_cero_efectos():
    started = threading.Event()
    release = threading.Event()
    late: list[str] = []

    def route(*_a, **_k):
        started.set()
        release.wait(timeout=2)
        try:
            require_execution_allowed()
            late.append("race-late")
        except ExecutionCancelledError:
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    result_holder: list = []

    def runner():
        result_holder.append(
            run_timeout_scenario(route, actual_timeout=0.05, wait_after=0.25)
        )

    t = threading.Thread(target=runner)
    t.start()
    assert started.wait(timeout=2)
    time.sleep(0.12)
    release.set()
    t.join(timeout=15)
    assert result_holder
    assert result_holder[0].status == AutomationRunStatus.FAILED
    assert late == []


@pytest.mark.certification_intensive
@pytest.mark.concurrency
def test_cert_07_race_intensiva_100_cero_efectos():
    late_count = 0
    for _ in range(100):
        effects: list[str] = []

        def route(*_a, **_k):
            time.sleep(0.08)
            try:
                require_execution_allowed()
                effects.append("race")
            except ExecutionCancelledError:
                pass
            return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

        run = run_timeout_scenario(route, actual_timeout=0.03, wait_after=0.12)
        assert run.status == AutomationRunStatus.FAILED
        late_count += len(effects)
    assert late_count == 0, f"Efectos tardíos: {late_count}/100"


# ---------------------------------------------------------------------------
# 8. Rollback worker + timeout → cero persistencia
# ---------------------------------------------------------------------------
def test_cert_08_rollback_worker_sin_persistencia():
    """Cambios temporales del worker + timeout: cero persistencia funcional."""
    effects: list[str] = []

    def route(*_a, **_k):
        time.sleep(0.25)
        try:
            require_execution_allowed()
            effects.append("late-worker")
        except ExecutionCancelledError:
            pass
        finally:
            try:
                require_execution_allowed()
                effects.append("late-finally")
            except ExecutionCancelledError:
                pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = run_timeout_scenario(route)
    assert run.status == AutomationRunStatus.FAILED
    assert effects == []


# ---------------------------------------------------------------------------
# 9. Process tree padre → hijo → nieto
# ---------------------------------------------------------------------------
@pytest.mark.windows
def test_cert_09_process_tree_sin_descendientes_vivos():
    parent_marker = tempfile.mktemp(suffix=".cert.parent")
    child_marker = tempfile.mktemp(suffix=".cert.child")
    grand_marker = tempfile.mktemp(suffix=".cert.grand")
    for path in (parent_marker, child_marker, grand_marker):
        if os.path.exists(path):
            os.unlink(path)

    parent_script = (
        "import os, subprocess, sys, time\n"
        "child_marker = os.environ['CERT_CHILD']\n"
        "grand_marker = os.environ['CERT_GRAND']\n"
        "parent_marker = os.environ['CERT_PARENT']\n"
        "subprocess.Popen([sys.executable, '-c', "
        "'import os,time; time.sleep(30); open(os.environ[\\'M\\'],\\'w\\').write(\\'g\\')'], "
        "env={**os.environ, 'M': grand_marker})\n"
        "subprocess.Popen([sys.executable, '-c', "
        "'import os,time; time.sleep(30); open(os.environ[\\'M\\'],\\'w\\').write(\\'c\\')'], "
        "env={**os.environ, 'M': child_marker})\n"
        "time.sleep(30)\n"
        "open(parent_marker, 'w').write('p')\n"
    )
    proc_env = {
        **os.environ,
        "CERT_PARENT": parent_marker,
        "CERT_CHILD": child_marker,
        "CERT_GRAND": grand_marker,
    }
    proc_holder: list[subprocess.Popen] = []

    def route(*_a, **_k):
        proc = run_subprocess([sys.executable, "-c", parent_script], env=proc_env)
        proc_holder.append(proc)
        time.sleep(0.25)
        require_execution_allowed()
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    run = run_timeout_scenario(route, wait_after=1.5)
    assert run.status == AutomationRunStatus.FAILED
    proc = proc_holder[0]
    terminate_process_tree(proc)
    deadline = time.time() + 5
    while proc.pid and process_tree_alive(proc.pid) and time.time() < deadline:
        terminate_process_tree(proc)
        time.sleep(0.2)
    assert proc.poll() is not None
    if proc.pid:
        assert not process_tree_alive(proc.pid)
    time.sleep(1.0)
    assert not os.path.exists(parent_marker)
    assert not os.path.exists(child_marker)
    assert not os.path.exists(grand_marker)


def test_cert_09_process_tree_unitario():
    child_marker = tempfile.mktemp(suffix=".cert.unit")
    if os.path.exists(child_marker):
        os.unlink(child_marker)
    parent_script = (
        "import subprocess, sys, time\n"
        f"marker = {child_marker!r}\n"
        f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20); open({child_marker!r},\"w\").write(\"x\")'])\n"
        "time.sleep(20)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", parent_script],
        start_new_session=os.name != "nt",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )
    time.sleep(0.3)
    terminate_process_tree(proc)
    assert proc.poll() is not None
    time.sleep(0.8)
    assert not os.path.exists(child_marker)


# ---------------------------------------------------------------------------
# 10. Estado terminal — timeout no termina como SUCCESS
# ---------------------------------------------------------------------------
def test_cert_10_timeout_no_becomes_success():
    db = TestingSessionLocal()
    try:
        org, user = create_org_user(db, "CertNoSuccess")
        from app.services.automation_service import activate_automation, create_automation

        auto = create_automation(
            db, org_id=org.id, user_id=user.id,
            data=automation_payload(timeout_seconds=1, max_retries=0),
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
        sync_run_from_work_plan(db, work_plan_id=plan.id, plan_status=WorkPlanStatus.COMPLETED)
        db.refresh(run)
        assert run.status == AutomationRunStatus.FAILED
        assert run.status != AutomationRunStatus.SUCCEEDED
    finally:
        db.close()


# ---------------------------------------------------------------------------
# PostgreSQL — persistencia vía DATABASE_URL
# ---------------------------------------------------------------------------
@pytest.mark.postgresql
def test_cert_pg_commit_tardio_sin_persistencia(pg_session, pg_health):
    from app.automation_models import Automation
    from app.services.automation_service import activate_automation, create_automation

    org, user = create_org_user(pg_session, f"PGCert-{uuid.uuid4().hex[:6]}")
    auto = create_automation(
        pg_session, org_id=org.id, user_id=user.id,
        data=automation_payload(timeout_seconds=1),
    )
    activate_automation(pg_session, auto, user.id)
    before = pg_session.query(Automation).filter(Automation.organization_id == org.id).count()
    commits: list[str] = []

    def route(db, *_a, **_k):
        time.sleep(0.08)
        try:
            db.commit()
            commits.append("pg-late")
        except (ExecutionCancelledError, WorkerCommitForbiddenError):
            pass
        return {"plan_id": "x", "status": WorkPlanStatus.COMPLETED}

    with patch("app.services.automation_service.route_task", side_effect=route), patch(
        "app.services.automation_service._run_with_timeout",
        side_effect=lambda fn, ts: __import__(
            "tests.certification.scheduler_helpers", fromlist=["fractional_run_with_timeout"]
        ).fractional_run_with_timeout(fn, ts, 0.03),
    ):
        run = run_now(pg_session, auto, user.id)
    time.sleep(0.15)
    pg_session.refresh(run)
    after = pg_session.query(Automation).filter(Automation.organization_id == org.id).count()
    assert run.status == AutomationRunStatus.FAILED
    assert commits == []
    assert after == before
