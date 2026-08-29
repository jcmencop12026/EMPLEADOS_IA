"""Seed idempotente — DEMO EMPLEADOS IA."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.demo_integral.constants import (
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_USERNAME,
    DEMO_ANALYST_PASSWORD,
    DEMO_ANALYST_USERNAME,
    DEMO_BASELINE_INDICATOR,
    DEMO_CORRELATION_ID,
    DEMO_EXT_SOURCE_CODE,
    DEMO_FINOPS_EXEC_REF,
    DEMO_OPP_CODE,
    DEMO_OPP_SECONDARY_CODE,
    DEMO_ORG_NAME,
    DEMO_ORG_SLUG,
    DEMO_RECOMMENDATION_MARKER,
    DEMO_SIGNAL_REF,
    DEMO_SOURCE_CODE,
    DEMO_VIEWER_PASSWORD,
    DEMO_VIEWER_USERNAME,
)
from app.demo_integral.manifest import get_compatibility_manifest
from app.models import Organization, User
from app.opportunity_models import Opportunity
from app.optimization_models import OptimizacionRecomendacion
from app.security import hash_password
from app.seed_llm import bootstrap_llm
from app.seed_orchestration import bootstrap_orchestration
from app.seed_permissions import bootstrap_permissions
from app.seed_salud import bootstrap_salud
from app.services import baseline_service as baseline_svc
from app.services import external_intelligence_service as ext_svc
from app.services import finops_service as finops_svc
from app.services import learning_service as learning_svc
from app.services import optimization_service as opt_svc
from app.services import proactive_service as proactive_svc
from app.services import valuation_service as valuation_svc
from app.valuation_enums import AttributionLevel, RealValueNature, ValueScope, ValueType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_or_create_org(db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()
    if org:
        if org.name != DEMO_ORG_NAME:
            raise ValueError(f"ABORT: slug {DEMO_ORG_SLUG} pertenece a otra organización ({org.name})")
        return org
    org = Organization(name=DEMO_ORG_NAME, slug=DEMO_ORG_SLUG, status="ACTIVE")
    db.add(org)
    db.flush()
    return org


def _ensure_users(db: Session, org_id: str) -> dict[str, User]:
    specs = [
        (DEMO_ADMIN_USERNAME, DEMO_ADMIN_PASSWORD, "admin"),
        (DEMO_VIEWER_USERNAME, DEMO_VIEWER_PASSWORD, "viewer"),
        (DEMO_ANALYST_USERNAME, DEMO_ANALYST_PASSWORD, "analyst"),
    ]
    users: dict[str, User] = {}
    for username, password, role in specs:
        user = db.query(User).filter(User.username == username).first()
        if user:
            if user.organization_id != org_id:
                raise ValueError(f"ABORT: usuario demo {username} pertenece a otra organización")
            users[role] = user
            continue
        user = User(
            organization_id=org_id,
            username=username,
            password_hash=hash_password(password),
            full_name=username.replace(".", " ").title(),
            role=role,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        db.flush()
        users[role] = user
    return users


def _ensure_bootstrap(db: Session, org_id: str) -> None:
    bootstrap_permissions(db)
    bootstrap_orchestration(db, org_id)
    bootstrap_salud(db, org_id)
    bootstrap_llm(db, org_id)


def _find_opp_by_code(db: Session, org_id: str, codigo: str) -> Opportunity | None:
    return (
        db.query(Opportunity)
        .filter(Opportunity.organization_id == org_id, Opportunity.codigo == codigo)
        .first()
    )


def _ensure_signal_and_opportunity(db: Session, org_id: str, admin: User) -> Opportunity:
    existing = _find_opp_by_code(db, org_id, DEMO_OPP_CODE)
    if existing:
        return existing

    result = proactive_svc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        user_id=admin.id,
        tipo="financiera",
        dominio="financiero",
        evento="cartera_vencida_alerta",
        payload={
            "titulo": "Reducir cartera vencida en proceso de cobranza",
            "tipo_oportunidad": "FINANCIERA",
            "indicadores": {"cartera_vencida": 28_500_000, "dso": 45},
            "impacto_estimado": 8_500_000,
            "valor_potencial": 6_200_000,
            "costo_estimado": 1_800_000,
            "urgencia": "ALTA",
            "confianza": 0.85,
            "source_reference": DEMO_SIGNAL_REF,
            "correlation_id": DEMO_CORRELATION_ID,
        },
        origen="demo_integral_seed",
    )
    opp_id = result.get("opportunity_id")
    if not opp_id:
        raise RuntimeError("El pipeline demo no generó oportunidad")
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise RuntimeError("Oportunidad demo no encontrada tras pipeline")
    opp.codigo = DEMO_OPP_CODE
    opp.correlation_id = DEMO_CORRELATION_ID
    db.flush()
    return opp


def _ensure_secondary_opportunity(db: Session, org_id: str, admin: User) -> Opportunity:
    existing = _find_opp_by_code(db, org_id, DEMO_OPP_SECONDARY_CODE)
    if existing:
        return existing
    result = proactive_svc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        user_id=admin.id,
        tipo="operativa",
        dominio="operaciones",
        evento="demo_proceso_manual",
        payload={
            "titulo": "Automatizar conciliación de facturas demo",
            "tipo_oportunidad": "OPERATIVA",
            "indicadores": {"horas_mes": 120},
            "impacto_estimado": 3_200_000,
            "valor_potencial": 2_400_000,
            "costo_estimado": 900_000,
            "urgencia": "MEDIA",
            "source_reference": f"{DEMO_SIGNAL_REF}-sec",
            "correlation_id": DEMO_CORRELATION_ID,
        },
        origen="demo_integral_seed",
    )
    opp = db.query(Opportunity).filter(Opportunity.id == result["opportunity_id"]).first()
    opp.codigo = DEMO_OPP_SECONDARY_CODE
    db.flush()
    return opp


def _ensure_opportunity_lifecycle(db: Session, opp: Opportunity, admin: User) -> None:
    db.refresh(opp)
    if opp.resultado_json:
        return

    for _ in range(12):
        db.refresh(opp)
        estado = opp.estado
        if estado in ("EN_SEGUIMIENTO", "MATERIALIZADA", "CERRADA"):
            break
        if estado == "DATOS_INSUFICIENTES":
            proactive_svc.transition_state(
                db, opp, "EN_EVALUACION", actor_id=admin.id, motivo="Demo: datos enriquecidos"
            )
        elif estado == "EN_EVALUACION":
            proactive_svc.transition_state(db, opp, "PRIORIZADA", actor_id=admin.id, motivo="Demo: priorizada")
        elif estado in ("PRIORIZADA", "PROPUESTA", "PENDIENTE_APROBACION"):
            proactive_svc.approve_opportunity(
                db, opp, user_id=admin.id, aprobado=True, motivo="Aprobación demo integral"
            )
        elif estado == "APROBADA":
            proactive_svc.activate_opportunity(db, opp, user_id=admin.id, auto_execute=False)
        elif estado == "EN_EJECUCION":
            proactive_svc.transition_state(
                db, opp, "EN_SEGUIMIENTO", actor_id=admin.id, motivo="Demo: seguimiento activo"
            )
        else:
            break

    db.refresh(opp)
    if opp.estado in ("EN_SEGUIMIENTO", "MATERIALIZADA") and not opp.resultado_json:
        proactive_svc.register_result(
            db,
            opp,
            user_id=admin.id,
            valor_real=4_200_000.0,
            valor_esperado=6_200_000.0,
            evidencia={"correlation_id": DEMO_CORRELATION_ID, "demo": True},
            estado_resultado="PARCIAL",
        )


def _ensure_baseline(db: Session, org_id: str, admin: User, opp: Opportunity) -> str | None:
    from app.baseline_models import LineaBase

    existing = (
        db.query(LineaBase)
        .filter(
            LineaBase.organization_id == org_id,
            LineaBase.indicador == DEMO_BASELINE_INDICATOR,
        )
        .first()
    )
    if existing:
        return existing.id
    lb = baseline_svc.create_linea_base(
        db,
        organization_id=org_id,
        user_id=admin.id,
        indicador=DEMO_BASELINE_INDICATOR,
        valor_base=45.0,
        fecha_inicio_base=_utcnow() - timedelta(days=90),
        fecha_fin_base=_utcnow() - timedelta(days=1),
        unidad="días",
        descripcion="DSO cartera demo ficticia",
        opportunity_id=opp.id,
        evidencia={"correlation_id": DEMO_CORRELATION_ID, "fuente": "demo"},
    )
    med, impacto = baseline_svc.register_medicion(
        db,
        lb,
        user_id=admin.id,
        valor_posterior=38.0,
        periodo_inicio=_utcnow() - timedelta(days=30),
        periodo_fin=_utcnow(),
        evidencia={"correlation_id": DEMO_CORRELATION_ID},
    )
    baseline_svc.validate_medicion(db, lb, med, impacto, user_id=admin.id)
    return lb.id


def _ensure_valuation(db: Session, org_id: str, admin: User, opp: Opportunity) -> None:
    try:
        valuation_svc.create_valuation(
            db,
            organization_id=org_id,
            opportunity_id=opp.id,
            user_id=admin.id,
            value_type=ValueType.AHORRO,
            scope=ValueScope.INTERNO,
            currency="COP",
        )
    except valuation_svc.ValuationValidationError:
        pass
    valuation_svc.update_expected(
        db,
        organization_id=org_id,
        opportunity_id=opp.id,
        user_id=admin.id,
        gross_value=Decimal("6200000"),
        value_nature="ESTIMADA",
        evidence=f"Valor esperado demo — {DEMO_CORRELATION_ID}",
    )
    valuation_svc.register_real_value(
        db,
        organization_id=org_id,
        opportunity_id=opp.id,
        user_id=admin.id,
        materialized_value=Decimal("4200000"),
        attributable_value=Decimal("3800000"),
        value_nature=RealValueNature.VERIFICADO,
        attribution_level=AttributionLevel.ATRIBUIBLE,
        source="medicion_demo",
        evidence=f"Evidencia ficticia demo — {DEMO_CORRELATION_ID}",
    )
    valuation_svc.register_real_value(
        db,
        organization_id=org_id,
        opportunity_id=opp.id,
        user_id=admin.id,
        materialized_value=Decimal("2500000"),
        attributable_value=None,
        value_nature=RealValueNature.ESTIMADO,
        attribution_level=AttributionLevel.PARCIALMENTE_ATRIBUIBLE,
        attribution_pct=Decimal("60"),
        source="proyeccion_demo",
        evidence="Proyección sustentada — no es hecho verificado",
    )
    valuation_svc.register_real_value(
        db,
        organization_id=org_id,
        opportunity_id=opp.id,
        user_id=admin.id,
        materialized_value=Decimal("6200000"),
        attributable_value=None,
        value_nature=RealValueNature.POTENCIAL,
        attribution_level=AttributionLevel.NO_ATRIBUIBLE,
        source="oportunidad_residual",
        evidence="Potencial no materializado — excluido de precio sugerido",
    )


def _ensure_finops(db: Session, org_id: str, admin: User, opp: Opportunity) -> None:
    from app.finops_models import FinOpsBudget
    from app.orchestration_models import FinOpsRecord

    if (
        db.query(FinOpsRecord)
        .filter(
            FinOpsRecord.organization_id == org_id,
            FinOpsRecord.execution_ref == DEMO_FINOPS_EXEC_REF,
        )
        .first()
    ):
        return
    finops_svc.registrar_consumo(
        db,
        organization_id=org_id,
        user_id=admin.id,
        opportunity_id=opp.id,
        provider="openai",
        model_name="gpt-4o-mini",
        category="Modelo IA",
        tokens_in=12_500,
        tokens_out=3_200,
        execution_ref=DEMO_FINOPS_EXEC_REF,
        cost=Decimal("1850.50"),
        currency="COP",
        skip_budget_enforcement=True,
    )
    if not db.query(FinOpsBudget).filter(
        FinOpsBudget.organization_id == org_id,
        FinOpsBudget.name == "Presupuesto IA demo",
    ).first():
        now = _utcnow()
        db.add(
            FinOpsBudget(
                organization_id=org_id,
                scope_type="empresa",
                scope_id=None,
                period_start=now - timedelta(days=30),
                period_end=now + timedelta(days=335),
                amount_limit=Decimal("500000"),
                currency="COP",
                policy="Solo informar",
                name="Presupuesto IA demo",
            )
        )
        db.flush()


def _ensure_learning(db: Session, admin: User, opp: Opportunity) -> str | None:
    ciclos = learning_svc.listar_ciclos(db, admin.organization_id, opportunity_id=opp.id)
    if ciclos:
        ciclo = ciclos[0]
        if ciclo.estado == "ABIERTO":
            learning_svc.evaluar_ciclo(
                db,
                admin,
                ciclo.id,
                valor_real=4_200_000,
                impacto_real=5_100_000,
                tipo_explicacion="PROBABLE",
                notas="Aprendizaje demo — inferencia, no hecho",
            )
        return ciclo.id
    ciclo = learning_svc.crear_ciclo_aprendizaje(
        db,
        admin,
        opportunity_id=opp.id,
        valor_real=4_200_000,
        impacto_real=5_100_000,
    )
    learning_svc.evaluar_ciclo(
        db,
        admin,
        ciclo.id,
        valor_real=4_200_000,
        impacto_real=5_100_000,
        tipo_explicacion="PROBABLE",
        notas="Aprendizaje demo",
    )
    return ciclo.id


def _ensure_recommendation(db: Session, admin: User, opp_ids: list[str]) -> str | None:
    recs = (
        db.query(OptimizacionRecomendacion)
        .filter(
            OptimizacionRecomendacion.organization_id == admin.organization_id,
            OptimizacionRecomendacion.es_simulacion.is_(False),
        )
        .all()
    )
    for rec in recs:
        expl = opt_svc._json_load(rec.explicacion_json) or {}
        if expl.get("demo_marker") == DEMO_RECOMMENDATION_MARKER:
            return rec.id
    rec = opt_svc.crear_recomendacion(
        db,
        admin,
        objetivo="MAXIMIZAR_VALOR",
        restricciones={"presupuesto_maximo": 15_000_000, "max_iniciativas": 2},
        opportunity_ids=opp_ids,
    )
    expl = opt_svc._json_load(rec.explicacion_json) or {}
    expl["demo_marker"] = DEMO_RECOMMENDATION_MARKER
    expl["correlation_id"] = DEMO_CORRELATION_ID
    rec.explicacion_json = json.dumps(expl, ensure_ascii=False)
    db.flush()
    if rec.estado == "PROPUESTA":
        opt_svc.aprobar_recomendacion(db, admin, rec.id, "Aprobación demo integral Fase 2")
    return rec.id


def _ensure_external_signal(db: Session, org_id: str, admin: User) -> None:
    if ext_svc.get_external_source_by_code(db, org_id, DEMO_EXT_SOURCE_CODE):
        return
    ext_svc.create_external_source(
        db,
        organization_id=org_id,
        user_id=admin.id,
        code=DEMO_EXT_SOURCE_CODE,
        name="Mercado demo ficticio",
        source_type="MERCADO",
        ingestion_channel="CARGA MANUAL",
        sector="servicios",
        pais_region="Colombia",
        confiabilidad=0.75,
    )
    ext_svc.ingest_external_signal(
        db,
        organization_id=org_id,
        user_id=admin.id,
        data={
            "source_code": DEMO_EXT_SOURCE_CODE,
            "hecho_observado": "Competidor reduce plazos de cobro en sector servicios (dato ficticio)",
            "evento": "presion_mercado_cobranza",
            "dominio": "financiero",
            "classification": "CONTEXTO",
            "interpretacion": "Inferencia de mercado — no es hecho interno verificado",
            "referencia": f"{DEMO_SIGNAL_REF}-ext",
            "correlation_id": DEMO_CORRELATION_ID,
        },
        auto_process=False,
    )


def _ensure_diagnostic(db: Session, org_id: str, admin: User) -> str | None:
    from fastapi import HTTPException
    from app.services import diagnostic_service as diag_svc

    diags = diag_svc.list_diagnostics(db, org_id, limit=5)
    for d in diags:
        if DEMO_CORRELATION_ID in (d.resumen or ""):
            return d.id
    end = _utcnow()
    start = end - timedelta(days=30)
    try:
        diag = diag_svc.generate_diagnostic(
            db,
            organization_id=org_id,
            user_id=admin.id,
            periodo_inicio=start,
            periodo_fin=end,
            dominios=["financiero"],
        )
    except HTTPException:
        return None
    if diag.resumen:
        diag.resumen = f"{diag.resumen} [{DEMO_CORRELATION_ID}]"
    else:
        diag.resumen = f"Diagnóstico demo integral [{DEMO_CORRELATION_ID}]"
    db.flush()
    return diag.id


def seed_demo_integral(db: Session) -> dict[str, Any]:
    """Carga idempotente de la demo DEMO EMPLEADOS IA."""
    org = _get_or_create_org(db)
    _ensure_bootstrap(db, org.id)
    users = _ensure_users(db, org.id)
    admin = users["admin"]

    opp = _ensure_signal_and_opportunity(db, org.id, admin)
    opp2 = _ensure_secondary_opportunity(db, org.id, admin)
    _ensure_opportunity_lifecycle(db, opp, admin)
    _ensure_external_signal(db, org.id, admin)
    diag_id = _ensure_diagnostic(db, org.id, admin)
    lb_id = _ensure_baseline(db, org.id, admin, opp)
    _ensure_valuation(db, org.id, admin, opp)
    _ensure_finops(db, org.id, admin, opp)
    ciclo_id = _ensure_learning(db, admin, opp)
    rec_id = _ensure_recommendation(db, admin, [opp.id, opp2.id])

    db.commit()

    manifest = get_compatibility_manifest()
    return {
        "status": "ok",
        "organization_id": org.id,
        "organization_slug": org.slug,
        "organization_name": org.name,
        "correlation_id": DEMO_CORRELATION_ID,
        "users": {
            "admin": DEMO_ADMIN_USERNAME,
            "viewer": DEMO_VIEWER_USERNAME,
            "analyst": DEMO_ANALYST_USERNAME,
        },
        "entities": {
            "primary_opportunity_id": opp.id,
            "primary_opportunity_code": DEMO_OPP_CODE,
            "secondary_opportunity_id": opp2.id,
            "diagnostic_id": diag_id,
            "baseline_id": lb_id,
            "learning_cycle_id": ciclo_id,
            "recommendation_id": rec_id,
        },
        "compatibility_manifest": manifest,
        "login": {
            "username": DEMO_ADMIN_USERNAME,
            "password": DEMO_ADMIN_PASSWORD,
        },
    }
