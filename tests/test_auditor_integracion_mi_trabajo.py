"""Integración Auditor Empleados IA → Mi Trabajo."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Notification, Organization, Permission, Role, RolePermission, User
from app.notifications import emit_event
from app.orchestration_models import AIEmployee, EmployeeLimits, WorkPlan
from app.security import hash_password
from conftest import auth_header

pytestmark = pytest.mark.operations


def _create_employee(db: Session, org_id: str, code: str, lifecycle: str = "ACTIVE") -> AIEmployee:
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=f"Emp {code}",
        specialty="general",
        lifecycle_status=lifecycle,
        status="DISPONIBLE",
        is_active=True,
        certified_at=None if lifecycle == "ACTIVE" else __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    db.add(emp)
    db.flush()
    db.add(EmployeeLimits(employee_id=emp.id, daily_cost_limit=100.0))
    db.flush()
    return emp


def _run_audit(client: TestClient, headers: dict, employee_id: str) -> None:
    client.post("/api/empleados-auditor/ejecutar", headers=headers, json={"employee_id": employee_id})


def test_saludable_no_genera_trabajo(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        emp = _create_employee(db, admin.organization_id, f"trab-ok-{uuid.uuid4().hex[:4]}", "CERTIFIED")
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    res = client.get("/api/trabajo/items?modulo=auditor_empleados", headers=auth_headers)
    rows = [i for i in res.json()["items"] if i.get("metadata", {}).get("employee_id") == emp_id]
    assert rows == []


def test_critico_aparece_en_trabajo(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        org_id = admin.organization_id
        emp = _create_employee(db, org_id, f"trab-crit-{uuid.uuid4().hex[:4]}")
        for i in range(6):
            db.add(
                WorkPlan(
                    organization_id=org_id,
                    user_id=admin.id,
                    employee_id=emp.id,
                    correlation_id=f"corr-trab-{i}",
                    request="t",
                    objective="fail",
                    status="FAILED",
                    error="err",
                )
            )
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    res = client.get("/api/trabajo/items?modulo=auditor_empleados", headers=auth_headers)
    rows = [i for i in res.json()["items"] if i.get("metadata", {}).get("employee_id") == emp_id]
    assert len(rows) >= 1
    row = rows[0]
    assert row["tipo"] in ("auditor_empleado_critico", "auditor_empleado_intervencion", "auditor_empleado_revision")
    assert row["modulo"] == "auditor_empleados"
    assert row["correlation_id"]
    assert row["requires_action"]
    assert row["semantic_kind"] in ("HECHO", "INFERENCIA", "RECOMENDACION", None)
    assert "api_key" not in (row.get("detalle") or "").lower()
    assert any(a.get("href", "").startswith("/empleados/auditoria") for a in row["acciones"])


def test_intervencion_sin_certificacion(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        emp = _create_employee(db, admin.organization_id, f"trab-int-{uuid.uuid4().hex[:4]}")
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    res = client.get("/api/trabajo/items", headers=auth_headers)
    rows = [
        i
        for i in res.json()["items"]
        if i.get("metadata", {}).get("employee_id") == emp_id and i["modulo"] == "auditor_empleados"
    ]
    assert len(rows) >= 1
    assert rows[0]["tipo"] in ("auditor_empleado_intervencion", "auditor_empleado_critico")


def test_deduplicacion_auditor_vs_notificacion_820(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        org_id = admin.organization_id
        emp = _create_employee(db, org_id, f"trab-ded-{uuid.uuid4().hex[:4]}")
        for i in range(6):
            db.add(
                WorkPlan(
                    organization_id=org_id,
                    user_id=admin.id,
                    employee_id=emp.id,
                    correlation_id=f"corr-ded-{i}",
                    request="t",
                    objective="fail",
                    status="FAILED",
                )
            )
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    items = client.get("/api/trabajo/items", headers=auth_headers).json()["items"]
    auditor_rows = [i for i in items if i.get("metadata", {}).get("employee_id") == emp_id and i["modulo"] == "auditor_empleados"]
    notif_rows = [
        i
        for i in items
        if i["tipo"] == "notificacion"
        and i.get("metadata", {}).get("employee_id") == emp_id
    ]
    assert len(auditor_rows) >= 1
    assert len(notif_rows) == 0


def test_trabajo_resumen_incluye_auditor(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        emp = _create_employee(db, admin.organization_id, f"trab-sum-{uuid.uuid4().hex[:4]}")
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    resumen = client.get("/api/trabajo/resumen", headers=auth_headers).json()
    assert resumen["pendientes"] >= 1
    assert resumen["total_visible"] >= 1


def test_filtro_modulo_auditor(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        emp = _create_employee(db, admin.organization_id, f"trab-fil-{uuid.uuid4().hex[:4]}")
        db.commit()
        emp_id = emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    res = client.get("/api/trabajo/items?modulo=auditor_empleados&tipo=auditor_empleado_intervencion", headers=auth_headers)
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["modulo"] == "auditor_empleados"


def test_trabajo_multiempresa_auditor(client: TestClient):
    from app.database import SessionLocal
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    db = SessionLocal()
    pwd = "AuditorTrabajo*1"
    try:
        org_a = Organization(name="Aud Trab A", slug=f"at-a-{uuid.uuid4().hex[:6]}")
        org_b = Organization(name="Aud Trab B", slug=f"at-b-{uuid.uuid4().hex[:6]}")
        db.add_all([org_a, org_b])
        db.flush()
        for org in (org_a, org_b):
            bootstrap_permissions(db)
            bootstrap_orchestration(db, org.id)
            bootstrap_salud(db, org.id)
        ua = User(
            organization_id=org_a.id,
            username=f"aud_trab_a_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        ub = User(
            organization_id=org_b.id,
            username=f"aud_trab_b_{uuid.uuid4().hex[:4]}",
            password_hash=hash_password(pwd),
            role="admin",
            status="ACTIVE",
            is_active=True,
        )
        db.add_all([ua, ub])
        db.flush()
        emp_b = _create_employee(db, org_b.id, "only-b-trab")
        db.commit()
        username_a, username_b, emp_b_id = ua.username, ub.username, emp_b.id
    finally:
        db.close()

    ta = client.post("/api/auth/login", json={"username": username_a, "password": pwd}).json()["access_token"]
    tb = client.post("/api/auth/login", json={"username": username_b, "password": pwd}).json()["access_token"]
    client.post("/api/empleados-auditor/ejecutar", headers=auth_header(tb), json={"employee_id": emp_b_id})
    items_a = client.get("/api/trabajo/items?modulo=auditor_empleados", headers=auth_header(ta)).json()["items"]
    assert all(i.get("metadata", {}).get("employee_id") != emp_b_id for i in items_a)


def test_rbac_view_sin_execute_auditor(client: TestClient, auth_headers):
    from app.database import SessionLocal
    from app.config import settings
    from app.models import Role, RolePermission, Permission

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        viewer = User(
            organization_id=admin.organization_id,
            username=f"trab_view_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("Viewer*123"),
            role="viewer",
            status="ACTIVE",
            is_active=True,
        )
        db.add(viewer)
        role = (
            db.query(Role)
            .filter(Role.code == "viewer", Role.organization_id.is_(None), Role.is_system.is_(True))
            .first()
        )
        perm_codes = ["auditor_empleados.view", "operations.view"]
        for code in perm_codes:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if role and perm:
                exists = (
                    db.query(RolePermission)
                    .filter(RolePermission.role_id == role.id, RolePermission.permission_id == perm.id)
                    .first()
                )
                if not exists:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        emp = _create_employee(db, admin.organization_id, f"trab-rbac-{uuid.uuid4().hex[:4]}")
        db.commit()
        username, emp_id = viewer.username, emp.id
    finally:
        db.close()

    _run_audit(client, auth_headers, emp_id)
    login = client.post("/api/auth/login", json={"username": username, "password": "Viewer*123"})
    headers = auth_header(login.json()["access_token"])
    assert client.get("/api/trabajo/items?modulo=auditor_empleados", headers=headers).status_code == 200
    assert client.post("/api/empleados-auditor/ejecutar", headers=headers, json={}).status_code == 403
