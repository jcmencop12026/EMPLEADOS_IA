"""MB-08 — Centro de Control operacional: runtime y multitenant."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User
from app.orchestration_models import AIEmployee, WorkPlan
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.auth, pytest.mark.tenant]


def test_operacional_endpoint_estructura(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/operacional?periodo=mtd", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    for key in (
        "resumen_operacional",
        "fuerza_laboral",
        "ejecuciones",
        "capacidad",
        "costo",
        "requiere_atencion",
        "aprobaciones",
        "capacidades_externas",
        "proveedores",
        "resultados_frontera",
        "ultima_actualizacion",
    ):
        assert key in body
    assert body["modo_actualizacion"] == "bajo_demanda"


def test_resumen_ejecutivo_incluye_operacional(client: TestClient, auth_headers):
    res = client.get("/api/centro-control/resumen-ejecutivo", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "operacional" in body
    assert any(s["id"] == "empleados_ia" for s in body["secciones"])
    assert "conocimiento" in body or body.get("integraciones_futuras", {}).get("CONOCIMIENTO_930", "").startswith("Integrado")


def test_caso1_operacion_normal_empleado_y_ejecucion(client: TestClient, auth_headers):
    created = client.post(
        "/api/agent-factory/employees",
        headers=auth_headers,
        json={"name": "CC Operativo", "specialty": "DOCINT"},
    )
    assert created.status_code == 200
    emp_id = created.json()["id"]

    op = client.get("/api/centro-control/operacional", headers=auth_headers).json()
    ids = [e["id"] for e in op["fuerza_laboral"]["items"]]
    assert emp_id in ids


def test_caso2_error_en_atencion(client: TestClient, auth_headers):
    from app.config import settings

    db = TestingSessionLocal()
    try:
        admin = db.query(User).filter(User.username == settings.bootstrap_admin_username).first()
        plan = WorkPlan(
            organization_id=admin.organization_id,
            user_id=admin.id,
            correlation_id=str(uuid.uuid4()),
            status="FAILED",
            objective="Prueba fallida CC",
            request="test",
            error="Error controlado de prueba",
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
    finally:
        db.close()

    op = client.get("/api/centro-control/operacional", headers=auth_headers).json()
    tipos = [a["tipo"] for a in op["requiere_atencion"]]
    assert "ejecucion_fallida" in tipos

    detail = client.get(f"/api/centro-control/ejecuciones/{plan_id}/detalle-operacional", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body.get("fallo") or body.get("estado_codigo") == "FAILED"


def test_caso4_aprobacion_pendiente_en_centro(client: TestClient, auth_headers):
    op = client.get("/api/centro-control/operacional", headers=auth_headers).json()
    assert "aprobaciones" in op
    assert "total_pendientes" in op["aprobaciones"]


def test_caso6_multitenant_operacional(client: TestClient, auth_headers):
    db = TestingSessionLocal()
    try:
        org_b = Organization(name=f"CC-MB08-{uuid.uuid4().hex[:6]}")
        db.add(org_b)
        db.flush()
        user_b = User(
            organization_id=org_b.id,
            username=f"ccmb08_{uuid.uuid4().hex[:6]}",
            password_hash=hash_password("testpass123"),
            role="admin",
            is_active=True,
        )
        db.add(user_b)
        emp_b = AIEmployee(organization_id=org_b.id, code=f"emp-{uuid.uuid4().hex[:4]}", name="Empleado B", specialty="DOCINT")
        db.add(emp_b)
        db.commit()
        emp_b_id = emp_b.id
        login_b = client.post("/api/auth/login", json={"username": user_b.username, "password": "testpass123"})
        token_b = login_b.json()["access_token"]
    finally:
        db.close()

    op_a = client.get("/api/centro-control/operacional", headers=auth_headers).json()
    ids_a = [e["id"] for e in op_a["fuerza_laboral"]["items"]]
    assert emp_b_id not in ids_a

    op_b = client.get("/api/centro-control/operacional", headers=auth_header(token_b)).json()
    ids_b = [e["id"] for e in op_b["fuerza_laboral"]["items"]]
    assert emp_b_id in ids_b

    denied = client.get(
        f"/api/centro-control/ejecuciones/{uuid.uuid4()}/detalle-operacional",
        headers=auth_header(token_b),
    )
    assert denied.status_code in (404, 400)
