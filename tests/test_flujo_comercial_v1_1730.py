"""Flujo comercial V1 EIAAX — Bloque 1730."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(db: Session, org_name: str) -> tuple[Organization, str, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"t-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    password = "Flujo1730*Test1"
    user = User(
        organization_id=org.id,
        username=f"u-{uuid.uuid4().hex[:6]}",
        password_hash=hash_password(password),
        role="admin",
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, password, user.username


def test_catalogo_contextual_salud_glosas(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "Flujo-Salud")
    db.close()
    headers = auth_header(_token(client, username, password))
    ev = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Auditoría facturación IPS",
            "entidad_nombre": "IPS Demo",
            "necesidad": "Reducir glosas en facturación",
            "objetivo": "Recuperar ingresos",
            "area_proceso": "facturacion",
            "sector": "salud",
            "nivel": "DIAGNOSTICA",
        },
    )
    assert ev.status_code == 201, ev.text
    eid = ev.json()["id"]
    cat = client.get(f"/api/flujo-comercial/expedientes/{eid}/catalogo-informacion", headers=headers)
    assert cat.status_code == 200
    campos = {c["campo"] for c in cat.json()["aplicable"]}
    assert "salud_glosas" in campos
    assert "metricas_actuales" in campos
    # No pedir glosas universalmente
    ev2 = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Logística general",
            "entidad_nombre": "Empresa X",
            "necesidad": "Optimizar rutas",
            "nivel": "DIAGNOSTICA",
        },
    )
    eid2 = ev2.json()["id"]
    cat2 = client.get(f"/api/flujo-comercial/expedientes/{eid2}/catalogo-informacion", headers=headers)
    campos2 = {c["campo"] for c in cat2.json()["aplicable"]}
    assert "salud_glosas" not in campos2


def test_suficiencia_y_propuesta_desde_dossier(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "Flujo-Prop")
    db.close()
    headers = auth_header(_token(client, username, password))
    ev = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={
            "titulo": "Propuesta dossier",
            "entidad_nombre": "Cliente SA",
            "necesidad": "Automatizar cobranza",
            "area_proceso": "finanzas",
            "sector": "finanzas",
            "nivel": "DIAGNOSTICA",
        },
    )
    eid = ev.json()["id"]
    client.post(f"/api/flujo-comercial/expedientes/{eid}/sync-informacion", headers=headers)
    suf = client.get(f"/api/flujo-comercial/expedientes/{eid}/suficiencia", headers=headers)
    assert suf.status_code == 200
    opp = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={
            "tipo": "operativa",
            "dominio": "finanzas",
            "evento": "flujo_test",
            "payload": {"titulo": "Opp cobranza", "impacto_estimado": 60000},
        },
    )
    opp_id = opp.json().get("opportunity_id") or opp.json().get("id")
    client.patch(
        f"/api/flujo-comercial/oportunidades/{opp_id}/clasificacion",
        headers=headers,
        json={"origen_comercial": "INTERNA", "presentar_cliente": True, "clasificacion_valor": "ESTIMADO"},
    )
    client.post(
        f"/api/evaluaciones/{eid}/oportunidades/vincular",
        headers=headers,
        json={"opportunity_id": opp_id},
    )
    for item in client.get(f"/api/evaluaciones/{eid}", headers=headers).json().get("informacion", []):
        if item.get("obligatorio"):
            client.patch(
                f"/api/evaluaciones/{eid}/informacion/{item['id']}",
                headers=headers,
                json={"respuesta": "Dato demo", "estado": "RECIBIDO"},
            )
    prop = client.post(
        f"/api/flujo-comercial/expedientes/{eid}/generar-propuesta",
        headers=headers,
        json={"opportunity_id": opp_id},
    )
    assert prop.status_code == 200, prop.text
    data = prop.json()
    assert data["proposal_id"]
    doc = data["detail"].get("documento_cliente") or {}
    assert doc.get("que_encontramos") is not None or doc.get("resumen_ejecutivo")
    assert doc.get("economia_privada_incluida") is False
    assert "POTENCIAL" in (doc.get("nota_potencial") or "")


def test_instrumentos_y_garantias(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "Flujo-Inst")
    db.close()
    headers = auth_header(_token(client, username, password))
    demo = client.post("/api/flujo-comercial/demo/recorrido", headers=headers, json={"sector": "salud", "area": "facturacion"})
    assert demo.status_code == 200, demo.text
    pid = demo.json()["proposal_id"]
    inst = client.get(f"/api/flujo-comercial/propuestas/{pid}/instrumentos", headers=headers)
    assert inst.status_code == 200
    assert len(inst.json()) >= 2
    tipos = {i["tipo"] for i in inst.json()}
    assert "NDA" in tipos
    gar = client.get(f"/api/flujo-comercial/propuestas/{pid}/compromisos-garantia", headers=headers)
    assert gar.status_code == 200
    assert len(gar.json()) >= 1
    assert gar.json()[0]["tipo_compromiso"] == "CONTROL_NUESTRO"


def test_potencial_no_valor_realizado(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "Flujo-Pot")
    db.close()
    headers = auth_header(_token(client, username, password))
    ev = client.post(
        "/api/evaluaciones",
        headers=headers,
        json={"titulo": "Test potencial", "entidad_nombre": "Entidad", "nivel": "PRELIMINAR"},
    )
    assert ev.status_code == 201, ev.text
    eid = ev.json()["id"]
    opp = client.post(
        "/api/oportunidades/pipeline-proactivo",
        headers=headers,
        json={"tipo": "comercial", "dominio": "mercado", "evento": "x", "payload": {"titulo": "Pot", "impacto_estimado": 100000}},
    )
    opp_id = opp.json().get("opportunity_id")
    client.patch(
        f"/api/flujo-comercial/oportunidades/{opp_id}/clasificacion",
        headers=headers,
        json={"clasificacion_valor": "POTENCIAL", "presentar_cliente": True},
    )
    client.post(f"/api/evaluaciones/{eid}/oportunidades/vincular", headers=headers, json={"opportunity_id": opp_id})
    lista = client.get(f"/api/flujo-comercial/expedientes/{eid}/oportunidades", headers=headers)
    row = next(o for o in lista.json() if o["id"] == opp_id)
    assert row["clasificacion_valor"] == "POTENCIAL"
    assert row["es_valor_realizado"] is False


def test_recorrido_demo_completo(client: TestClient):
    db = TestingSessionLocal()
    _, password, username = _create_tenant(db, "Flujo-Demo")
    db.close()
    headers = auth_header(_token(client, username, password))
    res = client.post("/api/flujo-comercial/demo/recorrido", headers=headers, json={})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["evaluacion_id"]
    assert data["proposal_id"]
    assert data["opportunity_id"]
    assert "DEMO" in data["flujo"]
