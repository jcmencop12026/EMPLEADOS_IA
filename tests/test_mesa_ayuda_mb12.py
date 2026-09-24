"""MB-12 — Mesa de Ayuda y Soporte."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import support_service as svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def sdb():
    from app.database import SessionLocal

    db = SessionLocal()
    yield db
    db.close()


def _tenant(db: Session) -> tuple[Organization, User, User]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions

    org = Organization(name=f"Org-sup-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    admin = User(
        organization_id=org.id,
        username=f"adm-{uuid.uuid4().hex[:6]}",
        email=f"a-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="admin",
        is_active=True,
    )
    agent = User(
        organization_id=org.id,
        username=f"agt-{uuid.uuid4().hex[:6]}",
        email=f"g-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="operator",
        is_active=True,
    )
    db.add_all([admin, agent])
    db.commit()
    return org, admin, agent


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "Admin2026*"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_crear_caso_manual(client: TestClient, sdb):
    org, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    res = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={
            "tipo": "SOLICITUD",
            "asunto": "No puedo acceder al panel",
            "descripcion": "Error al iniciar sesión desde ayer",
            "prioridad": "ALTA",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["tipo"] == "SOLICITUD"
    assert body["estado"] == "NUEVO"
    assert body["organization_id"] == org.id


def test_asignar_y_cambiar_estado(client: TestClient, sdb):
    _, admin, agent = _tenant(sdb)
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "INCIDENTE", "asunto": "Servicio caído", "descripcion": "API no responde"},
    ).json()
    assign = client.post(
        f"/api/soporte/casos/{created['id']}/asignar",
        headers=headers,
        json={"responsable_id": agent.id},
    )
    assert assign.status_code == 200
    assert assign.json()["responsable_id"] == agent.id
    assert assign.json()["estado"] == "ASIGNADO"
    status = client.patch(
        f"/api/soporte/casos/{created['id']}/estado",
        headers=headers,
        json={"estado": "EN_PROCESO"},
    )
    assert status.status_code == 200
    assert status.json()["estado"] == "EN_PROCESO"


def test_resolver_y_cerrar(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "CONSULTA", "asunto": "Duda facturación", "descripcion": "Consulta sobre costos"},
    ).json()
    resolved = client.post(
        f"/api/soporte/casos/{created['id']}/resolver",
        headers=headers,
        json={"resolucion": "Se explicó el desglose de costos al cliente."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["estado"] == "RESUELTO"
    closed = client.post(f"/api/soporte/casos/{created['id']}/cerrar", headers=headers, json={})
    assert closed.status_code == 200
    assert closed.json()["estado"] == "CERRADO"


def test_sla_policy(sdb):
    org, admin, _ = _tenant(sdb)
    svc.create_sla_policy(
        sdb,
        org.id,
        {"nombre": "Alta", "prioridad": "ALTA", "minutos_resolucion": 120},
    )
    case = svc.create_case_manual(
        sdb,
        org.id,
        admin,
        {"tipo": "INCIDENTE", "asunto": "SLA test", "descripcion": "Prueba SLA", "prioridad": "ALTA"},
    )
    assert case["sla_estado"] in ("DENTRO", "PROXIMO", "VENCIDO", "NO_APLICA")
    assert case.get("resolucion_limite") is not None


def test_deduplicacion_origen_automatico(sdb):
    org, admin, _ = _tenant(sdb)
    payload = {
        "tipo": "INCIDENTE",
        "asunto": "Automatización fallida",
        "descripcion": "Fallo repetitivo en job X",
        "origen_tipo": "automation_failed",
        "origen_id": "job-123",
        "prioridad": "ALTA",
    }
    a = svc.create_case_auto(sdb, org.id, payload, actor_id=admin.id)
    b = svc.create_case_auto(sdb, org.id, payload, actor_id=admin.id)
    assert a["id"] == b["id"]
    assert b.get("deduplicado") is True


def test_comentarios_e_historial(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "SOLICITUD", "asunto": "Comentario", "descripcion": "Necesito ayuda"},
    ).json()
    com = client.post(
        f"/api/soporte/casos/{created['id']}/comentarios",
        headers=headers,
        json={"cuerpo": "Adjunto referencia del error"},
    )
    assert com.status_code == 200
    detail = client.get(f"/api/soporte/casos/{created['id']}", headers=headers).json()
    assert len(detail["comentarios"]) >= 1
    assert len(detail["historial"]) >= 2


def test_correlation_id_preservado(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    corr = str(uuid.uuid4())
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={
            "tipo": "INTEGRACION",
            "asunto": "Integración degradada",
            "descripcion": "Conector externo con errores",
            "correlation_id": corr,
        },
    ).json()
    assert created["correlation_id"] == corr


def test_multiempresa_aislamiento(client: TestClient, sdb):
    org_a, admin_a, _ = _tenant(sdb)
    _, admin_b, _ = _tenant(sdb)
    headers_a = _login(client, admin_a.username)
    headers_b = _login(client, admin_b.username)
    case_a = client.post(
        "/api/soporte/casos",
        headers=headers_a,
        json={"tipo": "SOLICITUD", "asunto": "Org A", "descripcion": "Solo A"},
    ).json()
    res = client.get(f"/api/soporte/casos/{case_a['id']}", headers=headers_b)
    assert res.status_code in (403, 404)
    list_b = client.get("/api/soporte/casos", headers=headers_b).json()
    assert all(c["organization_id"] != org_a.id for c in list_b)


def test_secretos_sanitizados():
    text = "Mi password: secreto123 y api_key=abc"
    clean = svc.sanitize_text(text)
    assert "secreto123" not in clean
    assert "[dato sensible omitido]" in clean


def test_contratos_portables(sdb):
    org, admin, agent = _tenant(sdb)
    case = svc.create_case_manual(
        sdb,
        org.id,
        admin,
        {"tipo": "SOLICITUD", "asunto": "Contrato", "descripcion": "Test"},
    )
    row = svc.get_case(sdb, org.id, case["id"])
    svc.assign_case(sdb, org.id, row.id, admin, responsable_id=agent.id)
    mt = svc.contrato_mi_trabajo(sdb, org.id, agent.id)
    cc = svc.contrato_centro_control(sdb, org.id)
    assert mt["casos_asignados"] >= 1
    assert "casos_abiertos" in cc


def test_tipos_endpoint(client: TestClient, auth_headers):
    res = client.get("/api/soporte/tipos", headers=auth_headers)
    assert res.status_code == 200
    assert "INCIDENTE" in res.json()["tipos"]


def test_rbac_viewer_sin_asignar(client: TestClient, sdb):
    org, admin, agent = _tenant(sdb)
    viewer = User(
        organization_id=org.id,
        username=f"view-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Admin2026*"),
        role="viewer",
        is_active=True,
    )
    sdb.add(viewer)
    sdb.commit()
    admin_headers = _login(client, admin.username)
    viewer_headers = _login(client, viewer.username)
    created = client.post(
        "/api/soporte/casos",
        headers=viewer_headers,
        json={"tipo": "CONSULTA", "asunto": "Mi caso", "descripcion": "Solo mío"},
    ).json()
    assert created["solicitante_id"] == viewer.id
    denied = client.post(
        f"/api/soporte/casos/{created['id']}/asignar",
        headers=viewer_headers,
        json={"responsable_id": agent.id},
    )
    assert denied.status_code == 403
    own = client.get("/api/soporte/casos", headers=viewer_headers).json()
    assert any(c["id"] == created["id"] for c in own)
    other = client.get(f"/api/soporte/casos/{created['id']}", headers=admin_headers).json()
    assert other["id"] == created["id"]


def test_superadmin_gestiona_casos(client: TestClient, auth_headers):
    created = client.post(
        "/api/soporte/casos",
        headers=auth_headers,
        json={"tipo": "SEGURIDAD", "asunto": "Alerta plataforma", "descripcion": "Revisión global"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["estado"] == "NUEVO"
    cc = client.get("/api/soporte/contrato/centro-control", headers=auth_headers)
    assert cc.status_code == 200
    assert "casos_abiertos" in cc.json()


def test_cierre_idempotente(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "SOLICITUD", "asunto": "Idempotencia", "descripcion": "Cierre doble"},
    ).json()
    first = client.post(f"/api/soporte/casos/{created['id']}/cerrar", headers=headers, json={})
    assert first.status_code == 200
    assert first.json()["estado"] == "CERRADO"
    second = client.post(f"/api/soporte/casos/{created['id']}/cerrar", headers=headers, json={})
    assert second.status_code == 200
    assert second.json()["estado"] == "CERRADO"
