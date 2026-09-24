"""BLOQUE 1260 — Aprendizaje, retroalimentación y repriorización."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.learning_models import AprendizajeAuditoria, CicloAprendizaje
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from conftest import TestingSessionLocal, auth_header

pytestmark = [pytest.mark.operations]


def _token(client: TestClient, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_tenant(
    db: Session,
    *,
    org_name: str,
    role: str = "admin",
    password: str = "Aprend1260*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"apr-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org.id)
    bootstrap_salud(db, org.id)
    username = f"user-{uuid.uuid4().hex[:6]}"
    user = User(
        organization_id=org.id,
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="ACTIVE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return org, user, password


def _create_opportunity_db(db: Session, org_id: str) -> Opportunity:
    opp = Opportunity(
        organization_id=org_id,
        codigo=f"OPP-{uuid.uuid4().hex[:6].upper()}",
        tipo="financiera",
        dominio="financiero",
        titulo="Oportunidad prueba 1260",
        impacto_estimado=1_000_000,
        valor_potencial=800_000,
        costo_estimado=200_000,
        prioridad_score=55.0,
        confianza=0.7,
        urgencia="MEDIA",
        riesgo="MEDIO",
        estado="ACTIVA",
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


def test_1260_viewer_denied_evaluate(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Viewer 1260", role="viewer")
        headers = auth_header(_token(client, user.username, password))
        opp = _create_opportunity_db(db, user.organization_id)
        denied = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers,
            json={"opportunity_id": opp.id},
        )
        assert denied.status_code == 403
    finally:
        db.close()


def test_1260_ciclo_completo_con_control_humano(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Ciclo 1260")
        headers = auth_header(_token(client, user.username, password))
        opp = _create_opportunity_db(db, user.organization_id)

        create = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers,
            json={"opportunity_id": opp.id, "valor_real": 500_000, "impacto_real": 700_000},
        )
        assert create.status_code == 201, create.text
        ciclo_id = create.json()["id"]
        assert create.json()["estado"] == "ABIERTO"

        evaluate = client.post(
            f"/api/aprendizaje/ciclos/{ciclo_id}/evaluar",
            headers=headers,
            json={"valor_real": 500_000, "impacto_real": 700_000, "tipo_explicacion": "CONFIRMADA"},
        )
        assert evaluate.status_code == 200, evaluate.text
        body = evaluate.json()
        assert body["ciclo"]["estado"] == "EVALUADO"
        assert body["desviaciones"]["valor"]["direccion"] == "INFERIOR"
        assert body["explicacion_prioridad"]["score"] is not None
        assert len(body["recalibraciones"]) >= 1

        rec_id = body["recalibraciones"][0]["id"]
        assert body["recalibraciones"][0]["estado"] == "SUGERIDA"

        approve = client.post(f"/api/aprendizaje/recalibraciones/{rec_id}/aprobar", headers=headers)
        assert approve.status_code == 200
        assert approve.json()["estado"] == "APROBADA"

        apply_res = client.post(f"/api/aprendizaje/recalibraciones/{rec_id}/aplicar", headers=headers)
        assert apply_res.status_code == 200
        assert apply_res.json()["estado"] == "APLICADA"

        historial = client.get("/api/aprendizaje/historial", headers=headers)
        assert historial.status_code == 200
        acciones = {e["accion"] for e in historial.json()}
        assert "ciclo.creado" in acciones
        assert "ciclo.evaluado" in acciones
        assert "recalibracion.aplicada" in acciones

        patrones = client.get("/api/aprendizaje/patrones", headers=headers)
        assert patrones.status_code == 200
        assert len(patrones.json()) >= 1
    finally:
        db.close()


def test_1260_rechazo_recalibracion(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Rechazo 1260")
        headers = auth_header(_token(client, user.username, password))
        opp = _create_opportunity_db(db, user.organization_id)
        ciclo = client.post("/api/aprendizaje/ciclos", headers=headers, json={"opportunity_id": opp.id})
        ciclo_id = ciclo.json()["id"]
        ev = client.post(
            f"/api/aprendizaje/ciclos/{ciclo_id}/evaluar",
            headers=headers,
            json={"valor_real": 100_000, "impacto_real": 100_000},
        )
        rec_id = ev.json()["recalibraciones"][0]["id"]
        reject = client.post(
            f"/api/aprendizaje/recalibraciones/{rec_id}/rechazar",
            headers=headers,
            json={"motivo": "Evidencia insuficiente para ajustar prioridad"},
        )
        assert reject.status_code == 200
        assert reject.json()["estado"] == "RECHAZADA"
        assert reject.json()["motivo_rechazo"]
    finally:
        db.close()


def test_1260_cross_tenant_isolation(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user_a, pass_a = _create_tenant(db, org_name="Org A 1260")
        _, user_b, pass_b = _create_tenant(db, org_name="Org B 1260")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        headers_b = auth_header(_token(client, user_b.username, pass_b))
        opp_a = _create_opportunity_db(db, user_a.organization_id)
        create = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers_a,
            json={"opportunity_id": opp_a.id},
        )
        ciclo_id = create.json()["id"]
        denied = client.get(f"/api/aprendizaje/ciclos/{ciclo_id}", headers=headers_b)
        assert denied.status_code == 404
        list_b = client.get("/api/aprendizaje/ciclos", headers=headers_b)
        assert all(c["opportunity_id"] != opp_a.id for c in list_b.json())
    finally:
        db.close()


def test_1260_sin_proveedor_ia(client: TestClient):
    """El motor funciona sin OpenAI/Ollama — solo reglas determinísticas."""
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Sin IA 1260")
        headers = auth_header(_token(client, user.username, password))
        opp = _create_opportunity_db(db, user.organization_id)
        res = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers,
            json={"opportunity_id": opp.id},
        )
        assert res.status_code == 201
        ciclo_id = res.json()["id"]
        ev = client.post(
            f"/api/aprendizaje/ciclos/{ciclo_id}/evaluar",
            headers=headers,
            json={"valor_real": 900_000, "impacto_real": 950_000},
        )
        assert ev.status_code == 200
        assert "formula" in ev.json()["explicacion_prioridad"]
    finally:
        db.close()


def test_1260_auditoria_registrada(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Audit 1260")
        headers = auth_header(_token(client, user.username, password))
        opp = _create_opportunity_db(db, org.id)
        client.post("/api/aprendizaje/ciclos", headers=headers, json={"opportunity_id": opp.id})
        count = (
            db.query(AprendizajeAuditoria)
            .filter(AprendizajeAuditoria.organization_id == org.id)
            .count()
        )
        assert count >= 1
    finally:
        db.close()
