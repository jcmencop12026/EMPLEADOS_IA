"""BLOQUE 1100 — cierre operativo UI/API oportunidades y cadena de ejecución."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.security import hash_password
from app.services import proactive_service as svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def opp_db(client):
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db: Session) -> tuple[str, str]:
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


def _signal_payload() -> dict:
    return {
        "titulo": "Recuperación financiera urgente",
        "tipo_oportunidad": "FINANCIERA",
        "indicadores": {"cartera_vencida": 45_000_000, "dias_mora": 90},
        "impacto_estimado": 12_000_000,
        "valor_potencial": 8_000_000,
        "urgencia": "CRITICA",
        "riesgo": "ALTO",
        "esfuerzo": "MEDIO",
        "source_reference": f"b1100-{uuid.uuid4().hex[:8]}",
    }


def _create_ready_opportunity(db: Session, org_id: str, user_id: str) -> Opportunity:
    result = svc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo="financiera",
        dominio="financiero",
        evento="bloque_1100",
        payload=_signal_payload(),
        origen="test",
        user_id=user_id,
    )
    db.commit()
    opp = db.query(Opportunity).get(result["opportunity_id"])
    assert opp
    svc.transition_state(db, opp, "PENDIENTE_APROBACION", actor_id=user_id, motivo="test 1100")
    db.commit()
    return opp


def test_1100_seguimiento_api(client: TestClient, auth_headers, opp_db):
    org_id, user_id = _admin(opp_db)
    opp = _create_ready_opportunity(opp_db, org_id, user_id)
    svc.approve_opportunity(opp_db, opp, user_id=user_id, aprobado=True)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()

    res = client.post(
        f"/api/oportunidades/{opp.id}/seguimiento",
        headers=auth_headers,
        json={"accion": "Revisión semanal", "bloqueo": "Sin bloqueos"},
    )
    assert res.status_code == 200
    assert res.json().get("tracking_id")

    trace = client.get(f"/api/oportunidades/{opp.id}/trazabilidad", headers=auth_headers)
    assert trace.status_code == 200
    seg = trace.json()["seguimiento"]
    assert any(s["accion"] == "Revisión semanal" for s in seg)
    assert any(s.get("responsable_id") for s in seg)
    assert any(s.get("fecha") for s in seg)


def test_1100_resultado_materializacion_api(client: TestClient, auth_headers, opp_db):
    org_id, user_id = _admin(opp_db)
    opp = _create_ready_opportunity(opp_db, org_id, user_id)
    svc.approve_opportunity(opp_db, opp, user_id=user_id, aprobado=True)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()

    res = client.post(
        f"/api/oportunidades/{opp.id}/resultado",
        headers=auth_headers,
        json={
            "valor_real": 6_200_000,
            "valor_esperado": 8_000_000,
            "evidencia": {"nota": "Cierre operativo 1100"},
            "estado_resultado": "EXITO",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["resultado"]["valor_real"] == 6_200_000
    assert body["oportunidad"]["estado"] == "MATERIALIZADA"
    assert float(body["oportunidad"]["valor_materializado"]) == 6_200_000


def test_1100_aprobacion_rechazo_api(client: TestClient, auth_headers, opp_db):
    org_id, user_id = _admin(opp_db)
    opp_ok = _create_ready_opportunity(opp_db, org_id, user_id)
    opp_no = _create_ready_opportunity(opp_db, org_id, user_id)
    opp_db.commit()

    ok = client.post(
        f"/api/oportunidades/{opp_ok.id}/aprobar",
        headers=auth_headers,
        json={"aprobado": True, "motivo": "Aprobada bloque 1100"},
    )
    assert ok.status_code == 200
    assert ok.json()["estado"] == "APROBADA"

    reject = client.post(
        f"/api/oportunidades/{opp_no.id}/aprobar",
        headers=auth_headers,
        json={"aprobado": False, "motivo": "Rechazada bloque 1100"},
    )
    assert reject.status_code == 200
    assert reject.json()["estado"] == "DESCARTADA"


def test_1100_trazabilidad_transiciones(opp_db):
    org_id, user_id = _admin(opp_db)
    opp = _create_ready_opportunity(opp_db, org_id, user_id)
    svc.approve_opportunity(opp_db, opp, user_id=user_id, aprobado=True)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    svc.register_result(opp_db, opp, user_id=user_id, valor_real=1_500_000, evidencia={"k": 1})
    opp_db.commit()

    trace = svc.get_full_trace(opp_db, opp.id, org_id)
    assert trace["seguimiento"]
    assert any(t["a"] == "APROBADA" for t in trace["transiciones"])
    assert any(t["a"] == "MATERIALIZADA" for t in trace["transiciones"])
    assert trace["seguimiento"][0].get("fecha")


def test_1100_cadena_oportunidad_ejecucion_resultado(opp_db):
    org_id, user_id = _admin(opp_db)
    opp = _create_ready_opportunity(opp_db, org_id, user_id)
    svc.approve_opportunity(opp_db, opp, user_id=user_id, aprobado=True)
    act = svc.activate_opportunity(opp_db, opp, user_id=user_id)
    svc.register_result(opp_db, opp, user_id=user_id, valor_real=2_000_000, evidencia={"doc": "ok"})
    opp_db.commit()

    assert opp.work_plan_id == act["work_plan_id"]
    assert opp.estado == "MATERIALIZADA"
    assert opp.resultado_json


def test_1100_cross_tenant_aislamiento(client: TestClient, auth_headers, opp_db):
    org_b = Organization(name=f"OrgB-1100-{uuid.uuid4().hex[:6]}")
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    db.add(org_b)
    db.commit()
    opp_b = svc.run_proactive_pipeline(
        db,
        organization_id=org_b.id,
        tipo="test",
        dominio="comercial",
        evento="tenant_b_1100",
        payload={"titulo": "B", "indicadores": {"x": 1}, "source_reference": f"b-{uuid.uuid4().hex[:6]}"},
        user_id=None,
    )
    db.commit()
    opp_id = opp_b["opportunity_id"]

    for path in (
        f"/api/oportunidades/{opp_id}",
        f"/api/oportunidades/{opp_id}/trazabilidad",
    ):
        res = client.get(path, headers=auth_headers)
        assert res.status_code == 404

    for method, path, body in (
        ("post", f"/api/oportunidades/{opp_id}/seguimiento", {"accion": "x"}),
        ("post", f"/api/oportunidades/{opp_id}/resultado", {"valor_real": 1}),
        ("post", f"/api/oportunidades/{opp_id}/aprobar", {"aprobado": True}),
    ):
        res = client.request(method, path, headers=auth_headers, json=body)
        assert res.status_code == 404
    db.close()


def test_1100_rbac_viewer_sin_gestion(client: TestClient, opp_db):
    org_id, _ = _admin(opp_db)
    viewer = User(
        username=f"viewer-1100-{uuid.uuid4().hex[:6]}",
        email=f"v1100-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=org_id,
        role="viewer",
        is_active=True,
    )
    opp_db.add(viewer)
    opp_db.commit()

    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    opp = _create_ready_opportunity(opp_db, org_id, viewer.id)
    opp_db.commit()

    assert client.get("/api/oportunidades", headers=headers).status_code == 200
    assert client.get(f"/api/oportunidades/{opp.id}", headers=headers).status_code == 200
    assert client.get(f"/api/oportunidades/{opp.id}/trazabilidad", headers=headers).status_code == 200

    denied = client.post(
        f"/api/oportunidades/{opp.id}/seguimiento",
        headers=headers,
        json={"accion": "no permitido"},
    )
    assert denied.status_code == 403

    denied2 = client.post(
        f"/api/oportunidades/{opp.id}/resultado",
        headers=headers,
        json={"valor_real": 100},
    )
    assert denied2.status_code == 403
