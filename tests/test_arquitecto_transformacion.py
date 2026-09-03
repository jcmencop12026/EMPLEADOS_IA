"""Arquitecto de Transformación — pruebas integración, multitenant y RBAC."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from app.transformacion_models import DossierEmpresarial

pytestmark = [pytest.mark.transformacion]


@pytest.fixture
def tx_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _create_org_user(db: Session, name: str) -> tuple[Organization, User]:
    org = Organization(id=str(uuid.uuid4()), name=name, slug=f"tx-{uuid.uuid4().hex[:8]}")
    db.add(org)
    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        username=f"tx_{uuid.uuid4().hex[:6]}",
        email=f"tx_{uuid.uuid4().hex[:6]}@test.local",
        password_hash=hash_password("testpass123"),
        is_active=True,
        role="operator",
    )
    db.add(user)
    db.flush()
    return org, user


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_transformacion_registrar_necesidad_y_dossier(client: TestClient, auth_headers, tx_db):
    res = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={
            "titulo": "Transformación cobranza",
            "necesidad": "Alta mora en cartera B2B",
            "objetivo": "Reducir DSO en 20%",
            "area_proceso": "Finanzas",
            "nivel": "PRELIMINAR",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["paso"] == "necesidad_registrada"
    assert body["expediente"]["codigo"].startswith("EVA-")
    assert len(body["expediente"]["informacion"]) >= 3

    dossier = client.get("/api/transformacion/dossier", headers=auth_headers)
    assert dossier.status_code == 200
    assert dossier.json()["etapa_actual"] == "EVALUACION"


def test_transformacion_suficiencia_con_informacion_incompleta(client: TestClient, auth_headers, tx_db):
    reg = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={
            "titulo": "Caso incompleto",
            "necesidad": "Proceso manual lento",
            "nivel": "DIAGNOSTICA",
        },
    ).json()
    eid = reg["expediente"]["id"]
    suf = client.get(f"/api/transformacion/expedientes/{eid}/suficiencia", headers=auth_headers)
    assert suf.status_code == 200
    body = suf.json()
    assert body["puede_continuar"] is True
    assert body["confianza_global"] in ("ALTA", "MEDIA", "BAJA")
    assert "explicacion" in body


def test_transformacion_diagnostico_completo(client: TestClient, auth_headers, tx_db):
    reg = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={
            "titulo": "Diagnóstico integral",
            "necesidad": "Reprocesos en atención al cliente",
            "objetivo": "Mejorar NPS",
            "area_proceso": "Servicio",
            "nivel": "PRELIMINAR",
        },
    ).json()
    eid = reg["expediente"]["id"]
    diag = client.post(f"/api/transformacion/expedientes/{eid}/diagnosticar", headers=auth_headers)
    assert diag.status_code == 200, diag.text
    body = diag.json()
    assert body["paso"] == "diagnostico_completado"
    assert len(body["causas"]) >= 1
    assert len(body["alternativas"]) >= 3
    assert len(body["iniciativas"]) >= 3
    assert len(body["escenarios"]) >= 3
    tipos = {e["tipo"] for e in body["escenarios"]}
    assert "ACTUAL" in tipos
    assert body["siguiente_accion"]["accion"] in ("completar_informacion", "iniciar_transformacion", "revisar_diagnostico")
    recomendadas = [a for a in body["alternativas"] if a["recomendada"]]
    assert len(recomendadas) == 1


def test_transformacion_causas_sintoma_vs_probable(client: TestClient, auth_headers, tx_db):
    reg = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={"titulo": "Causas", "necesidad": "Errores frecuentes en facturación", "nivel": "PRELIMINAR"},
    ).json()
    diag = client.post(
        f"/api/transformacion/expedientes/{reg['expediente']['id']}/diagnosticar",
        headers=auth_headers,
    ).json()
    tipos = {c["tipo"] for c in diag["causas"]}
    assert "SINTOMA" in tipos


def test_transformacion_dossier_no_repregunta(client: TestClient, auth_headers, tx_db):
    reg1 = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={"titulo": "Primera", "necesidad": "Necesidad A", "nivel": "PRELIMINAR"},
    ).json()
    eid1 = reg1["expediente"]["id"]
    item = next(i for i in reg1["expediente"]["informacion"] if i["campo"] == "contexto_negocio")
    client.patch(
        f"/api/evaluaciones/{eid1}/informacion/{item['id']}",
        headers=auth_headers,
        json={"respuesta": "Empresa industrial 500 empleados"},
    )
    client.post(f"/api/transformacion/expedientes/{eid1}/diagnosticar", headers=auth_headers)

    reg2 = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={"titulo": "Segunda", "necesidad": "Necesidad B", "nivel": "PRELIMINAR"},
    ).json()
    ctx2 = next(i for i in reg2["expediente"]["informacion"] if i["campo"] == "contexto_negocio")
    assert ctx2["respuesta"] == "Empresa industrial 500 empleados"
    assert ctx2["estado"] == "RECIBIDO"


def test_transformacion_multitenant_aislamiento(client: TestClient, auth_headers, tx_db):
    reg_a = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={"titulo": "Org A", "necesidad": "Secreto A", "nivel": "PRELIMINAR"},
    ).json()

    org_b, user_b = _create_org_user(tx_db, "Org B Transform")
    tx_db.commit()
    headers_b = _login(client, user_b.username)

    dossier_b = client.get("/api/transformacion/dossier", headers=headers_b)
    assert dossier_b.status_code == 200
    assert dossier_b.json().get("resumen") is None or "Secreto A" not in str(dossier_b.json())

    reg_b = client.post(
        "/api/transformacion/necesidad",
        headers=headers_b,
        json={"titulo": "Org B", "necesidad": "Secreto B", "nivel": "PRELIMINAR"},
    ).json()
    assert reg_a["expediente"]["id"] != reg_b["expediente"]["id"]

    dossier_a = client.get("/api/transformacion/dossier", headers=auth_headers).json()
    assert all("Secreto B" not in str(c.get("valor", "")) for c in dossier_a.get("conocimiento", []))


def test_transformacion_rbac_sin_permiso(client: TestClient, tx_db):
    org, user = _create_org_user(tx_db, "Org RBAC TX")
    user.role = "viewer"
    tx_db.flush()
    tx_db.commit()
    headers = _login(client, user.username)
    res = client.post(
        "/api/transformacion/necesidad",
        headers=headers,
        json={"titulo": "X", "necesidad": "Y"},
    )
    assert res.status_code == 403


def test_transformacion_recorrido_e2e(client: TestClient, auth_headers, tx_db):
    """Recorrido representativo completo."""
    reg = client.post(
        "/api/transformacion/necesidad",
        headers=auth_headers,
        json={
            "titulo": "E2E Transformación",
            "necesidad": "Cuellos de botella en logística",
            "objetivo": "Reducir tiempos de entrega",
            "area_proceso": "Logística",
            "nivel": "PRELIMINAR",
        },
    ).json()
    eid = reg["expediente"]["id"]

    rec = client.get("/api/transformacion/recorrido", headers=auth_headers)
    assert rec.status_code == 200
    assert len(rec.json()["pasos"]) >= 5

    diag = client.post(f"/api/transformacion/expedientes/{eid}/diagnosticar", headers=auth_headers).json()
    assert diag["empleado_ia_requerimientos"] is not None or diag["capacidades_externas"]

    dossier = client.get("/api/transformacion/dossier", headers=auth_headers).json()
    assert dossier["etapa_actual"] == "OPORTUNIDADES"
    assert len(dossier["alternativas"]) >= 1

    org_id = tx_db.query(User).filter(User.username == "admin").first().organization_id
    d_row = tx_db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == org_id).one()
    assert d_row.expediente_activo_id == eid
