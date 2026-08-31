"""NX04 — Wrapper CAS/concurrencia gate (reusa lógica existente + assert BD ≤1 aprobación)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.test_gate_post6d_correcciones import (
    _assert_single_effective_approval,
    _concurrent_solicitar_aprobacion,
    _employee_with_failures,
    _open_finding,
    _run_audit,
    _start_improvement_trace,
)
from app.config import settings
from conftest import TestingSessionLocal

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _admin_user(db):
    from app.models import User

    return db.query(User).filter(User.username == settings.bootstrap_admin_username).first()


def test_nx04_cas_wrapper_single_approval_under_concurrency(client: TestClient, token: str):
    """Reutiliza helpers gate post-6D: máximo una aprobación efectiva bajo concurrencia."""
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(
            db, admin.organization_id, admin.id, f"nx04-{uuid.uuid4().hex[:4]}"
        )
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    trace_id = _start_improvement_trace(client, token, finding_id)
    results = _concurrent_solicitar_aprobacion(client, token, trace_id, keys=("nx04-a", "nx04-b"))
    assert len(results) == 2
    assert sum(1 for r in results if r["status_code"] == 200 and not r["body"].get("idempotent")) <= 1

    db = TestingSessionLocal()
    try:
        _assert_single_effective_approval(db, org_id, emp_id, trace_id)
    finally:
        db.close()
