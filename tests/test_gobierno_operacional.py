"""Tests gobierno operacional EIAAX — acciones, aprobaciones, visibilidad, IA y multitenant."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header


def _create_tenant_user(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "Gobierno*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"gob-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    uname = f"gob-user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=uname,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def gob_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_evaluar_accion_tipos(client: TestClient, token: str):
    headers = auth_header(token)
    for tipo, requiere in [("LECTURA", False), ("PROPUESTA", True), ("EJECUCION", True)]:
        res = client.post(
            "/api/gobierno-operacional/acciones/evaluar",
            headers=headers,
            json={"tipo_accion": tipo, "recurso_tipo": "hallazgo"},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["tipo_accion"] == tipo
        assert body["requiere_aprobacion_humana"] is requiere


def test_flujo_aprobacion_completo(client: TestClient, token: str):
    headers = auth_header(token)
    created = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "EJECUCION",
            "recurso_tipo": "integracion",
            "recurso_id": str(uuid.uuid4()),
            "descripcion": "Ejecutar conector externo",
            "motivo_solicitud": "Prueba gobierno operacional",
            "criticidad": "HIGH",
        },
    )
    assert created.status_code == 201, created.text
    sol = created.json()
    assert sol["estado"] == "PENDIENTE"
    assert sol["correlation_id"]

    decided = client.post(
        f"/api/gobierno-operacional/solicitudes/{sol['id']}/decidir",
        headers=headers,
        json={"decision": "approve", "motivo": "Autorizado en prueba"},
    )
    assert decided.status_code == 200, decided.text
    final = decided.json()
    assert final["estado"] == "EJECUTADA"
    assert final["aprobado_por"] is not None
    assert final["executed_at"] is not None


def test_lectura_auto_ejecuta_sin_aprobacion(client: TestClient, token: str):
    headers = auth_header(token)
    res = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "LECTURA",
            "recurso_tipo": "informe",
            "descripcion": "Consulta de informe",
        },
    )
    assert res.status_code == 201
    assert res.json()["estado"] == "APROBADA"


def test_visibilidad_generalizada(client: TestClient, token: str):
    headers = auth_header(token)
    obj_id = str(uuid.uuid4())
    res = client.post(
        "/api/gobierno-operacional/visibilidad",
        headers=headers,
        json={
            "dominio": "hallazgo",
            "contexto_id": str(uuid.uuid4()),
            "objeto_tipo": "hallazgo",
            "objeto_id": obj_id,
            "visible": True,
        },
    )
    assert res.status_code == 201, res.text
    listed = client.get("/api/gobierno-operacional/visibilidad?dominio=hallazgo", headers=headers)
    assert listed.status_code == 200
    assert any(r["objeto_id"] == obj_id for r in listed.json())


def test_ia_policy_verificar(client: TestClient, token: str):
    headers = auth_header(token)
    policies = client.get("/api/gobierno-operacional/ia/politicas", headers=headers)
    assert policies.status_code == 200
    assert len(policies.json()) >= 1

    check = client.post(
        "/api/gobierno-operacional/ia/verificar",
        headers=headers,
        json={"tipo_accion": "EJECUCION", "proveedor": "openai", "modelo": "gpt-4"},
    )
    assert check.status_code == 200
    body = check.json()
    assert "permitido" in body
    assert "requiere_aprobacion" in body


def test_centro_confianza_solo_evidencia_real(client: TestClient, token: str):
    headers = auth_header(token)
    client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "PROPUESTA",
            "recurso_tipo": "plan",
            "descripcion": "Propuesta de mejora",
        },
    )
    centro = client.get("/api/gobierno-operacional/confianza", headers=headers)
    assert centro.status_code == 200, centro.text
    body = centro.json()
    assert body["resumen"]["solo_evidencia_real"] is True
    ids = {c["id"] for c in body["controles"]}
    assert "aislamiento" in ids
    assert "rbac" in ids
    assert "acciones_controladas" in ids
    for ctrl in body["controles"]:
        assert ctrl["evidencia"]


def test_cross_tenant_solicitud_denied(client: TestClient, gob_db: Session):
    org_a, user_a, pass_a = _create_tenant_user(gob_db, org_name="Gobierno Org A")
    org_b, user_b, pass_b = _create_tenant_user(gob_db, org_name="Gobierno Org B")
    token_a = _token(client, user_a.username, pass_a)
    token_b = _token(client, user_b.username, pass_b)

    created = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=auth_header(token_a),
        json={
            "tipo_accion": "EJECUCION",
            "recurso_tipo": "herramienta",
            "descripcion": "Solicitud org A",
        },
    )
    assert created.status_code == 201
    sol_id = created.json()["id"]

    cross_decide = client.post(
        f"/api/gobierno-operacional/solicitudes/{sol_id}/decidir",
        headers=auth_header(token_b),
        json={"decision": "approve"},
    )
    assert cross_decide.status_code == 404

    cross_list = client.get(
        f"/api/gobierno-operacional/solicitudes",
        headers=auth_header(token_b),
    )
    assert cross_list.status_code == 200
    assert all(s["id"] != sol_id for s in cross_list.json())


def test_permiso_insuficiente_denegado(client: TestClient, gob_db: Session):
    org, user, password = _create_tenant_user(gob_db, org_name="Gobierno Viewer", role="viewer")
    token = _token(client, user.username, password)
    headers = auth_header(token)

    centro = client.get("/api/gobierno-operacional/confianza", headers=headers)
    assert centro.status_code == 200

    crear = client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "EJECUCION",
            "recurso_tipo": "test",
            "descripcion": "Debe fallar",
        },
    )
    assert crear.status_code == 403


def test_eventos_trazabilidad(client: TestClient, token: str):
    headers = auth_header(token)
    client.post(
        "/api/gobierno-operacional/solicitudes",
        headers=headers,
        json={
            "tipo_accion": "ANALISIS",
            "recurso_tipo": "indicador",
            "descripcion": "Análisis de indicador",
        },
    )
    eventos = client.get("/api/gobierno-operacional/eventos", headers=headers)
    assert eventos.status_code == 200
    assert len(eventos.json()) >= 1
    evt = eventos.json()[0]
    assert evt["actor_tipo"]
    assert evt["accion"]
    assert evt.get("correlation_id")


def test_tipo_accion_invalido_rechazado(client: TestClient, token: str):
    headers = auth_header(token)
    res = client.post(
        "/api/gobierno-operacional/acciones/evaluar",
        headers=headers,
        json={"tipo_accion": "DESTRUIR"},
    )
    assert res.status_code == 422
