"""MB-12 EIAAX — Mesa de Ayuda: casos runtime y regresión."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.services import support_service as svc
from app.support_models import SupportCase

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

    org = Organization(name=f"Org-mb12-{uuid.uuid4().hex[:6]}")
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


def test_runtime_caso1_solicitud_normal(client: TestClient, sdb):
    """CASO 1: solicitud → clasificación → asignación → comunicación → resolución → validación → cierre."""
    _, admin, agent = _tenant(sdb)
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={
            "tipo": "SOLICITUD",
            "asunto": "Acceso al panel ejecutivo",
            "descripcion": "Necesito permiso de lectura",
            "impacto": "MEDIO",
            "urgencia": "MEDIA",
        },
    )
    assert created.status_code == 201
    case_id = created.json()["id"]
    assert created.json()["prioridad_sugerida"] == "MEDIA"

    cls = client.post(
        f"/api/soporte/casos/{case_id}/clasificar",
        headers=headers,
        json={"categoria": "ACCESO", "servicio_componente": "Centro Control"},
    )
    assert cls.status_code == 200
    assert cls.json()["estado"] == "CLASIFICADO"

    assign = client.post(
        f"/api/soporte/casos/{case_id}/asignar",
        headers=headers,
        json={"responsable_id": agent.id},
    )
    assert assign.status_code == 200
    assert assign.json()["estado"] == "ASIGNADO"

    com = client.post(
        f"/api/soporte/casos/{case_id}/comentarios",
        headers=headers,
        json={"cuerpo": "Solicitamos captura del error"},
    )
    assert com.status_code == 200

    resolved = client.post(
        f"/api/soporte/casos/{case_id}/resolver",
        headers=headers,
        json={"resolucion": "Se otorgó permiso de lectura al solicitante."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["estado"] == "RESUELTO"
    assert resolved.json()["validacion_solicitante"] == "PENDIENTE"

    validated = client.post(
        f"/api/soporte/casos/{case_id}/validar",
        headers=headers,
        json={"aceptada": True},
    )
    assert validated.status_code == 200
    assert validated.json()["estado"] == "CERRADO"


def test_runtime_caso2_sla(client: TestClient, sdb):
    """CASO 2: incidente prioritario con SLA, alerta y medición."""
    org, admin, _ = _tenant(sdb)
    svc.create_sla_policy(
        sdb,
        org.id,
        {"nombre": "Alta incidente", "prioridad": "ALTA", "minutos_resolucion": 30},
    )
    headers = _login(client, admin.username)
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={
            "tipo": "INCIDENTE",
            "asunto": "API no responde",
            "descripcion": "Timeout en integración",
            "impacto": "ALTO",
            "urgencia": "ALTA",
            "prioridad": "ALTA",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["resolucion_limite"] is not None
    assert body["sla_estado"] in ("DENTRO", "PROXIMO", "VENCIDO")

    case = svc.get_case(sdb, org.id, body["id"])
    case.resolucion_limite = datetime.now(timezone.utc) - timedelta(minutes=5)
    case.sla_warning_emitido = False
    sdb.commit()

    alertas = svc.check_sla_warnings(sdb, org.id)
    assert len(alertas) >= 1

    resolved = client.post(
        f"/api/soporte/casos/{body['id']}/resolver",
        headers=headers,
        json={"resolucion": "Se reinició el conector.", "cerrar": True},
    )
    assert resolved.status_code == 200
    assert resolved.json()["estado"] == "CERRADO"


def test_runtime_caso3_problema_recurrente(client: TestClient, sdb):
    """CASO 3: incidentes relacionados → problema → causa → solución → KB propuesta."""
    org, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    ids = []
    for i in range(2):
        res = client.post(
            "/api/soporte/casos",
            headers=headers,
            json={
                "tipo": "INCIDENTE",
                "asunto": f"Error login SSO #{i}",
                "descripcion": "Fallo intermitente IdP",
                "categoria": "SSO",
            },
        )
        ids.append(res.json()["id"])

    prob = client.post(
        "/api/soporte/problemas",
        headers=headers,
        json={
            "titulo": "SSO intermitente",
            "descripcion": "Varios incidentes de autenticación",
            "case_ids": ids,
        },
    )
    assert prob.status_code == 201
    problem_id = prob.json()["id"]

    upd = client.patch(
        f"/api/soporte/problemas/{problem_id}",
        headers=headers,
        json={
            "causa_raiz": "Certificado IdP expirado",
            "solucion_definitiva": "Renovación de certificado",
            "acciones_preventivas": "Monitoreo de vencimiento",
            "estado": "MITIGADO",
        },
    )
    assert upd.status_code == 200

    kb = client.post(
        "/api/soporte/conocimiento/proponer",
        headers=headers,
        json={
            "titulo": "Renovar certificado SSO",
            "contenido": "Procedimiento de renovación",
            "problem_id": problem_id,
        },
    )
    assert kb.status_code == 201
    assert kb.json()["estado"] == "PENDIENTE"


def test_runtime_caso4_fallo_externo(client: TestClient, sdb):
    """CASO 4: capacidad externa no disponible → incidente controlado."""
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    corr = str(uuid.uuid4())
    created = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={
            "tipo": "INTEGRACION",
            "asunto": "Proveedor PIIAX no disponible",
            "descripcion": "Timeout en capacidad externa",
            "servicio_componente": "PIIAX-connector",
            "correlation_id": corr,
            "impacto": "ALTO",
            "urgencia": "ALTA",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["correlation_id"] == corr
    assert body["estado"] == "NUEVO"
    assert body["tipo"] == "INTEGRACION"
    assert body["estado"] != "CERRADO"


def test_runtime_caso5_multiempresa(client: TestClient, sdb):
    """CASO 5: tenant A no accede caso/evidencia de tenant B."""
    org_a, admin_a, _ = _tenant(sdb)
    _, admin_b, _ = _tenant(sdb)
    headers_a = _login(client, admin_a.username)
    headers_b = _login(client, admin_b.username)

    case_a = client.post(
        "/api/soporte/casos",
        headers=headers_a,
        json={"tipo": "SOLICITUD", "asunto": "Solo org A", "descripcion": "Privado"},
    ).json()

    denied = client.get(f"/api/soporte/casos/{case_a['id']}", headers=headers_b)
    assert denied.status_code in (403, 404)

    ev = client.post(
        f"/api/soporte/casos/{case_a['id']}/evidencias",
        headers=headers_a,
        json={"tipo": "LOG", "referencia": "log://a/secret"},
    )
    assert ev.status_code == 200

    ev_denied = client.get(f"/api/soporte/casos/{case_a['id']}", headers=headers_b)
    assert ev_denied.status_code in (403, 404)


def test_prioridad_sugerida_no_todo_urgente():
    assert svc.suggest_priority_for_case("BAJO", "BAJA")["prioridad_sugerida"] == "BAJA"
    assert svc.suggest_priority_for_case("CRITICO", "CRITICA")["prioridad_sugerida"] == "CRITICA"


def test_escalamiento_registrado(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "INCIDENTE", "asunto": "Escalar", "descripcion": "Test"},
    ).json()
    esc = client.post(
        f"/api/soporte/casos/{case['id']}/escalar",
        headers=headers,
        json={"motivo": "VENCIMIENTO", "nota": "SLA próximo"},
    )
    assert esc.status_code == 200
    assert esc.json()["escalamiento_nivel"] >= 1


def test_diagnostico_separado(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    case = client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "INCIDENTE", "asunto": "Diag", "descripcion": "Test"},
    ).json()
    diag = client.patch(
        f"/api/soporte/casos/{case['id']}/diagnostico",
        headers=headers,
        json={
            "sintoma": "Error 500",
            "hipotesis": "Memoria insuficiente",
            "causa_validada": "Heap OOM confirmado",
        },
    )
    assert diag.status_code == 200
    assert diag.json()["hipotesis"] != diag.json()["causa_validada"]


def test_autoservicio_endpoint(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    res = client.post(
        "/api/soporte/autoservicio",
        headers=headers,
        json={"consulta": "no puedo iniciar sesión"},
    )
    assert res.status_code == 200
    assert "prioridad_sugerida" in res.json()


def test_indicadores_endpoint(client: TestClient, sdb):
    _, admin, _ = _tenant(sdb)
    headers = _login(client, admin.username)
    client.post(
        "/api/soporte/casos",
        headers=headers,
        json={"tipo": "CONSULTA", "asunto": "Indicador", "descripcion": "Test"},
    )
    ind = client.get("/api/soporte/indicadores", headers=headers)
    assert ind.status_code == 200
    assert "casos_abiertos" in ind.json()


def test_list_sla_policies(client: TestClient, sdb):
    org, admin, _ = _tenant(sdb)
    svc.create_sla_policy(sdb, org.id, {"nombre": "Media", "prioridad": "MEDIA", "minutos_resolucion": 480})
    headers = _login(client, admin.username)
    res = client.get("/api/soporte/sla", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1
