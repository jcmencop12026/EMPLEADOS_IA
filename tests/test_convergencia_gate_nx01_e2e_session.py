"""NX01 — E2E sesión única: login → CC → Mi Trabajo → Auditor (gate C1)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.models import User
from app.orchestration_models import AIEmployee, EmployeeLimits, WorkPlan
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _employee_with_failures(db, org_id: str, user_id: str, code: str) -> str:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"NX01 {code}",
        specialty="DOCINT",
        lifecycle_status="ACTIVE",
        status="DISPONIBLE",
        is_active=True,
    )
    db.add(emp)
    db.flush()
    db.add(EmployeeLimits(employee_id=emp.id, daily_cost_limit=100.0))
    for i in range(6):
        db.add(
            WorkPlan(
                organization_id=org_id,
                user_id=user_id,
                employee_id=emp.id,
                correlation_id=f"corr-nx01-{code}-{i}",
                request="fail",
                objective="fail",
                status="FAILED",
                error="err",
            )
        )
    db.commit()
    return emp.id


def test_nx01_e2e_session_login_cc_trabajo_auditor(client: TestClient, token: str):
    """Login → CC (mi_trabajo) → bandeja → auditoría mínima sin duplicados."""
    headers = auth_header(token)

    login_check = client.get("/api/auth/me", headers=headers)
    assert login_check.status_code == 200

    cc = client.get("/api/centro-control/resumen-ejecutivo", headers=headers)
    assert cc.status_code == 200
    cc_body = cc.json()
    assert cc_body.get("mi_trabajo") is not None
    assert isinstance(cc_body["mi_trabajo"], dict)

    trabajo = client.get("/api/trabajo/items", headers=headers)
    assert trabajo.status_code == 200
    assert "items" in trabajo.json()

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).one()
        emp_id = _employee_with_failures(
            db, admin.organization_id, admin.id, f"nx01-{uuid.uuid4().hex[:4]}"
        )
    finally:
        db.close()

    audit = client.post(
        "/api/empleados-auditor/ejecutar",
        headers=headers,
        json={"employee_id": emp_id},
    )
    assert audit.status_code == 200

    items = client.get("/api/trabajo/items?modulo=auditor_empleados", headers=headers).json()["items"]
    auditor_rows = [i for i in items if i.get("metadata", {}).get("employee_id") == emp_id]
    assert len(auditor_rows) >= 1
    assert auditor_rows[0]["modulo"] == "auditor_empleados"
    assert len({i["id"] for i in auditor_rows}) == len(auditor_rows)
