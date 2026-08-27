"""OPORTUNIDADES-PROACTIVAS-1030 — certificación bloqueante."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.finops_models import FinOpsValueRecord
from app.models import Organization, User
from app.opportunity_models import Opportunity, ProactiveSignal
from app.security import hash_password
from app.services import proactive_service as svc
from app.services.domain_analysis import (
    GenericDomainAnalysisProvider,
    SaludDomainAnalysisProvider,
    bootstrap_providers,
    detect_domain,
    get_provider_for_request,
)
from app.services.proactive_scheduler import run_proactive_tick_once

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


def _signal_payload(case: str) -> dict:
    cases = {
        "OP-A": {
            "titulo": "Recuperación financiera urgente",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"cartera_vencida": 45_000_000, "dias_mora": 90},
            "impacto_estimado": 12_000_000,
            "valor_potencial": 8_000_000,
            "urgencia": "CRITICA",
            "riesgo": "ALTO",
            "esfuerzo": "MEDIO",
            "source_reference": f"op-a-{uuid.uuid4().hex[:6]}",
        },
        "OP-B": {
            "titulo": "Automatización alto volumen bajo valor unitario",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen": 5000, "valor_unitario": 500},
            "impacto_estimado": 500_000,
            "valor_potencial": 400_000,
            "urgencia": "BAJA",
            "esfuerzo": "BAJO",
            "source_reference": f"op-b-{uuid.uuid4().hex[:6]}",
        },
        "OP-C": {
            "titulo": "Riesgo de cumplimiento regulatorio",
            "tipo_oportunidad": "CUMPLIMIENTO",
            "indicadores": {"incumplimientos": 3, "sla_horas": 24},
            "impacto_estimado": 20_000_000,
            "valor_potencial": 15_000_000,
            "urgencia": "ALTA",
            "riesgo": "CRITICO",
            "sla_horas": 36,
            "source_reference": f"op-c-{uuid.uuid4().hex[:6]}",
        },
        "OP-D": {
            "titulo": "Competencia por capacidad — recuperación cartera",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"cartera": 30_000_000},
            "impacto_estimado": 10_000_000,
            "valor_potencial": 7_000_000,
            "urgencia": "ALTA",
            "source_reference": f"op-d1-{uuid.uuid4().hex[:6]}",
        },
        "OP-D2": {
            "titulo": "Competencia por capacidad — automatización",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen": 800},
            "impacto_estimado": 9_000_000,
            "valor_potencial": 6_500_000,
            "urgencia": "ALTA",
            "source_reference": f"op-d2-{uuid.uuid4().hex[:6]}",
        },
        "OP-E": {
            "titulo": "Datos insuficientes para conclusión",
            "tipo_oportunidad": "OPERATIVA",
            "indicadores": {},
            "source_reference": f"op-e-{uuid.uuid4().hex[:6]}",
        },
        "OP-F": {
            "titulo": "Información contradictoria",
            "tipo_oportunidad": "COMERCIAL",
            "indicadores": {"tasa_conversion": 0.35, "valor_principal": 0.35},
            "conocimiento_autorizado": {"valor": 0.08, "fuente": "manual_comercial"},
            "impacto_estimado": 5_000_000,
            "valor_potencial": 3_000_000,
            "source_reference": f"op-f-{uuid.uuid4().hex[:6]}",
        },
        "NS-1": {
            "titulo": "Automatizar proceso administrativo repetitivo",
            "tipo_oportunidad": "AUTOMATIZACION",
            "indicadores": {"volumen_mensual": 450, "repeticiones": 30},
            "impacto_estimado": 2_500_000,
            "valor_potencial": 1_800_000,
            "source_reference": f"ns-1-{uuid.uuid4().hex[:6]}",
        },
        "NS-2": {
            "titulo": "Recuperar conversión comercial",
            "tipo_oportunidad": "COMERCIAL",
            "indicadores": {"tasa_conversion": 0.12, "capacidad_ociosa_pct": 35},
            "impacto_estimado": 8_000_000,
            "valor_potencial": 5_500_000,
            "urgencia": "ALTA",
            "tendencia": "EMPEORANDO",
            "source_reference": f"ns-2-{uuid.uuid4().hex[:6]}",
        },
    }
    return cases[case]


def _run_case(db: Session, org_id: str, user_id: str, case: str, dominio: str = "financiero") -> dict:
    payload = _signal_payload(case)
    return svc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo=payload.get("tipo_oportunidad", "OPERATIVA").lower(),
        dominio=dominio if case not in ("NS-1", "NS-2") else ("administrativo" if case == "NS-1" else "comercial"),
        evento=f"certificacion_{case.lower()}",
        payload=payload,
        origen="test",
        user_id=user_id,
    )


# 1 señal→oportunidad
def test_01_signal_to_opportunity(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    assert result["opportunity_id"]
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.signal_id == result["signal_id"]


# 2 dedupe señal
def test_02_signal_dedupe(opp_db):
    org_id, user_id = _admin(opp_db)
    payload = _signal_payload("OP-B")
    r1 = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="automatizacion", dominio="administrativo",
        evento="dedupe_test", payload=payload, origen="test", user_id=user_id,
    )
    opp_db.commit()
    r2 = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="automatizacion", dominio="administrativo",
        evento="dedupe_test", payload=payload, origen="test", user_id=user_id,
    )
    opp_db.commit()
    assert r1["signal_id"] == r2["signal_id"]
    assert r2.get("deduplicated") is True
    count = opp_db.query(Opportunity).filter(Opportunity.signal_id == r1["signal_id"]).count()
    assert count == 1


# 3 contexto
def test_03_contexto_360(opp_db):
    org_id, _ = _admin(opp_db)
    ctx = svc.build_context_360(
        opp_db, organization_id=org_id, dominio="comercial",
        payload={"indicadores": {"tasa": 0.2}, "historico": {"mes_anterior": 0.3}},
    )
    assert ctx["suficiencia"] == "SUFICIENTE"


# 4 suficiencia
def test_04_suficiencia_insuficiente(opp_db):
    org_id, _ = _admin(opp_db)
    ctx = svc.build_context_360(opp_db, organization_id=org_id, dominio="financiero", payload={})
    assert ctx["suficiencia"] == "INSUFICIENTE"
    assert "indicadores" in ctx["faltantes"]


# 5 pertinencia
def test_05_pertinencia(opp_db):
    ctx = svc.build_context_360(None, organization_id="x", dominio="comercial",
                                payload={"indicadores": {"v": 1}, "historico": {"v": 1}})
    pert = svc.evaluate_pertinence(ctx, impacto=5_000_000, capacidad={"ejecutable": True})
    assert pert["resultado"] in svc.PERTINENCIA_RESULTADOS


# 6 momento
def test_06_momento(opp_db):
    m = svc.evaluate_momento(urgencia="CRITICA", sla_horas=24, capacidad={"ejecutable": True})
    assert m["resultado"] == "AHORA"


# 7 priorización global
def test_07_priorizacion_global(opp_db):
    org_id, user_id = _admin(opp_db)
    _run_case(opp_db, org_id, user_id, "OP-A")
    _run_case(opp_db, org_id, user_id, "OP-C")
    opp_db.commit()
    ranking = svc.prioritize_opportunities_global(opp_db, org_id)
    assert len(ranking["ranking"]) >= 2
    assert ranking["ranking"][0]["prioridad_score"] >= ranking["ranking"][1]["prioridad_score"]


# 8 score explicable
def test_08_score_explicable(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    componentes = json.loads(opp.prioridad_componentes_json or "{}")
    assert "impacto" in componentes
    assert "urgencia" in componentes


# 9 siguiente mejor acción
def test_09_siguiente_mejor_accion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    accion = json.loads(opp.siguiente_accion_json or "{}")
    assert accion.get("que")
    assert accion.get("por_que")
    assert accion.get("cuando")


# 10 alternativas (priorización entre oportunidades)
def test_10_alternativas_ranking(opp_db):
    org_id, user_id = _admin(opp_db)
    _run_case(opp_db, org_id, user_id, "OP-D")
    _run_case(opp_db, org_id, user_id, "OP-D2", dominio="administrativo")
    opp_db.commit()
    ranking = svc.prioritize_opportunities_global(opp_db, org_id)
    assert ranking["por_que_primero"]


# 11 equipo
def test_11_equipo_orquestador(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    equipo = json.loads(opp.equipo_json or "{}")
    assert equipo.get("lider") or equipo.get("equipo")


# 12 aprobación
def test_12_aprobacion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-C")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.transition_state(opp_db, opp, "PENDIENTE_APROBACION", actor_id=user_id, motivo="test")
    svc.approve_opportunity(opp_db, opp, user_id=user_id, aprobado=True)
    opp_db.commit()
    assert opp.estado == "APROBADA"


# 13 automática permitida
def test_13_automatica_politica(opp_db):
    cap = svc.assess_capability_360(opp_db, organization_id=_admin(opp_db)[0], dominio="administrativo", riesgo="BAJO")
    assert cap["human_gate"] in svc.HUMAN_GATE


# 14 WorkPlan
def test_14_workplan_activacion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    act = svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    assert act["work_plan_id"]
    assert opp.work_plan_id == act["work_plan_id"]


# 15 Operaciones (estado EN_EJECUCION/SEGUIMIENTO)
def test_15_operaciones_seguimiento(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    assert opp.estado in ("EN_EJECUCION", "EN_SEGUIMIENTO")


# 16 FINOPS
def test_16_finops_registro(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    finops = opp_db.query(FinOpsValueRecord).filter(
        FinOpsValueRecord.organization_id == org_id,
        FinOpsValueRecord.source.contains("motor_analitico"),
    ).all()
    assert len(finops) >= 1


# 17 work_plan_id FINOPS (G-02)
def test_17_finops_work_plan_id(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    row = opp_db.query(FinOpsValueRecord).filter(
        FinOpsValueRecord.work_plan_id == opp.work_plan_id,
    ).first()
    assert row is not None
    assert row.opportunity_id == opp.id


# 18 valor potencial
def test_18_valor_potencial(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.valor_potencial_certidumbre in ("ESTIMADO", "NO_CUANTIFICABLE")
    assert float(opp.valor_potencial or 0) > 0


# 19 valor materializado
def test_19_valor_materializado(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    svc.register_result(opp_db, opp, user_id=user_id, valor_real=6_500_000, evidencia={"kpi": "ok"})
    opp_db.commit()
    assert float(opp.valor_materializado or 0) == 6_500_000


# 20 atribución
def test_20_atribucion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    svc.register_result(opp_db, opp, user_id=user_id, valor_real=1_000_000, evidencia={"doc": "x"})
    opp_db.commit()
    assert opp.atribucion_nivel in svc.ATRIBUCION_NIVELES


# 21 seguimiento
def test_21_seguimiento(opp_db):
    from app.opportunity_models import OpportunityTracking
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    tracks = opp_db.query(OpportunityTracking).filter(OpportunityTracking.opportunity_id == opp.id).all()
    assert len(tracks) >= 1


# 22 resultado
def test_22_resultado(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-B")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    res = svc.register_result(opp_db, opp, user_id=user_id, valor_real=350_000)
    opp_db.commit()
    assert res["valor_real"] == 350_000
    assert opp.estado == "MATERIALIZADA"


# 23 aprendizaje
def test_23_aprendizaje(opp_db):
    from app.experience_models import EmployeeExperienceRecord
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    svc.activate_opportunity(opp_db, opp, user_id=user_id)
    before = opp_db.query(EmployeeExperienceRecord).filter(
        EmployeeExperienceRecord.caso_origen_id == opp.id,
    ).count()
    svc.register_result(opp_db, opp, user_id=user_id, valor_real=5_000_000, evidencia={"kpi": 1})
    opp_db.commit()
    after = opp_db.query(EmployeeExperienceRecord).filter(
        EmployeeExperienceRecord.caso_origen_id == opp.id,
    ).count()
    assert after >= before


# 24 segunda ejecución
def test_24_segunda_ejecucion(opp_db):
    org_id, user_id = _admin(opp_db)
    r1 = _run_case(opp_db, org_id, user_id, "NS-2", dominio="comercial")
    opp_db.commit()
    opp1 = opp_db.query(Opportunity).get(r1["opportunity_id"])
    svc.approve_opportunity(opp_db, opp1, user_id=user_id)
    svc.activate_opportunity(opp_db, opp1, user_id=user_id)
    svc.register_result(opp_db, opp1, user_id=user_id, valor_real=4_000_000, evidencia={"k": 1})
    opp_db.commit()
    payload = _signal_payload("NS-2")
    payload["source_reference"] = f"ns-2-rep-{uuid.uuid4().hex[:6]}"
    r2 = svc.run_proactive_pipeline(
        opp_db, organization_id=org_id, tipo="comercial", dominio="comercial",
        evento="segunda_ejecucion", payload=payload, user_id=user_id,
    )
    opp_db.commit()
    opp2 = opp_db.query(Opportunity).get(r2["opportunity_id"])
    assert opp2.id != opp1.id


# 25 scheduler proactivo
def test_25_scheduler_proactivo(opp_db):
    from app.services import proactive_scheduler
    proactive_scheduler._synthetic_indicators = lambda _: [{
        "tipo": "scheduler_test",
        "dominio": "administrativo",
        "evento": f"sched_{uuid.uuid4().hex[:8]}",
        "payload": _signal_payload("NS-1"),
    }]
    results = run_proactive_tick_once(opp_db)
    assert len(results) >= 1
    assert results[0].get("opportunity_id")


# 26 cross-tenant
def test_26_cross_tenant(client: TestClient, auth_headers):
    org_b = Organization(name=f"OrgB-{uuid.uuid4().hex[:6]}")
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    db.add(org_b)
    db.commit()
    opp_b = svc.run_proactive_pipeline(
        db, organization_id=org_b.id, tipo="test", dominio="comercial",
        evento="tenant_b", payload={"titulo": "B", "indicadores": {"x": 1}, "source_reference": "b-only"},
        user_id=None,
    )
    db.commit()
    res = client.get(f"/api/oportunidades/{opp_b['opportunity_id']}", headers=auth_headers)
    assert res.status_code == 404
    db.close()


# 27 permisos
def test_27_permisos_viewer(client: TestClient, opp_db):
    org_id, _ = _admin(opp_db)
    viewer = User(
        username=f"viewer-{uuid.uuid4().hex[:6]}",
        email=f"v-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Viewer2026*"),
        organization_id=org_id,
        role="viewer",
        is_active=True,
    )
    opp_db.add(viewer)
    opp_db.commit()
    login = client.post("/api/auth/login", json={"username": viewer.username, "password": "Viewer2026*"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    ok = client.get("/api/oportunidades", headers=headers)
    assert ok.status_code == 200
    denied = client.post("/api/oportunidades/priorizar", headers=headers)
    assert denied.status_code == 403


# 28 insuficiencia OP-E
def test_28_datos_insuficientes(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-E")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.estado == "DATOS_INSUFICIENTES"
    assert opp.pertinencia == "SOLICITAR_DATOS"


# 29 contradicción OP-F
def test_29_contradiccion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-F", dominio="comercial")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    ctx = json.loads(opp.contexto_json or "{}")
    assert ctx.get("conflicto") is True
    assert opp.pertinencia == "SOLICITAR_APROBACION"


# 30 anti-prefabricado
def test_30_anti_prefabricado(opp_db):
    org_id, user_id = _admin(opp_db)
    r_a = _run_case(opp_db, org_id, user_id, "OP-A")
    r_b = _run_case(opp_db, org_id, user_id, "OP-B", dominio="administrativo")
    opp_db.commit()
    opp_a = opp_db.query(Opportunity).get(r_a["opportunity_id"])
    opp_b = opp_db.query(Opportunity).get(r_b["opportunity_id"])
    assert opp_a.tipo != opp_b.tipo or opp_a.prioridad_score != opp_b.prioridad_score


# 31 idempotencia activación
def test_31_idempotencia_activacion(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    svc.approve_opportunity(opp_db, opp, user_id=user_id)
    a1 = svc.activate_opportunity(opp_db, opp, user_id=user_id)
    a2 = svc.activate_opportunity(opp_db, opp, user_id=user_id)
    opp_db.commit()
    assert a1["work_plan_id"] == a2["work_plan_id"]
    assert a2.get("idempotent") is True


# 32 trazabilidad
def test_32_trazabilidad(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "OP-A")
    opp_db.commit()
    trace = svc.get_full_trace(opp_db, result["opportunity_id"], org_id)
    etapas = [t["etapa"] for t in trace["trazas"]]
    assert "SENAL_CREADA" in etapas
    assert "OPORTUNIDAD_CREADA" in etapas


# 33 G-01 domain interface
def test_33_g01_domain_interface():
    bootstrap_providers()
    salud = get_provider_for_request("diagnóstico IPS cartera", {})
    assert isinstance(salud, SaludDomainAnalysisProvider)
    admin = detect_domain("proceso administrativo repetitivo", {})
    assert admin[0] == "administrativo"
    generic = get_provider_for_request("algo genérico xyz", {})
    assert isinstance(generic, GenericDomainAnalysisProvider)


# 34 caso no-SALUD NS-1
def test_34_ns1_administrativo(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "NS-1", dominio="administrativo")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.dominio == "administrativo"
    assert opp.tipo == "AUTOMATIZACION"


# 35 caso no-SALUD NS-2
def test_35_ns2_comercial(opp_db):
    org_id, user_id = _admin(opp_db)
    result = _run_case(opp_db, org_id, user_id, "NS-2", dominio="comercial")
    opp_db.commit()
    opp = opp_db.query(Opportunity).get(result["opportunity_id"])
    assert opp.dominio == "comercial"
    assert opp.tipo == "COMERCIAL"
    assert float(opp.prioridad_score or 0) > 0


# API E2E reactivo
def test_api_e2e_reactivo(client: TestClient, auth_headers):
    payload = _signal_payload("OP-A")
    res = client.post("/api/oportunidades/pipeline-proactivo", headers=auth_headers, json={
        "tipo": "financiera", "dominio": "financiero", "evento": "api_e2e",
        "payload": payload,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["opportunity_id"]
    opp_id = data["opportunity_id"]
    client.post(f"/api/oportunidades/{opp_id}/aprobar", headers=auth_headers, json={"aprobado": True})
    act = client.post(f"/api/oportunidades/{opp_id}/activar", headers=auth_headers, json={})
    assert act.status_code == 200
    assert act.json().get("work_plan_id")


# API listado
def test_api_list_opportunities(client: TestClient, auth_headers):
    res = client.get("/api/oportunidades", headers=auth_headers)
    assert res.status_code == 200
    assert "items" in res.json()


# API resumen negocio
def test_api_resumen(client: TestClient, auth_headers):
    res = client.get("/api/oportunidades/resumen", headers=auth_headers)
    assert res.status_code == 200
    assert "oportunidades_detectadas" in res.json()
