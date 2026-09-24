"""Servicio — Valoración económica y ROI por oportunidad (1210)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.opportunity_models import Opportunity
from app.services import finops_service as finops
from app.valuation_enums import (
    AttributionLevel,
    ExecutionCostType,
    RealValueNature,
    ScenarioType,
    ValuationHistoryAction,
    ValuationStatus,
    ValueDiscipline,
    ValueScope,
    ValueType,
)
from app.valuation_models import (
    OpportunityExecutionCost,
    OpportunityValuation,
    OpportunityValuationExpected,
    OpportunityValuationHistory,
    OpportunityValuationReal,
    OpportunityValuationScenario,
)

NO_CALCULABLE = "NO CALCULABLE"


class ValuationValidationError(ValueError):
    """Datos inválidos o referencias cruzadas en valoración."""


def _decimal(value: float | Decimal | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_adjusted_expected(gross: Decimal | None, probability: Decimal | None) -> Decimal | None:
    """Cálculo determinístico: valor bruto × probabilidad."""
    if gross is None or probability is None:
        return None
    return (gross * probability).quantize(Decimal("0.0001"))


def _validate_opportunity(db: Session, organization_id: str, opportunity_id: str) -> Opportunity:
    opp = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id)
        .first()
    )
    if not opp:
        raise ValuationValidationError("Oportunidad no encontrada en la organización.")
    return opp


def _get_valuation(
    db: Session, organization_id: str, opportunity_id: str, *, required: bool = True
) -> OpportunityValuation | None:
    row = (
        db.query(OpportunityValuation)
        .filter(
            OpportunityValuation.organization_id == organization_id,
            OpportunityValuation.opportunity_id == opportunity_id,
        )
        .first()
    )
    if required and not row:
        raise ValuationValidationError("Valoración no encontrada para esta oportunidad.")
    return row


def _snapshot_valuation(db: Session, valuation: OpportunityValuation) -> dict[str, Any]:
    expected = (
        db.query(OpportunityValuationExpected)
        .filter(OpportunityValuationExpected.valuation_id == valuation.id)
        .first()
    )
    scenarios = (
        db.query(OpportunityValuationScenario)
        .filter(OpportunityValuationScenario.valuation_id == valuation.id)
        .all()
    )
    real = (
        db.query(OpportunityValuationReal)
        .filter(
            OpportunityValuationReal.valuation_id == valuation.id,
            OpportunityValuationReal.is_current.is_(True),
        )
        .first()
    )
    costs = (
        db.query(OpportunityExecutionCost)
        .filter(OpportunityExecutionCost.valuation_id == valuation.id)
        .all()
    )
    return {
        "valuation": {
            "id": valuation.id,
            "value_type": valuation.value_type,
            "scope": valuation.scope,
            "currency": valuation.currency,
            "status": valuation.status,
            "version": valuation.version,
        },
        "expected": _serialize_expected(expected) if expected else None,
        "scenarios": [_serialize_scenario(s) for s in scenarios],
        "real": _serialize_real(real) if real else None,
        "execution_costs": [_serialize_cost(c) for c in costs],
    }


def _append_history(
    db: Session,
    valuation: OpportunityValuation,
    action: str,
    *,
    user_id: str | None = None,
    change_summary: str | None = None,
) -> None:
    db.add(
        OpportunityValuationHistory(
            valuation_id=valuation.id,
            organization_id=valuation.organization_id,
            version=valuation.version,
            action=action,
            snapshot_json=json.dumps(_snapshot_valuation(db, valuation), default=str),
            change_summary=change_summary,
            changed_by=user_id,
        )
    )


def _bump_version(valuation: OpportunityValuation) -> None:
    valuation.version += 1
    valuation.updated_at = _utcnow()


def create_valuation(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    user_id: str | None = None,
    value_type: str = ValueType.AHORRO,
    scope: str = ValueScope.INTERNO,
    currency: str = "USD",
) -> OpportunityValuation:
    _validate_opportunity(db, organization_id, opportunity_id)
    if value_type not in ValueType.ALL:
        raise ValuationValidationError(f"Tipo de valor no válido: {value_type}")
    if scope not in (ValueScope.INTERNO, ValueScope.EXTERNO):
        raise ValuationValidationError(f"Ámbito no válido: {scope}")

    existing = _get_valuation(db, organization_id, opportunity_id, required=False)
    if existing:
        raise ValuationValidationError("Ya existe una valoración para esta oportunidad.")

    valuation = OpportunityValuation(
        organization_id=organization_id,
        opportunity_id=opportunity_id,
        value_type=value_type,
        scope=scope,
        currency=currency,
        status=ValuationStatus.BORRADOR,
        created_by=user_id,
    )
    db.add(valuation)
    db.flush()

    for scenario_type in ScenarioType.ALL:
        db.add(
            OpportunityValuationScenario(
                valuation_id=valuation.id,
                organization_id=organization_id,
                scenario_type=scenario_type,
            )
        )
    db.add(
        OpportunityValuationExpected(
            valuation_id=valuation.id,
            organization_id=organization_id,
        )
    )
    db.commit()
    db.refresh(valuation)

    _append_history(db, valuation, ValuationHistoryAction.CREATED, user_id=user_id, change_summary="Valoración creada")
    write_audit(
        db,
        action="valoracion.creada",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}",
    )
    db.commit()
    return valuation


def update_expected(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    user_id: str | None = None,
    gross_value: Decimal | None = None,
    probability: Decimal | None = None,
    execution_cost_expected: Decimal | None = None,
    period_days: int | None = None,
    value_nature: str = ValueDiscipline.ESTIMADA,
    assumptions: str | None = None,
    source: str | None = None,
    evidence: str | None = None,
) -> OpportunityValuationExpected:
    valuation = _get_valuation(db, organization_id, opportunity_id)
    if valuation.status == ValuationStatus.VALIDADA:
        raise ValuationValidationError("La valoración está validada; cree una revisión antes de modificar.")

    expected = (
        db.query(OpportunityValuationExpected)
        .filter(OpportunityValuationExpected.valuation_id == valuation.id)
        .first()
    )
    if not expected:
        raise ValuationValidationError("Registro de valor esperado no encontrado.")

    _append_history(
        db,
        valuation,
        ValuationHistoryAction.EXPECTED_MODIFIED,
        user_id=user_id,
        change_summary="Valor esperado modificado",
    )

    if gross_value is not None:
        expected.gross_value = gross_value
    if probability is not None:
        if probability < 0 or probability > 1:
            raise ValuationValidationError("La probabilidad debe estar entre 0 y 1.")
        expected.probability = probability
    if execution_cost_expected is not None:
        expected.execution_cost_expected = execution_cost_expected
    if period_days is not None:
        expected.period_days = period_days
    if value_nature:
        expected.value_nature = value_nature
    if assumptions is not None:
        expected.assumptions = assumptions
    if source is not None:
        expected.source = source
    if evidence is not None:
        expected.evidence = evidence

    expected.adjusted_expected = compute_adjusted_expected(expected.gross_value, expected.probability)
    _bump_version(valuation)
    db.commit()
    db.refresh(expected)

    write_audit(
        db,
        action="valoracion.esperado.modificado",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}",
    )
    db.commit()
    return expected


def update_scenario(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    scenario_type: str,
    user_id: str | None = None,
    value_amount: Decimal | None = None,
    probability: Decimal | None = None,
    cost: Decimal | None = None,
    period_days: int | None = None,
    assumptions: str | None = None,
) -> OpportunityValuationScenario:
    if scenario_type not in ScenarioType.ALL:
        raise ValuationValidationError(f"Escenario no válido: {scenario_type}")

    valuation = _get_valuation(db, organization_id, opportunity_id)
    if valuation.status == ValuationStatus.VALIDADA:
        raise ValuationValidationError("La valoración está validada.")

    scenario = (
        db.query(OpportunityValuationScenario)
        .filter(
            OpportunityValuationScenario.valuation_id == valuation.id,
            OpportunityValuationScenario.scenario_type == scenario_type,
        )
        .first()
    )
    if not scenario:
        raise ValuationValidationError("Escenario no encontrado.")

    _append_history(
        db,
        valuation,
        ValuationHistoryAction.SCENARIO_MODIFIED,
        user_id=user_id,
        change_summary=f"Escenario {scenario_type} modificado",
    )

    if value_amount is not None:
        scenario.value_amount = value_amount
    if probability is not None:
        if probability < 0 or probability > 1:
            raise ValuationValidationError("La probabilidad debe estar entre 0 y 1.")
        scenario.probability = probability
    if cost is not None:
        scenario.cost = cost
    if period_days is not None:
        scenario.period_days = period_days
    if assumptions is not None:
        scenario.assumptions = assumptions

    scenario.adjusted_value = compute_adjusted_expected(scenario.value_amount, scenario.probability)
    _bump_version(valuation)
    db.commit()
    db.refresh(scenario)

    write_audit(
        db,
        action="valoracion.escenario.modificado",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}:{scenario_type}",
    )
    db.commit()
    return scenario


def register_real_value(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    user_id: str | None = None,
    materialized_value: Decimal | None = None,
    attributable_value: Decimal | None = None,
    value_nature: str = RealValueNature.ESTIMADO,
    attribution_level: str = AttributionLevel.NO_ATRIBUIBLE,
    attribution_pct: Decimal | None = None,
    source: str | None = None,
    evidence: str | None = None,
    responsible_id: str | None = None,
    justification: str | None = None,
    external_measurement_ref: str | None = None,
) -> OpportunityValuationReal:
    valuation = _get_valuation(db, organization_id, opportunity_id)

    if attribution_level == AttributionLevel.PARCIALMENTE_ATRIBUIBLE and attribution_pct is None:
        raise ValuationValidationError("Atribución parcial requiere porcentaje de atribución.")
    if attribution_pct is not None and (attribution_pct < 0 or attribution_pct > 100):
        raise ValuationValidationError("El porcentaje de atribución debe estar entre 0 y 100.")

    if materialized_value is not None and attributable_value is None:
        if attribution_level == AttributionLevel.ATRIBUIBLE:
            attributable_value = materialized_value
        elif attribution_level == AttributionLevel.PARCIALMENTE_ATRIBUIBLE and attribution_pct is not None:
            attributable_value = (materialized_value * attribution_pct / Decimal("100")).quantize(Decimal("0.0001"))
        elif attribution_level == AttributionLevel.NO_ATRIBUIBLE:
            attributable_value = Decimal("0")

    db.query(OpportunityValuationReal).filter(
        OpportunityValuationReal.valuation_id == valuation.id,
        OpportunityValuationReal.is_current.is_(True),
    ).update({"is_current": False})

    _append_history(
        db,
        valuation,
        ValuationHistoryAction.REAL_REGISTERED,
        user_id=user_id,
        change_summary="Valor real registrado",
    )

    real = OpportunityValuationReal(
        valuation_id=valuation.id,
        organization_id=organization_id,
        materialized_value=materialized_value,
        attributable_value=attributable_value,
        value_nature=value_nature,
        attribution_level=attribution_level,
        attribution_pct=attribution_pct,
        source=source,
        evidence=evidence,
        responsible_id=responsible_id or user_id,
        justification=justification,
        external_measurement_ref=external_measurement_ref,
        is_current=True,
    )
    db.add(real)
    _bump_version(valuation)
    db.commit()
    db.refresh(real)

    write_audit(
        db,
        action="valoracion.valor.real",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}",
    )
    db.commit()
    return real


def register_execution_cost(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    user_id: str | None = None,
    cost_type: str,
    amount: Decimal,
    currency: str | None = None,
    finops_record_id: str | None = None,
    description: str | None = None,
    source: str | None = None,
) -> OpportunityExecutionCost:
    valuation = _get_valuation(db, organization_id, opportunity_id)
    valid_types = (
        ExecutionCostType.IA,
        ExecutionCostType.HORAS_HUMANAS,
        ExecutionCostType.SERVICIOS,
        ExecutionCostType.INFRAESTRUCTURA,
        ExecutionCostType.LICENCIAS,
        ExecutionCostType.OTRO,
    )
    if cost_type not in valid_types:
        raise ValuationValidationError(f"Tipo de costo no válido: {cost_type}")

    _append_history(
        db,
        valuation,
        ValuationHistoryAction.COST_REGISTERED,
        user_id=user_id,
        change_summary=f"Costo de ejecución: {cost_type}",
    )

    cost = OpportunityExecutionCost(
        valuation_id=valuation.id,
        opportunity_id=opportunity_id,
        organization_id=organization_id,
        cost_type=cost_type,
        amount=amount,
        currency=currency or valuation.currency,
        finops_record_id=finops_record_id,
        description=description,
        source=source,
        recorded_by=user_id,
    )
    db.add(cost)
    _bump_version(valuation)
    db.commit()
    db.refresh(cost)

    write_audit(
        db,
        action="valoracion.costo.registrado",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}:{cost_type}",
    )
    db.commit()
    return cost


def validate_valuation(
    db: Session,
    *,
    organization_id: str,
    opportunity_id: str,
    user_id: str | None = None,
) -> OpportunityValuation:
    valuation = _get_valuation(db, organization_id, opportunity_id)
    expected = (
        db.query(OpportunityValuationExpected)
        .filter(OpportunityValuationExpected.valuation_id == valuation.id)
        .first()
    )
    if not expected or expected.gross_value is None:
        raise ValuationValidationError("No se puede validar sin valor bruto esperado.")

    _append_history(
        db,
        valuation,
        ValuationHistoryAction.VALIDATED,
        user_id=user_id,
        change_summary="Valoración validada",
    )
    valuation.status = ValuationStatus.VALIDADA
    valuation.validated_by = user_id
    valuation.validated_at = _utcnow()
    _bump_version(valuation)
    db.commit()
    db.refresh(valuation)

    write_audit(
        db,
        action="valoracion.validada",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"oportunidad:{opportunity_id}",
    )
    db.commit()
    return valuation


def _sum_execution_costs(db: Session, valuation_id: str, currency: str) -> Decimal:
    costs = (
        db.query(OpportunityExecutionCost)
        .filter(OpportunityExecutionCost.valuation_id == valuation_id)
        .all()
    )
    total = Decimal("0")
    for c in costs:
        if c.currency != currency:
            continue
        total += Decimal(str(c.amount))
    return total


def _finops_ia_cost(db: Session, organization_id: str, opportunity_id: str) -> tuple[Decimal | None, str | None]:
    try:
        eco = finops.summarize_opportunity_economics(db, organization_id, opportunity_id)
        return eco.get("total_cost"), eco.get("consumptions", [{}])[0].get("currency") if eco.get("consumptions") else None
    except finops.FinOpsValidationError:
        return None, None


def compute_economic_summary(
    db: Session,
    organization_id: str,
    opportunity_id: str,
) -> dict[str, Any]:
    """Resumen económico completo: esperado, real, costos, beneficio neto, retorno."""
    _validate_opportunity(db, organization_id, opportunity_id)
    valuation = _get_valuation(db, organization_id, opportunity_id, required=False)
    if not valuation:
        return {"has_valuation": False, "opportunity_id": opportunity_id}

    expected = (
        db.query(OpportunityValuationExpected)
        .filter(OpportunityValuationExpected.valuation_id == valuation.id)
        .first()
    )
    scenarios = (
        db.query(OpportunityValuationScenario)
        .filter(OpportunityValuationScenario.valuation_id == valuation.id)
        .order_by(OpportunityValuationScenario.scenario_type)
        .all()
    )
    real = (
        db.query(OpportunityValuationReal)
        .filter(
            OpportunityValuationReal.valuation_id == valuation.id,
            OpportunityValuationReal.is_current.is_(True),
        )
        .first()
    )
    exec_costs = (
        db.query(OpportunityExecutionCost)
        .filter(OpportunityExecutionCost.valuation_id == valuation.id)
        .all()
    )

    currency = valuation.currency
    finops_cost, finops_currency = _finops_ia_cost(db, organization_id, opportunity_id)
    manual_costs = _sum_execution_costs(db, valuation.id, currency)

    total_cost = manual_costs
    missing: list[str] = []
    if finops_cost is not None:
        if finops_currency and finops_currency != currency:
            missing.append(f"costo IA en moneda distinta ({finops_currency} vs {currency})")
        else:
            total_cost += finops_cost
    elif finops_cost is None and not exec_costs:
        missing.append("costo total de ejecución")

    attributable = _decimal(real.attributable_value) if real else None
    materialized = _decimal(real.materialized_value) if real else None
    gross_expected = _decimal(expected.gross_value) if expected else None
    adjusted_expected = _decimal(expected.adjusted_expected) if expected else None

    net_benefit: Decimal | None = None
    if attributable is not None and total_cost > 0:
        net_benefit = attributable - total_cost
    elif attributable is not None and total_cost == 0:
        net_benefit = attributable
    else:
        missing.append("valor atribuible materializado")

    return_pct: Decimal | None = None
    return_label = NO_CALCULABLE
    if net_benefit is not None and total_cost > 0:
        return_pct = ((net_benefit / total_cost) * Decimal("100")).quantize(Decimal("0.01"))
        return_label = f"{return_pct}%"
    elif net_benefit is not None and total_cost == 0 and net_benefit > 0:
        return_label = "Retorno infinito (costo cero)"
    elif missing:
        return_label = NO_CALCULABLE

    payback_days: int | None = None
    payback_label = NO_CALCULABLE
    period_days = expected.period_days if expected else None
    if (
        attributable is not None
        and period_days
        and period_days > 0
        and total_cost > 0
        and attributable > 0
    ):
        daily_benefit = attributable / Decimal(period_days)
        if daily_benefit > 0:
            payback_days = int((total_cost / daily_benefit).quantize(Decimal("1")))
            payback_label = f"{payback_days} días"
    elif period_days and attributable and total_cost > 0:
        missing.append("periodo insuficiente para recuperación")
    else:
        if not period_days:
            missing.append("periodo esperado")

    history = (
        db.query(OpportunityValuationHistory)
        .filter(OpportunityValuationHistory.valuation_id == valuation.id)
        .order_by(OpportunityValuationHistory.changed_at.desc())
        .limit(20)
        .all()
    )

    return {
        "has_valuation": True,
        "opportunity_id": opportunity_id,
        "valuation": _serialize_valuation(valuation),
        "expected": _serialize_expected(expected) if expected else None,
        "scenarios": [_serialize_scenario(s) for s in scenarios],
        "real": _serialize_real(real) if real else None,
        "execution_costs": [_serialize_cost(c) for c in exec_costs],
        "finops_ia_cost": finops_cost,
        "finops_ia_cost_label": finops.cost_label(finops_cost) if finops_cost is not None else finops.COST_UNAVAILABLE,
        "total_execution_cost": total_cost if total_cost > 0 or finops_cost is not None or exec_costs else None,
        "gross_expected": gross_expected,
        "adjusted_expected": adjusted_expected,
        "materialized_value": materialized,
        "attributable_value": attributable,
        "net_benefit": net_benefit,
        "return_percent": return_pct,
        "return_label": return_label,
        "payback_days": payback_days,
        "payback_label": payback_label,
        "missing_for_calculation": list(dict.fromkeys(missing)),
        "history": [_serialize_history(h) for h in history],
    }


def _serialize_valuation(v: OpportunityValuation) -> dict[str, Any]:
    return {
        "id": v.id,
        "opportunity_id": v.opportunity_id,
        "value_type": v.value_type,
        "scope": v.scope,
        "currency": v.currency,
        "status": v.status,
        "version": v.version,
        "validated_at": v.validated_at,
        "created_at": v.created_at,
        "updated_at": v.updated_at,
    }


def _serialize_expected(e: OpportunityValuationExpected) -> dict[str, Any]:
    return {
        "gross_value": e.gross_value,
        "probability": e.probability,
        "execution_cost_expected": e.execution_cost_expected,
        "period_days": e.period_days,
        "adjusted_expected": e.adjusted_expected,
        "value_nature": e.value_nature,
        "assumptions": e.assumptions,
        "source": e.source,
        "evidence": e.evidence,
        "updated_at": e.updated_at,
    }


def _serialize_scenario(s: OpportunityValuationScenario) -> dict[str, Any]:
    return {
        "scenario_type": s.scenario_type,
        "value_amount": s.value_amount,
        "probability": s.probability,
        "cost": s.cost,
        "period_days": s.period_days,
        "adjusted_value": s.adjusted_value,
        "assumptions": s.assumptions,
        "updated_at": s.updated_at,
    }


def _serialize_real(r: OpportunityValuationReal) -> dict[str, Any]:
    return {
        "materialized_value": r.materialized_value,
        "attributable_value": r.attributable_value,
        "value_nature": r.value_nature,
        "attribution_level": r.attribution_level,
        "attribution_pct": r.attribution_pct,
        "source": r.source,
        "evidence": r.evidence,
        "responsible_id": r.responsible_id,
        "justification": r.justification,
        "external_measurement_ref": r.external_measurement_ref,
        "recorded_at": r.recorded_at,
    }


def _serialize_cost(c: OpportunityExecutionCost) -> dict[str, Any]:
    return {
        "id": c.id,
        "cost_type": c.cost_type,
        "amount": c.amount,
        "currency": c.currency,
        "finops_record_id": c.finops_record_id,
        "description": c.description,
        "source": c.source,
        "created_at": c.created_at,
    }


def _serialize_history(h: OpportunityValuationHistory) -> dict[str, Any]:
    return {
        "id": h.id,
        "version": h.version,
        "action": h.action,
        "change_summary": h.change_summary,
        "changed_by": h.changed_by,
        "changed_at": h.changed_at,
    }
