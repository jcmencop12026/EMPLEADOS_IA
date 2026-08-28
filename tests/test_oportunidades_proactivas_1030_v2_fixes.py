"""Correcciones quirúrgicas certificación V2 — OP-A, OP-B, OP-F."""

from __future__ import annotations

import uuid

import pytest

from app.opportunity_models import Opportunity
from app.services import proactive_service as svc

pytestmark = [pytest.mark.operations]


@pytest.fixture
def opp_db():
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    yield db
    db.close()


def _admin(db):
    from app.models import User
    user = db.query(User).filter(User.username == "admin").first()
    assert user
    return user.organization_id, user.id


def test_v2_op_b_senal_inmadura_no_promovida(opp_db):
    org_id, user_id = _admin(opp_db)
    payload = {
        "titulo": "Señal inmadura comercial",
        "tipo_oportunidad": "COMERCIAL",
        "indicadores": {"leads_variacion_pct": 12, "conversion_historica_pct": 3.1},
        "impacto_estimado": 800_000,
        "evidencia_insuficiente": True,
        "datos_financieros_suficientes": False,
        "source_reference": f"v2-op-b-{uuid.uuid4().hex[:8]}",
    }
    result = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="comercial", dominio="comercial",
        evento="crecimiento_interes_segmento", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    assert result.get("opportunity_id") is None
    assert result.get("signal_id")
    ctx = svc.build_context_360(opp_db, organization_id=org_id, dominio="comercial", payload=payload)
    assert ctx["senal_inmadura"] is True


def test_v2_op_a_requiere_aprobacion_y_workplan(opp_db):
    org_id, user_id = _admin(opp_db)
    payload = {
        "titulo": "Oportunidad urgente con SLA",
        "tipo_oportunidad": "OPERATIVA",
        "indicadores": {"demanda_variacion_pct": 34},
        "historico": {"registrado": True},
        "impacto_estimado": 6_000_000,
        "valor_potencial": 4_200_000,
        "urgencia": "ALTA",
        "sla_horas": 36,
        "source_reference": f"v2-op-a-{uuid.uuid4().hex[:8]}",
    }
    result = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="operativa", dominio="operativo",
        evento="incremento_sostenido_demanda", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.estado == "PENDIENTE_APROBACION"
    assert result["siguiente_accion"]["autorizacion"] == "REQUIERE_APROBACION"
    assert opp.momento == "AHORA"
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    act = svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    assert act["work_plan_id"]
    assert opp.work_plan_id == act["work_plan_id"]


def test_v2_op_f_conflicto_observar(opp_db):
    org_id, user_id = _admin(opp_db)
    payload = {
        "titulo": "Evidencia contradictoria",
        "tipo_oportunidad": "RIESGO",
        "indicadores": {"valor_principal": 0.86, "tasa_conversion": 0.86},
        "conocimiento_autorizado": {"valor": 0.12, "fuente": "B"},
        "historico": {"registrado": True},
        "impacto_estimado": 3_000_000,
        "valor_potencial": 2_000_000,
        "source_reference": f"v2-op-f-{uuid.uuid4().hex[:8]}",
    }
    result = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="riesgo", dominio="comercial",
        evento="contradiccion", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    ctx = svc.build_context_360(opp_db, organization_id=org_id, dominio="comercial", payload=payload)
    assert ctx["conflicto"] is True
    assert opp.pertinencia == "SOLICITAR_APROBACION"
    assert opp.momento == "OBSERVAR"
    assert opp.work_plan_id is None
    assert opp.estado == "PENDIENTE_APROBACION"


def test_v2_op_e_sin_valor_inventado(opp_db):
    org_id, user_id = _admin(opp_db)
    payload = {
        "titulo": "Datos insuficientes",
        "tipo_oportunidad": "AHORRO",
        "indicadores": {"variacion_consumo_pct": 9},
        "source_reference": f"v2-op-e-{uuid.uuid4().hex[:8]}",
    }
    result = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="ahorro", dominio="financiero",
        evento="posible_ahorro", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.pertinencia == "OBSERVAR"
    assert float(opp.valor_potencial or 0) == 0


def test_v2_px1_idempotencia_preservada(opp_db):
    org_id, user_id = _admin(opp_db)
    ref = f"v2-px1-{uuid.uuid4().hex[:8]}"
    payload = {
        "titulo": "Idempotencia",
        "tipo_oportunidad": "OPERATIVA",
        "indicadores": {"demanda_variacion_pct": 34},
        "historico": {"registrado": True},
        "impacto_estimado": 6_000_000,
        "valor_potencial": 4_200_000,
        "urgencia": "ALTA",
        "sla_horas": 36,
        "source_reference": ref,
    }
    r1 = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="operativa", dominio="operativo",
        evento="incremento_sostenido_demanda", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    r2 = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="operativa", dominio="operativo",
        evento="incremento_sostenido_demanda", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    assert r1["signal_id"] == r2["signal_id"]
    assert r2.get("deduplicated") is True
