"""Ciclo Auditor → Mi Trabajo → Fábrica — integración controlada."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.employee_audit_models import EmployeeAuditFinding, EmployeeImprovementTrace
from app.models import Organization, User
from app.orchestration_models import AIEmployee, EmployeeLimits, WorkPlan
from app.security import hash_password
from app.config import settings
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant, pytest.mark.operations]


def _admin_user(db):
    return db.query(User).filter(User.username == settings.bootstrap_admin_username).first()


def _employee_with_failures(db, org_id: str, user_id: str, code: str) -> str:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"AudFab {code}",
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
                correlation_id=f"corr-af-{code}-{i}",
                request="fail",
                objective="fail",
                status="FAILED",
                error="err",
            )
        )
    db.commit()
    return emp.id


def _run_audit(client, token, emp_id: str):
    return client.post(
        "/api/empleados-auditor/ejecutar",
        headers=auth_header(token),
        json={"employee_id": emp_id},
    )


def _open_finding(db, org_id: str, emp_id: str) -> EmployeeAuditFinding:
    finding = (
        db.query(EmployeeAuditFinding)
        .filter(
            EmployeeAuditFinding.organization_id == org_id,
            EmployeeAuditFinding.employee_id == emp_id,
            EmployeeAuditFinding.status == "ABIERTO",
        )
        .first()
    )
    assert finding is not None
    return finding


def test_auditor_recommends_without_executing(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"rec-{uuid.uuid4().hex[:4]}")
        before_version = db.query(AIEmployee).filter(AIEmployee.id == emp_id).first().version
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        after_version = db.query(AIEmployee).filter(AIEmployee.id == emp_id).first().version
    finally:
        db.close()
    assert before_version == after_version


def test_trabajo_shows_revisar_fabrica(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"tr-{uuid.uuid4().hex[:4]}")
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    res = client.get("/api/trabajo/items?modulo=auditor_empleados", headers=auth_header(token))
    rows = [i for i in res.json()["items"] if i.get("metadata", {}).get("employee_id") == emp_id]
    assert rows
    assert any(a["codigo"] == "revisar_fabrica" for a in rows[0]["acciones"])


def test_iniciar_mejora_blocks_auto_execution(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"ini-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding = _open_finding(db, org_id, emp_id)
        finding_id = finding.id
    finally:
        db.close()

    start = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    )
    assert start.status_code == 200
    body = start.json()
    assert body["auto_execution_blocked"] is True
    assert body["trace_id"]
    assert "/empleados/" in body["href"]


def test_viewer_cannot_execute_factory_action(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"den-{uuid.uuid4().hex[:4]}")
        finding = None
        _run_audit(client, token, emp_id)
        finding = _open_finding(db, admin.organization_id, emp_id)
        finding_id = finding.id
        username = f"viewer-af-{uuid.uuid4().hex[:6]}"
        db.add(User(
            organization_id=admin.organization_id,
            username=username,
            password_hash=hash_password("ViewerAf*1"),
            role="viewer",
        ))
        db.commit()
    finally:
        db.close()

    viewer = client.post("/api/auth/login", json={"username": username, "password": "ViewerAf*1"}).json()["access_token"]
    trace = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    denied = client.post(
        f"/api/empleados-auditor/mejoras/{trace}/ejecutar",
        headers=auth_header(viewer),
        json={"operation": "capacitar", "payload": {"training_type": "INSTRUCTIONS", "reason": "x"}},
    )
    assert denied.status_code == 403


def test_authorized_train_and_traceability(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"ok-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding = _open_finding(db, org_id, emp_id)
        finding_id = finding.id
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    exec1 = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={
            "operation": "capacitar",
            "payload": {
                "authorize_deviation": True,
                "deviation_justification": "Capacitación autorizada explícitamente en prueba de trazabilidad",
                "training_type": "INSTRUCTIONS",
                "reason": "Capacitación test ciclo",
                "source": "test",
                "config_delta": {"instructions": {"operating_rules": "Regla ciclo auditor-fábrica"}},
            },
            "idempotency_key": "train-once",
        },
    )
    assert exec1.status_code == 200
    assert exec1.json()["factory_operation"] == "capacitar"

    exec2 = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={"operation": "capacitar", "idempotency_key": "train-once"},
    )
    assert exec2.status_code == 200
    assert exec2.json().get("idempotent") is True

    chain = client.get(f"/api/empleados-auditor/mejoras/{trace_id}/trazabilidad", headers=auth_header(token)).json()
    assert chain["employee_id"] == emp_id
    assert chain["finding_id"] == finding_id
    assert chain["correlation_id"]
    assert chain["factory_operation"] == "capacitar"
    dumped = str(chain)
    assert "api_key" not in dumped.lower()
    assert "secret" not in dumped.lower() or "auditor" in dumped.lower()


def test_idempotency_iniciar_mejora(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"idem-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    key = f"idem-key-{uuid.uuid4().hex[:8]}"
    r1 = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={"idempotency_key": key},
    ).json()
    r2 = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={"idempotency_key": key},
    ).json()
    assert r1["trace_id"] == r2["trace_id"]


def test_tenant_isolation_trace(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"iso-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
        other = Organization(name=f"OrgB {uuid.uuid4().hex[:6]}", slug=f"orgb-{uuid.uuid4().hex[:6]}")
        db.add(other)
        db.flush()
        other_user = f"other-{uuid.uuid4().hex[:6]}"
        db.add(User(organization_id=other.id, username=other_user, password_hash=hash_password("OtherOrg*1"), role="admin"))
        db.commit()
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    other_token = client.post("/api/auth/login", json={"username": other_user, "password": "OtherOrg*1"}).json()["access_token"]
    denied = client.get(f"/api/empleados-auditor/mejoras/{trace_id}/trazabilidad", headers=auth_header(other_token))
    assert denied.status_code == 404


def test_reauditoria_and_before_after(client: TestClient, token: str):
    db = TestingSessionLocal()
    try:
        admin = _admin_user(db)
        emp_id = _employee_with_failures(db, admin.organization_id, admin.id, f"rea-{uuid.uuid4().hex[:4]}")
        org_id = admin.organization_id
    finally:
        db.close()

    _run_audit(client, token, emp_id)
    db = TestingSessionLocal()
    try:
        finding_id = _open_finding(db, org_id, emp_id).id
    finally:
        db.close()

    trace_id = client.post(
        f"/api/empleados-auditor/hallazgos/{finding_id}/iniciar-mejora",
        headers=auth_header(token),
        json={},
    ).json()["trace_id"]

    client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/ejecutar",
        headers=auth_header(token),
        json={"operation": "probar", "idempotency_key": "probe"},
    )

    reaudit = client.post(
        f"/api/empleados-auditor/mejoras/{trace_id}/reauditar",
        headers=auth_header(token),
        json={"idempotency_key": "reaudit-1"},
    )
    assert reaudit.status_code == 200
    assert reaudit.json()["comparison"]["semantic_note"]


def test_contrato_fabrica_no_auto_execution(client: TestClient, token: str):
    res = client.get("/api/empleados-auditor/contrato-fabrica", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["auto_execution_blocked"] is True
    assert res.json()["factory"]["module"] == "employee_factory"
