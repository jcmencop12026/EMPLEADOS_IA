"""BLOQUE 1290 — Optimización, priorización avanzada y recomendaciones."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.learning_models import CicloAprendizaje
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.optimization_models import OptimizacionAuditoria
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
    password: str = "Opt1290*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"opt-{uuid.uuid4().hex[:8]}")
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


def _opp(
    db: Session,
    org_id: str,
    *,
    codigo: str,
    valor: float,
    costo: float,
    impacto: float,
    riesgo: str = "MEDIO",
) -> Opportunity:
    o = Opportunity(
        organization_id=org_id,
        codigo=codigo,
        tipo="financiera",
        dominio="financiero",
        titulo=f"Oportunidad {codigo}",
        valor_potencial=valor,
        costo_estimado=costo,
        impacto_estimado=impacto,
        confianza=0.7,
        urgencia="MEDIA",
        riesgo=riesgo,
        estado="ACTIVA",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def _headers(client: TestClient, db: Session, org_name: str = "Org Opt 1290") -> dict[str, str]:
    _, user, password = _create_tenant(db, org_name=org_name)
    return auth_header(_token(client, user.username, password))


def test_1290_priorizacion_simple(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        _opp(db, org.id, codigo="A", valor=80_000_000, costo=20_000_000, impacto=50_000_000)
        _opp(db, org.id, codigo="B", valor=40_000_000, costo=10_000_000, impacto=30_000_000)
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR", "restricciones": {"max_iniciativas": 2}},
        )
        assert sim.status_code == 200, sim.text
        body = sim.json()
        assert body["factible"] is True
        assert len(body["seleccion"]) == 2
        assert body["explicacion"]["por_que_primera"] is not None
    finally:
        db.close()


def test_1290_presupuesto_limitado(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        a = _opp(db, org.id, codigo="A", valor=100_000_000, costo=60_000_000, impacto=80_000_000)
        b = _opp(db, org.id, codigo="B", valor=50_000_000, costo=50_000_000, impacto=40_000_000)
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={
                "objetivo": "MAXIMIZAR_VALOR",
                "restricciones": {"presupuesto_maximo": 70_000_000, "max_iniciativas": 2},
                "opportunity_ids": [a.id, b.id],
            },
        )
        assert sim.status_code == 200
        body = sim.json()
        assert body["factible"] is True
        assert len(body["seleccion"]) == 1
        assert body["seleccion"][0] == a.id
    finally:
        db.close()


def test_1290_objetivos_configurables(client: TestClient):
    db = TestingSessionLocal()
    try:
        headers = _headers(client, db, "Org Objetivos")
        org = db.query(Organization).filter(Organization.name == "Org Objetivos").first()
        _opp(db, org.id, codigo="R1", valor=10_000_000, costo=8_000_000, impacto=5_000_000, riesgo="ALTO")
        _opp(db, org.id, codigo="R2", valor=12_000_000, costo=2_000_000, impacto=8_000_000, riesgo="BAJO")
        for obj in ("MAXIMIZAR_ROI", "MINIMIZAR_RIESGO", "RESULTADO_EQUILIBRADO"):
            res = client.post(
                "/api/optimizacion/simular",
                headers=headers,
                json={"objetivo": obj, "restricciones": {"max_iniciativas": 1}},
            )
            assert res.status_code == 200, f"objetivo {obj}: {res.text}"
            assert res.json()["factible"] is True
    finally:
        db.close()


def test_1290_obligatorias_y_excluidas(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        a = _opp(db, org.id, codigo="A", valor=30_000_000, costo=5_000_000, impacto=20_000_000)
        b = _opp(db, org.id, codigo="B", valor=90_000_000, costo=10_000_000, impacto=50_000_000)
        c = _opp(db, org.id, codigo="C", valor=20_000_000, costo=3_000_000, impacto=15_000_000)
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={
                "objetivo": "MAXIMIZAR_VALOR",
                "restricciones": {"obligatorias": [a.id], "excluidas": [b.id], "max_iniciativas": 2},
                "opportunity_ids": [a.id, b.id, c.id],
            },
        )
        assert sim.status_code == 200
        body = sim.json()
        assert a.id in body["seleccion"]
        assert b.id not in body["seleccion"]
    finally:
        db.close()


def test_1290_dependencias_e_incompatibles(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        a = _opp(db, org.id, codigo="A", valor=50_000_000, costo=10_000_000, impacto=30_000_000)
        b = _opp(db, org.id, codigo="B", valor=40_000_000, costo=8_000_000, impacto=25_000_000)
        c = _opp(db, org.id, codigo="C", valor=35_000_000, costo=7_000_000, impacto=20_000_000)
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={
                "objetivo": "MAXIMIZAR_VALOR",
                "restricciones": {
                    "requiere": [{"dependiente": a.id, "prerequisito": b.id}],
                    "incompatibles": [[a.id, c.id]],
                    "max_iniciativas": 3,
                },
                "opportunity_ids": [a.id, b.id, c.id],
            },
        )
        assert sim.status_code == 200
        sel = set(sim.json()["seleccion"])
        if a.id in sel:
            assert b.id in sel
            assert c.id not in sel
    finally:
        db.close()


def test_1290_sin_solucion_factible(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        a = _opp(db, org.id, codigo="A", valor=50_000_000, costo=80_000_000, impacto=30_000_000)
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={
                "objetivo": "MAXIMIZAR_VALOR",
                "restricciones": {"presupuesto_maximo": 10_000_000, "obligatorias": [a.id]},
                "opportunity_ids": [a.id],
            },
        )
        assert sim.status_code == 200
        body = sim.json()
        assert body["factible"] is False
        assert any("SIN SOLUCIÓN" in str(c) or "Presupuesto" in str(c) for c in body["conflictos"])
    finally:
        db.close()


def test_1290_aprendizaje_influye(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        opp = _opp(db, org.id, codigo="L1", valor=60_000_000, costo=15_000_000, impacto=40_000_000)
        db.add(
            CicloAprendizaje(
                organization_id=org.id,
                opportunity_id=opp.id,
                estado="EVALUADO",
                calidad_recomendacion="DEFICIENTE",
                impacto_esperado=50_000_000,
                impacto_real=20_000_000,
                valor_esperado=60_000_000,
                valor_real=25_000_000,
                created_by=user.id,
            )
        )
        db.commit()
        sim = client.post(
            "/api/optimizacion/simular",
            headers=headers,
            json={"objetivo": "RESULTADO_EQUILIBRADO", "opportunity_ids": [opp.id]},
        )
        assert sim.status_code == 200
        opps = sim.json()["oportunidades"]
        assert opps[0]["aprendizaje"]["ciclos"]
    finally:
        db.close()


def test_1290_control_humano_y_reoptimizacion(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        _opp(db, org.id, codigo="X", valor=50_000_000, costo=10_000_000, impacto=30_000_000)
        create = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR", "restricciones": {"max_iniciativas": 1}},
        )
        assert create.status_code == 201, create.text
        rec_id = create.json()["id"]
        approve = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/aprobar",
            headers=headers,
            json={"justificacion": "Alineado con plan estratégico trimestral"},
        )
        assert approve.status_code == 200
        assert approve.json()["estado"] == "APROBADA"
        recalc = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/recalcular",
            headers=headers,
            json={"restricciones": {"max_iniciativas": 2, "presupuesto_maximo": 200_000_000}},
        )
        assert recalc.status_code == 201
        assert recalc.json()["version"] == 2
    finally:
        db.close()


def test_1290_comparacion_escenarios(client: TestClient):
    db = TestingSessionLocal()
    try:
        headers = _headers(client, db, "Org Comparar")
        org = db.query(Organization).filter(Organization.name == "Org Comparar").first()
        _opp(db, org.id, codigo="C1", valor=70_000_000, costo=20_000_000, impacto=50_000_000)
        res = client.post(
            "/api/optimizacion/comparar",
            headers=headers,
            json={
                "restricciones_base": {"presupuesto_maximo": 100_000_000},
                "escenarios": [
                    {"objetivo": "MAXIMIZAR_VALOR"},
                    {"objetivo": "MINIMIZAR_RIESGO"},
                    {"objetivo": "RESULTADO_EQUILIBRADO"},
                ],
            },
        )
        assert res.status_code == 201, res.text
        body = res.json()
        assert len(body["escenarios"]) == 3
        assert body["grupo_comparacion_id"]
    finally:
        db.close()


def test_1290_rbac_viewer_denied_create(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Viewer 1290", role="viewer")
        headers = auth_header(_token(client, user.username, password))
        denied = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR"},
        )
        assert denied.status_code == 403
    finally:
        db.close()


def test_1290_cross_tenant(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_tenant(db, org_name="Org A 1290")
        _, user_b, pass_b = _create_tenant(db, org_name="Org B 1290")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        headers_b = auth_header(_token(client, user_b.username, pass_b))
        _opp(db, org_a.id, codigo="TA", valor=10_000_000, costo=2_000_000, impacto=5_000_000)
        create = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers_a,
            json={"objetivo": "MAXIMIZAR_VALOR"},
        )
        rec_id = create.json()["id"]
        denied = client.get(f"/api/optimizacion/recomendaciones/{rec_id}", headers=headers_b)
        assert denied.status_code == 404
    finally:
        db.close()


def test_1290_auditoria_y_explicabilidad(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prior Simple")
        headers = auth_header(_token(client, user.username, password))
        _opp(db, org.id, codigo="E1", valor=30_000_000, costo=5_000_000, impacto=20_000_000)
        create = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_IMPACTO"},
        )
        rec_id = create.json()["id"]
        detail = client.get(f"/api/optimizacion/recomendaciones/{rec_id}", headers=headers)
        assert detail.json()["explicacion"]["por_que_primera"]
        assert detail.json()["items"][0]["factores"]["contribuciones"]
        count = db.query(OptimizacionAuditoria).filter(OptimizacionAuditoria.organization_id == org.id).count()
        assert count >= 1
        hist = client.get("/api/optimizacion/historial", headers=headers)
        assert hist.status_code == 200
        assert any(e["accion"] == "recomendacion.creada" for e in hist.json())
    finally:
        db.close()


def test_1290_rechazo_recomendacion(client: TestClient):
    db = TestingSessionLocal()
    try:
        headers = _headers(client, db, "Org Rechazo 1290")
        org = db.query(Organization).filter(Organization.name == "Org Rechazo 1290").first()
        _opp(db, org.id, codigo="R1", valor=20_000_000, costo=5_000_000, impacto=10_000_000)
        create = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR"},
        )
        rec_id = create.json()["id"]
        reject = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/rechazar",
            headers=headers,
            json={"motivo": "No alineado con capacidad operativa actual"},
        )
        assert reject.status_code == 200
        assert reject.json()["estado"] == "RECHAZADA"
    finally:
        db.close()
