"""Servicio — Motor Económico EIAAX (facade sobre FinOps, MB-07, valoración)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.economic_motor_enums import (
    AMOUNT_KINDS,
    COST_CLASSES,
    FINOPS_CATEGORY_TO_SOURCE,
    FINOPS_CERTAINTY_TO_NATURE,
    ECONOMIC_TO_FINOPS_VALUE_TYPE,
    CostSource,
    EconomicScope,
    EconomicValueType,
    PriceRecommendationStatus,
)
from app.economic_motor_models import (
    EconomicCostEntry,
    EconomicPriceRecommendation,
    EconomicPrivateEconomy,
    EconomicValueEntry,
)
from app.finops_enums import FinOpsValueCertainty
from app.models import User
from app.orchestration_models import AIEmployee, FinOpsRecord
from app.services import consumption_planner_service as planner_svc
from app.services import control_center_service as cc_svc
from app.services import finops_service as finops_svc
from app.valuation_enums import RealValueNature

POTENCIAL_NOTE = "POTENCIAL no se presenta como valor realizado ni entra en ROI realizado."


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _d(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, requested_org_id)


def _infer_scope(
    *,
    employee_id: str | None,
    opportunity_id: str | None,
    evaluacion_id: str | None,
    execution_ref: str | None = None,
) -> tuple[str, str | None]:
    if employee_id:
        return EconomicScope.EMPLEADO_IA, employee_id
    if evaluacion_id:
        return EconomicScope.EVALUACION, evaluacion_id
    if opportunity_id:
        return EconomicScope.OPORTUNIDAD, opportunity_id
    ref = (execution_ref or "").lower()
    if ref.startswith("transversal:"):
        return EconomicScope.AGENTE_TRANSVERSAL, ref.split(":", 1)[-1] or None
    return EconomicScope.ORGANIZACION, None


def _cost_entry_from_finops(record: FinOpsRecord) -> EconomicCostEntry:
    cost_class = planner_svc.classify_finops_record(record)
    cost_source = FINOPS_CATEGORY_TO_SOURCE.get(record.category or "", CostSource.OTRO)
    if record.tokens_in or record.tokens_out:
        cost_source = CostSource.TOKENS if cost_source == CostSource.OTRO else cost_source
    if record.provider or record.model_name:
        cost_source = CostSource.PROVEEDOR_MODELO if cost_source in (CostSource.OTRO, CostSource.CONSUMO_IA) else cost_source
    scope_type, scope_id = _infer_scope(
        employee_id=record.employee_id,
        opportunity_id=record.opportunity_id,
        evaluacion_id=None,
        execution_ref=record.execution_ref,
    )
    return EconomicCostEntry(
        organization_id=record.organization_id,
        cost_class=cost_class,
        amount_kind="REAL",
        cost_source=cost_source,
        scope_type=scope_type,
        scope_id=scope_id,
        employee_id=record.employee_id,
        work_plan_id=record.work_plan_id,
        opportunity_id=record.opportunity_id,
        finops_record_id=record.id,
        amount=float(record.cost or 0),
        currency=record.currency or "USD",
        provider=record.provider,
        model_name=record.model_name,
        tokens_in=record.tokens_in,
        tokens_out=record.tokens_out,
        description=f"FinOps:{record.category}",
    )


def sync_cost_from_finops_record(db: Session, record: FinOpsRecord) -> EconomicCostEntry:
    existing = (
        db.query(EconomicCostEntry)
        .filter(EconomicCostEntry.finops_record_id == record.id)
        .first()
    )
    if existing:
        return existing
    row = _cost_entry_from_finops(record)
    db.add(row)
    db.flush()
    return row


def register_cost(
    db: Session,
    user: User,
    *,
    organization_id: str,
    amount_kind: str,
    cost_source: str,
    amount: Decimal,
    currency: str = "USD",
    cost_class: str = "DIRECTO",
    scope_type: str = EconomicScope.ORGANIZACION,
    scope_id: str | None = None,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    opportunity_id: str | None = None,
    evaluacion_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    description: str | None = None,
    execution_ref: str | None = None,
    register_finops: bool = True,
) -> EconomicCostEntry:
    if amount_kind not in AMOUNT_KINDS:
        raise ValueError(f"amount_kind inválido: {amount_kind}")
    if cost_class not in COST_CLASSES:
        raise ValueError(f"cost_class inválido: {cost_class}")
    if cost_source not in CostSource.ALL:
        raise ValueError(f"cost_source inválido: {cost_source}")

    finops_record_id = None
    if amount_kind == "REAL" and register_finops:
        category = "Modelo IA" if cost_source in (CostSource.CONSUMO_IA, CostSource.TOKENS, CostSource.PROVEEDOR_MODELO) else "Otro"
        record = finops_svc.registrar_consumo(
            db,
            organization_id=organization_id,
            user_id=user.id,
            employee_id=employee_id,
            work_plan_id=work_plan_id,
            opportunity_id=opportunity_id,
            execution_ref=execution_ref,
            provider=provider,
            model_name=model_name,
            category=category,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            currency=currency,
            cost=amount,
        )
        finops_record_id = record.id
        cost_class = planner_svc.classify_finops_record(record)

    row = EconomicCostEntry(
        organization_id=organization_id,
        cost_class=cost_class,
        amount_kind=amount_kind,
        cost_source=cost_source,
        scope_type=scope_type,
        scope_id=scope_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        opportunity_id=opportunity_id,
        evaluacion_id=evaluacion_id,
        finops_record_id=finops_record_id,
        amount=float(amount),
        currency=currency,
        provider=provider,
        model_name=model_name,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        description=description,
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="economic_motor.cost.registered",
        organization_id=organization_id,
        user_id=user.id,
        detail=f"{amount_kind}:{cost_source}:{row.id}",
        commit=False,
    )
    return row


def _map_value_nature(nature: str) -> str:
    key = (nature or "ESTIMADO").upper()
    if key not in (RealValueNature.VERIFICADO, RealValueNature.ESTIMADO, RealValueNature.POTENCIAL):
        return RealValueNature.ESTIMADO
    return key


def _finops_certainty_from_nature(nature: str) -> str:
    if nature == RealValueNature.VERIFICADO:
        return FinOpsValueCertainty.REAL
    return FinOpsValueCertainty.ESTIMADO


def register_value(
    db: Session,
    user: User,
    *,
    organization_id: str,
    value_type: str,
    value_nature: str,
    amount: Decimal,
    currency: str = "USD",
    scope_type: str = EconomicScope.ORGANIZACION,
    scope_id: str | None = None,
    employee_id: str | None = None,
    opportunity_id: str | None = None,
    evaluacion_id: str | None = None,
    methodology: str | None = None,
    notes: str | None = None,
    register_finops: bool = True,
) -> EconomicValueEntry:
    nature = _map_value_nature(value_nature)
    if value_type not in EconomicValueType.ALL:
        raise ValueError(f"value_type inválido: {value_type}")

    finops_value_id = None
    if register_finops and nature != RealValueNature.POTENCIAL:
        finops_row = finops_svc.registrar_valor(
            db,
            organization_id=organization_id,
            user_id=user.id,
            employee_id=employee_id,
            opportunity_id=opportunity_id,
            value_type=ECONOMIC_TO_FINOPS_VALUE_TYPE.get(value_type, value_type),
            certainty=_finops_certainty_from_nature(nature),
            amount=amount,
            currency=currency,
            methodology=methodology,
            source="motor_economico",
            notes=notes,
        )
        finops_value_id = finops_row.id

    row = EconomicValueEntry(
        organization_id=organization_id,
        value_type=value_type,
        value_nature=nature,
        scope_type=scope_type,
        scope_id=scope_id,
        employee_id=employee_id,
        opportunity_id=opportunity_id,
        evaluacion_id=evaluacion_id,
        finops_value_id=finops_value_id,
        amount=float(amount),
        currency=currency,
        methodology=methodology,
        notes=notes,
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="economic_motor.value.registered",
        organization_id=organization_id,
        user_id=user.id,
        detail=f"{nature}:{value_type}:{row.id}",
        commit=False,
    )
    return row


def sum_values_by_nature(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict[str, Any]:
    q = db.query(EconomicValueEntry.value_nature, func.sum(EconomicValueEntry.amount)).filter(
        EconomicValueEntry.organization_id == organization_id
    )
    if period_start:
        q = q.filter(EconomicValueEntry.created_at >= period_start)
    if period_end:
        q = q.filter(EconomicValueEntry.created_at <= period_end)
    rows = q.group_by(EconomicValueEntry.value_nature).all()
    buckets = {RealValueNature.VERIFICADO: 0.0, RealValueNature.ESTIMADO: 0.0, RealValueNature.POTENCIAL: 0.0}
    for nature, total in rows:
        key = (nature or RealValueNature.ESTIMADO).upper()
        if key in buckets:
            buckets[key] += float(total or 0)
    realizado = buckets[RealValueNature.VERIFICADO] + buckets[RealValueNature.ESTIMADO]
    return {
        "valor_verificado": buckets[RealValueNature.VERIFICADO] or None,
        "valor_estimado": buckets[RealValueNature.ESTIMADO] or None,
        "valor_potencial": buckets[RealValueNature.POTENCIAL] or None,
        "valor_realizado": realizado or None,
        "nota_potencial": POTENCIAL_NOTE,
    }


def sum_costs_by_class_and_kind(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict[str, Any]:
    q = db.query(
        EconomicCostEntry.cost_class,
        EconomicCostEntry.amount_kind,
        func.sum(EconomicCostEntry.amount),
    ).filter(EconomicCostEntry.organization_id == organization_id)
    if period_start:
        q = q.filter(EconomicCostEntry.created_at >= period_start)
    if period_end:
        q = q.filter(EconomicCostEntry.created_at <= period_end)
    rows = q.group_by(EconomicCostEntry.cost_class, EconomicCostEntry.amount_kind).all()
    result: dict[str, dict[str, float]] = {
        cls: {"ESTIMADO": 0.0, "REAL": 0.0, "PROYECTADO": 0.0} for cls in COST_CLASSES
    }
    for cls, kind, total in rows:
        if cls in result and kind in result[cls]:
            result[cls][kind] += float(total or 0)
    return {"by_class": result}


def build_indicators(
    db: Session,
    organization_id: str,
    *,
    period_days: int = 30,
) -> dict[str, Any]:
    """Indicadores ANTES / PROYECTADO / REAL para Centro de Control."""
    period_end = _utcnow()
    period_start = period_end - timedelta(days=period_days)

    # REAL — FinOps + motor + planner
    real_planner = planner_svc.aggregate_real_consumption(db, organization_id, period_start=period_start, period_end=period_end)
    real_motor = sum_costs_by_class_and_kind(db, organization_id, period_start=period_start, period_end=period_end)
    real_values = sum_values_by_nature(db, organization_id, period_start=period_start, period_end=period_end)
    real_total = sum(v.get("cost_total", 0) for v in real_planner.get("by_class", {}).values())

    # PROYECTADO — simulación MB-07 (sin persistir)
    config = planner_svc.get_or_create_org_config(db, organization_id)
    active_employees = (
        db.query(AIEmployee).filter(AIEmployee.organization_id == organization_id, AIEmployee.is_active.is_(True)).count()
        or 1
    )
    sim = planner_svc.simulate(
        db,
        organization_id,
        {
            "active_employees": active_employees,
            "days": period_days,
            "platform_cost_monthly": 0,
        },
    )

    # ANTES — línea base / estimados históricos del motor
    antes_estimated = (
        db.query(func.sum(EconomicCostEntry.amount))
        .filter(
            EconomicCostEntry.organization_id == organization_id,
            EconomicCostEntry.amount_kind == "ESTIMADO",
            EconomicCostEntry.created_at < period_start,
        )
        .scalar()
    )

    return {
        "organization_id": organization_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "fases": {
            "ANTES": {
                "costo_estimado_historico": float(antes_estimated or 0) or None,
                "nota": "Baseline histórico motor + línea base cuando disponible",
            },
            "PROYECTADO": {
                "costo_total": sim.get("cost_total"),
                "consumo_ia": sim.get("directo", {}).get("cost_total"),
                "transversal": sim.get("transversal", {}).get("cost_total"),
                "plataforma": sim.get("plataforma_cost_monthly"),
                "desviacion_vs_presupuesto": sim.get("budget", {}).get("utilization_pct"),
            },
            "REAL": {
                "costos_por_clase": real_planner.get("by_class"),
                "costos_motor": real_motor,
                "valores": real_values,
            },
        },
        "presupuesto_ia": {
            "included_consumption_usd": float(config.included_consumption_usd or 0) if config.included_consumption_usd else None,
            "consumo_real_periodo": real_total,
            "alert_thresholds": planner_svc.org_config_to_dict(config).get("alert_thresholds"),
        },
        "nota_potencial": POTENCIAL_NOTE,
    }


def entity_view_summary(db: Session, organization_id: str, *, period_days: int = 30) -> dict[str, Any]:
    """Vista Entidad — sin economía privada ni márgenes."""
    period_end = _utcnow()
    period_start = period_end - timedelta(days=period_days)
    costs = sum_costs_by_class_and_kind(db, organization_id, period_start=period_start, period_end=period_end)
    values = sum_values_by_nature(db, organization_id, period_start=period_start, period_end=period_end)
    dashboard = finops_svc.dashboard_summary(db, organization_id, period_start=period_start, period_end=period_end)
    return {
        "organization_id": organization_id,
        "vista": "ENTIDAD",
        "costos": costs,
        "valores": values,
        "roi_finops": dashboard.get("roi"),
        "costo_total_finops": dashboard.get("total_cost"),
        "valor_realizado_finops": dashboard.get("total_value"),
        "nota_potencial": POTENCIAL_NOTE,
        "economia_privada_incluida": False,
    }


def get_private_economy(db: Session, organization_id: str) -> EconomicPrivateEconomy | None:
    return (
        db.query(EconomicPrivateEconomy)
        .filter(EconomicPrivateEconomy.organization_id == organization_id)
        .order_by(EconomicPrivateEconomy.updated_at.desc())
        .first()
    )


def save_private_economy(db: Session, user: User, organization_id: str, data: dict[str, Any]) -> EconomicPrivateEconomy:
    row = get_private_economy(db, organization_id)
    if not row:
        row = EconomicPrivateEconomy(organization_id=organization_id, created_by_id=user.id)
        db.add(row)
    for field in (
        "period_label",
        "estimated_cost",
        "real_cost",
        "time_hours",
        "resources_cost",
        "ia_cost",
        "infra_cost",
        "services_cost",
        "support_cost",
        "client_value",
        "suggested_price",
        "margin",
        "roi",
        "payback_months",
        "commercial_risk_score",
        "notes",
    ):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    row.updated_at = _utcnow()
    db.flush()
    write_audit(
        db,
        action="economic_motor.private_economy.saved",
        organization_id=organization_id,
        user_id=user.id,
        detail=f"private:{row.id}",
        commit=False,
    )
    return row


def private_economy_to_dict(row: EconomicPrivateEconomy | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "period_label": row.period_label,
        "estimated_cost": float(row.estimated_cost) if row.estimated_cost is not None else None,
        "real_cost": float(row.real_cost) if row.real_cost is not None else None,
        "time_hours": float(row.time_hours) if row.time_hours is not None else None,
        "resources_cost": float(row.resources_cost) if row.resources_cost is not None else None,
        "ia_cost": float(row.ia_cost) if row.ia_cost is not None else None,
        "infra_cost": float(row.infra_cost) if row.infra_cost is not None else None,
        "services_cost": float(row.services_cost) if row.services_cost is not None else None,
        "support_cost": float(row.support_cost) if row.support_cost is not None else None,
        "client_value": float(row.client_value) if row.client_value is not None else None,
        "suggested_price": float(row.suggested_price) if row.suggested_price is not None else None,
        "margin": float(row.margin) if row.margin is not None else None,
        "roi": float(row.roi) if row.roi is not None else None,
        "payback_months": float(row.payback_months) if row.payback_months is not None else None,
        "commercial_risk_score": float(row.commercial_risk_score) if row.commercial_risk_score is not None else None,
        "notes": row.notes,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def recommend_price(
    db: Session,
    user: User,
    organization_id: str,
    *,
    scope_type: str = EconomicScope.ORGANIZACION,
    scope_id: str | None = None,
    attributable_value: Decimal | None = None,
    complexity: float = 0.5,
    risk: float = 0.3,
    urgency: float = 0.3,
    reuse_factor: float = 0.5,
    personalization: float = 0.5,
    support_level: float = 0.3,
    consumption_cost: Decimal | None = None,
    infra_cost: Decimal | None = None,
    currency: str = "USD",
    persist: bool = True,
) -> dict[str, Any]:
    """Motor de precio recomendado — siempre BORRADOR, sin publicación automática."""
    base_value = _d(attributable_value)
    if base_value <= 0:
        values = sum_values_by_nature(db, organization_id)
        base_value = _d(values.get("valor_realizado") or 0)
    cons = _d(consumption_cost)
    infra = _d(infra_cost)
    if cons <= 0 or infra <= 0:
        real = planner_svc.aggregate_real_consumption(db, organization_id)
        by_class = real.get("by_class", {})
        if cons <= 0:
            cons = _d(sum(v.get("cost_total", 0) for v in by_class.values()))
        if infra <= 0:
            infra = _d(by_class.get("PLATAFORMA", {}).get("cost_total", 0))

    complexity_w = Decimal(str(max(0.0, min(1.0, complexity))))
    risk_w = Decimal(str(max(0.0, min(1.0, risk))))
    urgency_w = Decimal(str(max(0.0, min(1.0, urgency))))
    reuse_w = Decimal("1") - Decimal(str(max(0.0, min(1.0, reuse_factor))))
    pers_w = Decimal(str(max(0.0, min(1.0, personalization))))
    support_w = Decimal(str(max(0.0, min(1.0, support_level))))

    cost_base = cons + infra
    multiplier = Decimal("1") + complexity_w * Decimal("0.35") + risk_w * Decimal("0.25") + urgency_w * Decimal("0.15")
    multiplier += reuse_w * Decimal("0.20") + pers_w * Decimal("0.25") + support_w * Decimal("0.10")
    value_component = base_value * Decimal("0.4")
    price = (cost_base * multiplier) + value_component
    margin_est = price - cost_base

    factors = {
        "attributable_value": float(base_value),
        "complexity": float(complexity_w),
        "risk": float(risk_w),
        "urgency": float(urgency_w),
        "reuse_factor": float(reuse_w),
        "personalization": float(pers_w),
        "support_level": float(support_w),
        "consumption_cost": float(cons),
        "infra_cost": float(infra),
        "multiplier": float(multiplier),
    }
    rationale = (
        "Precio recomendado = (costo consumo + infra) × factor ajuste + 40% valor atribuible. "
        "BORRADOR — requiere revisión humana antes de publicar."
    )
    result = {
        "recommended_price": float(price.quantize(Decimal("0.01"))),
        "currency": currency,
        "margin_estimate": float(margin_est.quantize(Decimal("0.01"))),
        "status": PriceRecommendationStatus.BORRADOR,
        "factors": factors,
        "rationale": rationale,
        "auto_published": False,
    }
    if persist:
        row = EconomicPriceRecommendation(
            organization_id=organization_id,
            scope_type=scope_type,
            scope_id=scope_id,
            status=PriceRecommendationStatus.BORRADOR,
            recommended_price=float(price),
            currency=currency,
            margin_estimate=float(margin_est),
            factors_json=_json_dumps(factors),
            rationale_text=rationale,
            created_by_id=user.id,
        )
        db.add(row)
        db.flush()
        result["id"] = row.id
    return result


def backfill_costs_from_finops(db: Session, organization_id: str, *, limit: int = 500) -> int:
    """Sincroniza registros FinOps existentes al motor (idempotente)."""
    records = (
        db.query(FinOpsRecord)
        .filter(FinOpsRecord.organization_id == organization_id)
        .order_by(FinOpsRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    created = 0
    for record in records:
        before = (
            db.query(EconomicCostEntry)
            .filter(EconomicCostEntry.finops_record_id == record.id)
            .count()
        )
        if not before:
            sync_cost_from_finops_record(db, record)
            created += 1
    return created
