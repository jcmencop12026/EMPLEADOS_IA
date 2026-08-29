"""P1 1290 — Transición APROBADA → EJECUTADA con trazabilidad."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
    password: str = "OptEjec*Test1",
) -> tuple[Organization, User, str]:
    from app.seed_orchestration import bootstrap_orchestration
    from app.seed_permissions import bootstrap_permissions
    from app.seed_salud import bootstrap_salud

    org = Organization(name=org_name, slug=f"ej-{uuid.uuid4().hex[:8]}")
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


def _opp(db: Session, org_id: str, *, codigo: str, estado: str = "PRIORIZADA") -> Opportunity:
    o = Opportunity(
        organization_id=org_id,
        codigo=codigo,
        tipo="financiera",
        dominio="financiero",
        titulo=f"Oportunidad {codigo}",
        valor_potencial=50_000_000,
        costo_estimado=10_000_000,
        impacto_estimado=30_000_000,
        confianza=0.7,
        urgencia="MEDIA",
        riesgo="MEDIO",
        estado=estado,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def _crear_y_aprobar(client: TestClient, headers: dict[str, str], db: Session, org_id: str) -> str:
    _opp(db, org_id, codigo=f"O{uuid.uuid4().hex[:4].upper()}")
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
        json={"justificacion": "Alineado con plan estratégico"},
    )
    assert approve.status_code == 200
    assert approve.json()["estado"] == "APROBADA"
    return rec_id


def test_p1_01_propuesta_a_aprobada(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Prop Aprob")
        headers = auth_header(_token(client, user.username, password))
        _opp(db, org.id, codigo="PA1")
        create = client.post(
            "/api/optimizacion/recomendaciones",
            headers=headers,
            json={"objetivo": "MAXIMIZAR_VALOR"},
        )
        assert create.json()["estado"] == "PROPUESTA"
        rec_id = create.json()["id"]
        approve = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/aprobar",
            headers=headers,
            json={"justificacion": "Validada por comité"},
        )
        assert approve.status_code == 200
        assert approve.json()["estado"] == "APROBADA"
    finally:
        db.close()


def test_p1_02_aprobada_a_ejecutada_automatica(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Ejec Auto")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        ejecutar = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert ejecutar.status_code == 200, ejecutar.text
        body = ejecutar.json()
        assert body["estado"] == "EJECUTADA"
        assert body["ejecucion"]["estado"] == "EJECUTADA"
        assert body["ejecucion"]["tipo"] == "AUTOMATICA"
        assert body["ejecucion"]["correlation_id"]
        assert body["ejecucion"]["execution_reference"]
        assert body["ejecucion"]["learning_refs"]
        assert body["resultado"]["ejecucion"]["oportunidades"][0]["work_plan_id"]
    finally:
        db.close()


def test_p1_03_aprobada_pendiente_humana(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Ejec Humana")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        pendiente = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "HUMANA_EXTERNA"},
        )
        assert pendiente.status_code == 200, pendiente.text
        body = pendiente.json()
        assert body["estado"] == "APROBADA"
        assert body["ejecucion"]["estado"] == "PENDIENTE_EJECUCION_HUMANA"
        assert body["ejecucion"]["tipo"] == "HUMANA_EXTERNA"
        confirm = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/confirmar-ejecucion",
            headers=headers,
            json={"referencia_externa": "ACTA-COMITE-2026-001", "notas": "Ejecutado en campo"},
        )
        assert confirm.status_code == 200
        assert confirm.json()["estado"] == "EJECUTADA"
        assert confirm.json()["ejecucion"]["referencia_externa"] == "ACTA-COMITE-2026-001"
    finally:
        db.close()


def test_p1_04_idempotencia_ejecutada(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Idempot")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        first = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert first.status_code == 200
        corr = first.json()["ejecucion"]["correlation_id"]
        second = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert second.status_code == 200
        assert second.json()["estado"] == "EJECUTADA"
        assert second.json()["ejecucion"]["idempotent"] is True
        assert second.json()["ejecucion"]["correlation_id"] == corr
    finally:
        db.close()


def test_p1_05_fallo_no_marca_ejecutada(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Fallo")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        with patch("app.services.proactive_service.activate_opportunity", side_effect=RuntimeError("fallo simulado")):
            fail = client.post(
                f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
                headers=headers,
                json={"tipo_ejecucion": "AUTOMATICA"},
            )
        assert fail.status_code == 400
        detail = client.get(f"/api/optimizacion/recomendaciones/{rec_id}", headers=headers)
        assert detail.json()["estado"] == "FALLIDA"
        assert detail.json()["ejecucion"]["estado"] == "FALLIDA"
        assert "fallo simulado" in str(detail.json()["ejecucion"]["error"])
    finally:
        db.close()


def test_p1_06_viewer_no_aprueba(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Viewer Ejec", role="viewer")
        headers = auth_header(_token(client, user.username, password))
        denied = client.post(
            "/api/optimizacion/recomendaciones/fake-id/aprobar",
            headers=headers,
            json={"justificacion": "x" * 5},
        )
        assert denied.status_code == 403
    finally:
        db.close()


def test_p1_07_viewer_no_ejecuta(client: TestClient):
    db = TestingSessionLocal()
    try:
        _, user, password = _create_tenant(db, org_name="Org Viewer Ejec2", role="viewer")
        headers = auth_header(_token(client, user.username, password))
        denied = client.post(
            "/api/optimizacion/recomendaciones/fake-id/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert denied.status_code == 403
    finally:
        db.close()


def test_p1_08_cross_tenant_ejecucion(client: TestClient):
    db = TestingSessionLocal()
    try:
        org_a, user_a, pass_a = _create_tenant(db, org_name="Org A Ejec")
        _, user_b, pass_b = _create_tenant(db, org_name="Org B Ejec")
        headers_a = auth_header(_token(client, user_a.username, pass_a))
        headers_b = auth_header(_token(client, user_b.username, pass_b))
        rec_id = _crear_y_aprobar(client, headers_a, db, org_a.id)
        denied = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers_b,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert denied.status_code in (400, 404)
    finally:
        db.close()


def test_p1_09_auditoria_ejecucion(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Audit Ejec")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        hist = client.get(f"/api/optimizacion/historial?recomendacion_id={rec_id}", headers=headers)
        acciones = {e["accion"] for e in hist.json()}
        assert "recomendacion.aprobada" in acciones
        assert "recomendacion.ejecutada" in acciones
        count = db.query(OptimizacionAuditoria).filter(
            OptimizacionAuditoria.organization_id == org.id,
            OptimizacionAuditoria.recomendacion_id == rec_id,
        ).count()
        assert count >= 2
    finally:
        db.close()


def test_p1_10_correlation_id_preservado(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Corr")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        res = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        corr = res.json()["ejecucion"]["correlation_id"]
        hist = client.get(f"/api/optimizacion/historial?recomendacion_id={rec_id}", headers=headers)
        ejecutada = next(e for e in hist.json() if e["accion"] == "recomendacion.ejecutada")
        assert ejecutada["detalle"]["correlation_id"] == corr
    finally:
        db.close()


def test_p1_11_referencia_ejecucion_creada(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Ref")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        res = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        ref = res.json()["ejecucion"]["execution_reference"]
        assert ref == f"opt-rec:{rec_id}"
        assert res.json()["resultado"]["ejecucion"]["execution_reference"] == ref
    finally:
        db.close()


def test_p1_12_referencia_para_aprendizaje_1260(client: TestClient):
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Learn Link")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        res = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        refs = res.json()["ejecucion"]["learning_refs"]
        assert len(refs) >= 1
        assert refs[0]["opportunity_id"]
        assert refs[0]["recomendacion_id"] == rec_id
        assert refs[0].get("work_plan_id")
    finally:
        db.close()


def test_p1_ciclo_aprobacion_ejecucion_resultado_aprendizaje(client: TestClient):
    """RECOMENDACIÓN → APROBACIÓN → EJECUCIÓN → referencia consumible por 1260."""
    db = TestingSessionLocal()
    try:
        org, user, password = _create_tenant(db, org_name="Org Ciclo P1")
        headers = auth_header(_token(client, user.username, password))
        rec_id = _crear_y_aprobar(client, headers, db, org.id)
        ejecutar = client.post(
            f"/api/optimizacion/recomendaciones/{rec_id}/ejecutar",
            headers=headers,
            json={"tipo_ejecucion": "AUTOMATICA"},
        )
        assert ejecutar.status_code == 200
        opp_id = ejecutar.json()["ejecucion"]["learning_refs"][0]["opportunity_id"]
        ciclo = client.post(
            "/api/aprendizaje/ciclos",
            headers=headers,
            json={"opportunity_id": opp_id, "valor_real": 40_000_000, "impacto_real": 25_000_000},
        )
        assert ciclo.status_code == 201, ciclo.text
        assert ciclo.json()["opportunity_id"] == opp_id
    finally:
        db.close()
