"""Contrato API consumido por vistas comerciales frontend — sin modificar backend."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _setup(client: TestClient) -> tuple[dict, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    db = TestingSessionLocal()
    org = Organization(name=f"Vistas {uuid.uuid4().hex[:6]}", slug=f"v-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "VistasUI*Test1"
    username = f"u-{uuid.uuid4().hex[:4]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    org_id = org.id
    db.close()
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return auth_header(login.json()["access_token"]), org_id


def test_api_planes_list_and_detail(client: TestClient):
    headers, _ = _setup(client)
    plan = client.post(
        "/api/comercial/planes",
        headers=headers,
        json={
            "code": f"ui-{uuid.uuid4().hex[:4]}",
            "name": "Plan UI",
            "consumo_ia_incluido_tokens": 500000,
            "credential_mode": "IA_ADMINISTRADA",
            "limits": {"empleados_ia": 3, "usuarios": 10},
        },
    )
    assert plan.status_code == 201
    plan_id = plan.json()["id"]
    listed = client.get("/api/comercial/planes", headers=headers)
    assert listed.status_code == 200
    detail = client.get(f"/api/comercial/planes/{plan_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["consumo_ia_incluido_tokens"] == 500000
    assert body["credential_mode"] == "IA_ADMINISTRADA"


def test_api_propuesta_trazabilidad_desglose_naturaleza(client: TestClient):
    headers, _ = _setup(client)
    prop = client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "UI propuesta"})
    assert prop.status_code == 201
    pid = prop.json()["id"]
    client.post(
        f"/api/comercial/propuestas/{pid}/valores",
        headers=headers,
        json={"categoria": "AHORRO", "naturaleza": "VERIFICADO", "valor_bruto": 80000, "atribucion_pct": 50, "criterio_atribucion": "x"},
    )
    client.post(
        f"/api/comercial/propuestas/{pid}/valores",
        headers=headers,
        json={"categoria": "NUEVO_INGRESO", "naturaleza": "POTENCIAL", "valor_bruto": 200000, "atribucion_pct": 40, "criterio_atribucion": "y"},
    )
    client.post(f"/api/comercial/propuestas/{pid}/precio-sugerido", headers=headers, json={})
    detail = client.get(f"/api/comercial/propuestas/{pid}", headers=headers).json()
    trace = client.get(f"/api/comercial/propuestas/{pid}/trazabilidad", headers=headers).json()
    assert "desglose_naturaleza" in trace
    assert trace["desglose_naturaleza"]["valor_potencial_atribuible"] == 80000.0
    assert detail["valor_atribuible_total"] == 40000.0
    assert "contrato_centro_control" in trace


def test_api_tco_tablero(client: TestClient):
    headers, _ = _setup(client)
    tab = client.get("/api/tco/tablero", headers=headers)
    assert tab.status_code == 200


def test_api_implementacion_proyectos(client: TestClient):
    headers, _ = _setup(client)
    prop = client.post("/api/comercial/propuestas", headers=headers, json={"titulo": "Para impl"})
    pid = prop.json()["id"]
    proj = client.post("/api/implementacion/proyectos", headers=headers, json={"titulo": "Impl UI", "proposal_id": pid})
    assert proj.status_code == 201
    listed = client.get("/api/implementacion/proyectos", headers=headers)
    assert listed.status_code == 200
    tab = client.get(f"/api/implementacion/proyectos/{proj.json()['id']}/tablero", headers=headers)
    assert tab.status_code == 200


def test_api_finops_dashboard(client: TestClient):
    headers, _ = _setup(client)
    dash = client.get("/api/finops/dashboard", headers=headers)
    assert dash.status_code == 200


def test_multiempresa_planes_aislamiento(client: TestClient):
    h1, _ = _setup(client)
    h2, _ = _setup(client)
    prop = client.post("/api/comercial/propuestas", headers=h1, json={"titulo": "A"})
    pid = prop.json()["id"]
    assert client.get(f"/api/comercial/propuestas/{pid}", headers=h2).status_code == 404
