"""Servicio — Planificador de consumo y capacidad IA (MB-07)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.consumption_planner_models import (
    ConsumptionPlannerOrgConfig,
    ConsumptionPlannerSimulation,
    ConsumptionPlannerTransversal,
)
from app.finops_models import FinOpsBudget, FinOpsRate, FinOpsValueRecord
from app.llm_models import LlmInferenceLog
from app.models import User
from app.orchestration_models import AIEmployee, FinOpsRecord
from app.services import control_center_service as cc_svc
from app.services import finops_service as finops_svc
from app.valuation_enums import RealValueNature

DEFAULT_MODEL_DISTRIBUTION = [
    {"provider": "openai", "model": "gpt-4o-mini", "pct": 60.0},
    {"provider": "openai", "model": "gpt-4o", "pct": 30.0},
    {"provider": "anthropic", "model": "claude-3-5-sonnet", "pct": 10.0},
]
DEFAULT_ALERT_THRESHOLDS = [70, 80, 90, 100]
DEFAULT_TRANSVERSAL = [
    {
        "capability_code": "auditor_empleados",
        "consumption_class": "TRANSVERSAL_ATRIBUIBLE",
        "activation_type": "CONTINUO_DETERMINISTICO",
        "is_deterministic": True,
        "executions_per_period": 30,
        "infra_cost_estimated": 2.0,
    },
    {
        "capability_code": "oportunidades",
        "consumption_class": "TRANSVERSAL_ATRIBUIBLE",
        "activation_type": "POR_EVENTO",
        "is_deterministic": False,
        "executions_per_period": 50,
        "tokens_in_avg": 2000,
        "tokens_out_avg": 1000,
        "provider": "openai",
        "model_name": "gpt-4o-mini",
    },
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _d(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, requested_org_id)


def get_or_create_org_config(db: Session, org_id: str) -> ConsumptionPlannerOrgConfig:
    row = db.query(ConsumptionPlannerOrgConfig).filter(ConsumptionPlannerOrgConfig.organization_id == org_id).first()
    if row:
        return row
    row = ConsumptionPlannerOrgConfig(
        organization_id=org_id,
        model_distribution_json=_json_dumps(DEFAULT_MODEL_DISTRIBUTION),
        alert_thresholds_json=_json_dumps(DEFAULT_ALERT_THRESHOLDS),
    )
    db.add(row)
    db.flush()
    for spec in DEFAULT_TRANSVERSAL:
        db.add(
            ConsumptionPlannerTransversal(
                organization_id=org_id,
                **spec,
            )
        )
    db.flush()
    return row


def org_config_to_dict(row: ConsumptionPlannerOrgConfig) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "credential_mode": row.credential_mode,
        "currency": row.currency,
        "included_consumption_usd": float(row.included_consumption_usd or 0),
        "client_price_monthly": float(row.client_price_monthly or 0) if row.client_price_monthly else None,
        "capacity_total_units": float(row.capacity_total_units or 0) if row.capacity_total_units else None,
        "max_concurrency": row.max_concurrency,
        "executions_per_employee_per_day": float(row.executions_per_employee_per_day),
        "tokens_in_avg": row.tokens_in_avg,
        "tokens_out_avg": row.tokens_out_avg,
        "model_distribution": _json_loads(row.model_distribution_json) or DEFAULT_MODEL_DISTRIBUTION,
        "alert_thresholds": _json_loads(row.alert_thresholds_json) or DEFAULT_ALERT_THRESHOLDS,
        "plan_label": row.plan_label,
    }


def update_org_config(db: Session, org_id: str, data: dict[str, Any], user: User) -> ConsumptionPlannerOrgConfig:
    row = get_or_create_org_config(db, org_id)
    for field in (
        "credential_mode",
        "currency",
        "included_consumption_usd",
        "client_price_monthly",
        "capacity_total_units",
        "max_concurrency",
        "executions_per_employee_per_day",
        "tokens_in_avg",
        "tokens_out_avg",
        "plan_label",
    ):
        if data.get(field) is not None:
            setattr(row, field, data[field])
    if data.get("model_distribution") is not None:
        row.model_distribution_json = _json_dumps(data["model_distribution"])
    if data.get("alert_thresholds") is not None:
        row.alert_thresholds_json = _json_dumps(data["alert_thresholds"])
    row.updated_at = _utcnow()
    write_audit(
        db,
        action="consumption_planner.config.updated",
        organization_id=org_id,
        user_id=user.id,
        detail="Configuración planificador actualizada",
        commit=False,
    )
    db.flush()
    return row


def classify_finops_record(record: FinOpsRecord) -> str:
    ref = (record.execution_ref or "").lower()
    if ref.startswith("platform:") or ref.startswith("plataforma:"):
        return "PLATAFORMA"
    if ref.startswith("transversal:") or ref.startswith("transversal_"):
        return "TRANSVERSAL_ATRIBUIBLE"
    if record.employee_id:
        return "DIRECTO"
    if record.category in ("Almacenamiento", "Procesamiento") and not record.employee_id:
        return "PLATAFORMA"
    return "DIRECTO" if record.employee_id else "PLATAFORMA"


def _is_deterministic_record(record: FinOpsRecord) -> bool:
    ref = (record.execution_ref or "").lower()
    if "deterministic" in ref or ref.startswith("transversal:auditor"):
        return True
    if (record.tokens_in or 0) == 0 and (record.tokens_out or 0) == 0 and (record.cost or 0) == 0:
        return True
    return False


def _rate_for(db: Session, org_id: str, provider: str | None, model: str | None) -> FinOpsRate | None:
    q = db.query(FinOpsRate).filter(FinOpsRate.organization_id == org_id, FinOpsRate.active.is_(True))
    if provider:
        q = q.filter(FinOpsRate.provider == provider)
    if model:
        q = q.filter(FinOpsRate.model_service == model)
    return q.order_by(FinOpsRate.valid_from.desc().nullslast()).first()


def _llm_cost_from_rate(tokens_in: int, tokens_out: int, rate: FinOpsRate | None) -> Decimal:
    if not rate:
        return Decimal("0")
    cost = Decimal("0")
    if rate.price_input:
        cost += _d(tokens_in) * _d(rate.price_input)
    if rate.price_output:
        cost += _d(tokens_out) * _d(rate.price_output)
    return cost


def validate_distribution(distribution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not distribution:
        return DEFAULT_MODEL_DISTRIBUTION
    total = sum(float(x.get("pct", 0)) for x in distribution)
    if abs(total - 100.0) > 0.01:
        raise ValueError("La distribución de modelos debe sumar 100%")
    return distribution


def weighted_llm_cost(
    db: Session,
    org_id: str,
    tokens_in: int,
    tokens_out: int,
    distribution: list[dict[str, Any]],
    currency: str,
) -> Decimal:
    distribution = validate_distribution(distribution)
    total = Decimal("0")
    for slice_ in distribution:
        pct = _d(slice_.get("pct", 0)) / Decimal("100")
        rate = _rate_for(db, org_id, slice_.get("provider"), slice_.get("model"))
        total += _llm_cost_from_rate(int(tokens_in * pct), int(tokens_out * pct), rate)
    return total


def aggregate_real_consumption(
    db: Session,
    org_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict[str, Any]:
    if not period_end:
        period_end = _utcnow()
    if not period_start:
        period_start = period_end - timedelta(days=30)
    records = (
        db.query(FinOpsRecord)
        .filter(
            FinOpsRecord.organization_id == org_id,
            FinOpsRecord.created_at >= period_start,
            FinOpsRecord.created_at <= period_end,
        )
        .all()
    )
    buckets: dict[str, dict[str, Any]] = {
        "DIRECTO": {"cost_ia": Decimal("0"), "cost_other": Decimal("0"), "tokens_in": 0, "tokens_out": 0, "executions": 0},
        "TRANSVERSAL_ATRIBUIBLE": {"cost_ia": Decimal("0"), "cost_other": Decimal("0"), "tokens_in": 0, "tokens_out": 0, "executions": 0},
        "PLATAFORMA": {"cost_ia": Decimal("0"), "cost_other": Decimal("0"), "tokens_in": 0, "tokens_out": 0, "executions": 0},
    }
    for r in records:
        cls = classify_finops_record(r)
        bucket = buckets[cls]
        cost = _d(r.cost)
        is_llm = r.category == "Modelo IA" or (r.tokens_in or r.tokens_out)
        if _is_deterministic_record(r):
            bucket["cost_other"] += cost
        elif is_llm:
            bucket["cost_ia"] += cost
        else:
            bucket["cost_other"] += cost
        bucket["tokens_in"] += int(r.tokens_in or 0)
        bucket["tokens_out"] += int(r.tokens_out or 0)
        bucket["executions"] += 1

    # LLM logs for additional REAL token/cost attribution
    llm_rows = (
        db.query(LlmInferenceLog)
        .filter(
            LlmInferenceLog.organization_id == org_id,
            LlmInferenceLog.created_at >= period_start,
            LlmInferenceLog.created_at <= period_end,
        )
        .all()
    )
    for log in llm_rows:
        cls = "DIRECTO" if log.employee_id else "TRANSVERSAL_ATRIBUIBLE"
        bucket = buckets[cls]
        bucket["tokens_in"] += int(log.tokens_in or 0)
        bucket["tokens_out"] += int(log.tokens_out or 0)
        bucket["cost_ia"] += _d(log.cost)
        bucket["executions"] += 1

    return {
        "kind": "REAL",
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "by_class": {
            k: {
                "cost_ia": float(v["cost_ia"]),
                "cost_other": float(v["cost_other"]),
                "cost_total": float(v["cost_ia"] + v["cost_other"]),
                "tokens_in": v["tokens_in"],
                "tokens_out": v["tokens_out"],
                "executions": v["executions"],
            }
            for k, v in buckets.items()
        },
    }


def estimate_transversal_monthly(db: Session, org_id: str, config: ConsumptionPlannerOrgConfig) -> dict[str, Any]:
    rows = (
        db.query(ConsumptionPlannerTransversal)
        .filter(ConsumptionPlannerTransversal.organization_id == org_id, ConsumptionPlannerTransversal.enabled.is_(True))
        .all()
    )
    items: list[dict[str, Any]] = []
    total_ia = Decimal("0")
    total_tools = Decimal("0")
    total_infra = Decimal("0")
    distribution = _json_loads(config.model_distribution_json) or DEFAULT_MODEL_DISTRIBUTION
    for row in rows:
        monthly_exec = _d(row.executions_per_period) * Decimal("30") / Decimal(max(row.period_days, 1))
        llm_cost = Decimal("0")
        if not row.is_deterministic:
            llm_cost = weighted_llm_cost(
                db,
                org_id,
                int(monthly_exec * row.tokens_in_avg),
                int(monthly_exec * row.tokens_out_avg),
                distribution,
                config.currency,
            )
        tools = _d(row.tools_cost_estimated)
        infra = _d(row.infra_cost_estimated)
        total_ia += llm_cost
        total_tools += tools
        total_infra += infra
        items.append(
            {
                "capability_code": row.capability_code,
                "consumption_class": row.consumption_class,
                "activation_type": row.activation_type,
                "is_deterministic": row.is_deterministic,
                "executions_monthly": float(monthly_exec),
                "cost_ia": float(llm_cost),
                "cost_tools": float(tools),
                "cost_infra": float(infra),
                "cost_total": float(llm_cost + tools + infra),
            }
        )
    return {
        "kind": "ESTIMADO",
        "items": items,
        "cost_ia": float(total_ia),
        "cost_tools": float(total_tools),
        "cost_infra": float(total_infra),
        "cost_total": float(total_ia + total_tools + total_infra),
    }


def estimate_direct_monthly(
    db: Session,
    org_id: str,
    config: ConsumptionPlannerOrgConfig,
    *,
    active_employees: int | None = None,
    executions_per_day: float | None = None,
    days: int = 30,
) -> dict[str, Any]:
    if active_employees is None:
        active_employees = (
            db.query(func.count(AIEmployee.id))
            .filter(AIEmployee.organization_id == org_id, AIEmployee.is_active.is_(True))
            .scalar()
            or 0
        )
    exec_per_day = executions_per_day or float(config.executions_per_employee_per_day)
    monthly_exec = int(active_employees * exec_per_day * days)
    tokens_in = monthly_exec * config.tokens_in_avg
    tokens_out = monthly_exec * config.tokens_out_avg
    distribution = _json_loads(config.model_distribution_json) or DEFAULT_MODEL_DISTRIBUTION
    llm_cost = weighted_llm_cost(db, org_id, tokens_in, tokens_out, distribution, config.currency)
    return {
        "kind": "ESTIMADO",
        "active_employees": active_employees,
        "executions_per_day": exec_per_day,
        "days": days,
        "executions_monthly": monthly_exec,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_ia": float(llm_cost),
        "cost_total": float(llm_cost),
    }


def simulate(
    db: Session,
    org_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Simulador ¿Qué pasa si...? — resultados ESTIMADO/PROYECTADO."""
    config = get_or_create_org_config(db, org_id)
    active = int(params.get("active_employees") or params.get("employee_count") or 25)
    exec_day = float(params.get("executions_per_day") or params.get("executions_per_employee_per_day") or config.executions_per_employee_per_day)
    days = int(params.get("days") or 30)
    if params.get("model_distribution"):
        config.model_distribution_json = _json_dumps(params["model_distribution"])
    direct = estimate_direct_monthly(db, org_id, config, active_employees=active, executions_per_day=exec_day, days=days)
    transversal = estimate_transversal_monthly(db, org_id, config)
    platform_cost = float(params.get("platform_cost_monthly") or 0)
    total_cost = direct["cost_total"] + transversal["cost_total"] + platform_cost
    included = float(config.included_consumption_usd or 0)
    capacity_total = float(config.capacity_total_units or 0)
    exec_monthly = direct["executions_monthly"] + sum(i["executions_monthly"] for i in transversal["items"])
    max_conc = config.max_concurrency or max(active, 1)
    exec_per_hour = exec_monthly / max(days * 24, 1)
    committed_capacity = exec_monthly / max(days, 1)
    budget_rows = db.query(FinOpsBudget).filter(FinOpsBudget.organization_id == org_id, FinOpsBudget.active.is_(True)).all()
    budget_limit = sum(float(b.amount_limit) for b in budget_rows) if budget_rows else included
    utilization_pct = (total_cost / budget_limit * 100) if budget_limit > 0 else None
    risk = "NORMAL"
    if utilization_pct and utilization_pct >= 100:
        risk = "CRITICO"
    elif utilization_pct and utilization_pct >= 90:
        risk = "ALTO"
    elif utilization_pct and utilization_pct >= 70:
        risk = "MEDIO"
    return {
        "kind": "PROYECTADO",
        "params": params,
        "directo": direct,
        "transversal": transversal,
        "plataforma_cost_monthly": platform_cost,
        "cost_total": total_cost,
        "consumo_incluido": included,
        "sobreconsumo": max(0.0, total_cost - included),
        "capacity": {
            "capacity_total": capacity_total,
            "capacity_committed_daily": round(committed_capacity, 2),
            "capacity_available": max(0.0, capacity_total - committed_capacity) if capacity_total else None,
            "max_concurrency": max_conc,
            "expected_concurrency": min(max_conc, active),
            "executions_per_hour": round(exec_per_hour, 4),
            "executions_per_day": round(exec_monthly / max(days, 1), 2),
        },
        "budget": {
            "limit": budget_limit,
            "projected_cost": total_cost,
            "utilization_pct": round(utilization_pct, 2) if utilization_pct else None,
            "risk": risk,
        },
        "demo_notice": "Valores de simulación — no tarifas reales de proveedores.",
    }


def compare_providers(
    db: Session,
    org_id: str,
    scenarios: list[dict[str, Any]],
    *,
    tokens_in: int,
    tokens_out: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sc in scenarios:
        provider = sc.get("provider")
        model = sc.get("model")
        rate = _rate_for(db, org_id, provider, model)
        cost = _llm_cost_from_rate(tokens_in, tokens_out, rate)
        out.append(
            {
                "provider": provider,
                "model": model,
                "cost_estimated": float(cost),
                "currency": rate.currency if rate else "USD",
                "rate_configured": rate is not None,
                "latency_hint": sc.get("latency_hint"),
                "note": "Comparación basada en catálogo configurado — no implica recomendación automática.",
            }
        )
    return out


def employee_cost_detail(db: Session, org_id: str, employee_id: str, *, days: int = 30) -> dict[str, Any]:
    since = _utcnow() - timedelta(days=days)
    emp = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )
    if not emp:
        raise ValueError("Empleado no encontrado")
    records = (
        db.query(FinOpsRecord)
        .filter(
            FinOpsRecord.organization_id == org_id,
            FinOpsRecord.employee_id == employee_id,
            FinOpsRecord.created_at >= since,
        )
        .all()
    )
    cost_ia = Decimal("0")
    cost_other = Decimal("0")
    tokens_in = 0
    tokens_out = 0
    for r in records:
        c = _d(r.cost)
        if _is_deterministic_record(r):
            cost_other += c
        elif r.category == "Modelo IA" or r.tokens_in or r.tokens_out:
            cost_ia += c
        else:
            cost_other += c
        tokens_in += int(r.tokens_in or 0)
        tokens_out += int(r.tokens_out or 0)
    config = get_or_create_org_config(db, org_id)
    estimated = estimate_direct_monthly(db, org_id, config, active_employees=1, days=days)
    return {
        "employee_id": employee_id,
        "employee_name": emp.name,
        "real": {
            "executions": len(records),
            "cost_ia": float(cost_ia),
            "cost_other": float(cost_other),
            "cost_total": float(cost_ia + cost_other),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        },
        "estimated_monthly_single": estimated,
    }


def margin_summary(db: Session, org_id: str, config: ConsumptionPlannerOrgConfig, projected_cost: float) -> dict[str, Any]:
    price = float(config.client_price_monthly or 0)
    if not price:
        return {"available": False, "reason": "Sin precio cliente configurado"}
    cost = projected_cost
    margin = price - cost
    return {
        "available": True,
        "kind": "ESTIMADO",
        "client_price_monthly": price,
        "cost_total": cost,
        "gross_margin": margin,
        "gross_margin_pct": round(margin / price * 100, 2) if price else None,
        "currency": config.currency,
        "credential_mode": config.credential_mode,
        "client_cost_note": "CREDENCIALES_PROPIAS: costo API puede ser COSTO_DEL_CLIENTE",
    }


def realized_value_sum(db: Session, org_id: str, *, period_start: datetime | None = None) -> Decimal:
    """Valor realizado — excluye POTENCIAL de valoración."""
    q = db.query(FinOpsValueRecord).filter(
        FinOpsValueRecord.organization_id == org_id,
        FinOpsValueRecord.certainty == "Real",
    )
    if period_start:
        q = q.filter(FinOpsValueRecord.created_at >= period_start)
    total = Decimal("0")
    for row in q.all():
        if row.notes and RealValueNature.POTENCIAL in row.notes:
            continue
        if row.amount:
            total += _d(row.amount)
    return total


def org_resumen(db: Session, org_id: str) -> dict[str, Any]:
    config = get_or_create_org_config(db, org_id)
    real = aggregate_real_consumption(db, org_id)
    direct_est = estimate_direct_monthly(db, org_id, config)
    trans_est = estimate_transversal_monthly(db, org_id, config)
    projected = direct_est["cost_total"] + trans_est["cost_total"]
    real_total = sum(v["cost_total"] for v in real["by_class"].values())
    included = float(config.included_consumption_usd or 0)
    realized_value = float(realized_value_sum(db, org_id, period_start=_utcnow() - timedelta(days=30)))
    return {
        "organization_id": org_id,
        "currency": config.currency,
        "credential_mode": config.credential_mode,
        "consumo_incluido": included,
        "consumo_real": real_total,
        "consumo_estimado_mensual": projected,
        "consumo_proyectado_mes": projected,
        "sobreconsumo_estimado": max(0.0, projected - included),
        "real_by_class": real["by_class"],
        "estimated_direct": direct_est,
        "estimated_transversal": trans_est,
        "valor_realizado_mes": realized_value,
        "potencial_excluido_roi": True,
        "margin": margin_summary(db, org_id, config, projected),
    }


def centro_control_contract(db: Session, org_id: str) -> dict[str, Any]:
    resumen = org_resumen(db, org_id)
    sim = simulate(db, org_id, {"active_employees": 25, "executions_per_day": 20, "days": 30})
    return {
        "organization_id": org_id,
        "consumo_real": resumen["consumo_real"],
        "consumo_proyectado": resumen["consumo_proyectado_mes"],
        "presupuesto_limite": sim["budget"]["limit"],
        "presupuesto_utilizacion_pct": sim["budget"]["utilization_pct"],
        "capacidad_riesgo": sim["budget"]["risk"],
        "sobreconsumo": resumen["sobreconsumo_estimado"],
        "margen_bruto_estimado": resumen["margin"].get("gross_margin"),
        "currency": resumen["currency"],
    }


def prepare_alert_contracts(db: Session, org_id: str) -> list[dict[str, Any]]:
    config = get_or_create_org_config(db, org_id)
    resumen = org_resumen(db, org_id)
    thresholds = _json_loads(config.alert_thresholds_json) or DEFAULT_ALERT_THRESHOLDS
    included = float(config.included_consumption_usd or 0)
    projected = resumen["consumo_proyectado_mes"]
    alerts: list[dict[str, Any]] = []
    if included > 0:
        pct = projected / included * 100
        for th in sorted(thresholds):
            if pct >= th:
                alerts.append(
                    {
                        "event_type": "FINOPS_LIMIT_REACHED",
                        "severity": "CRITICAL" if th >= 100 else "HIGH",
                        "title": f"Proyección consumo IA {pct:.0f}% del incluido",
                        "threshold_pct": th,
                        "projected_pct": round(pct, 2),
                    }
                )
                break
    cap = config.capacity_total_units
    if cap and resumen.get("estimated_direct", {}).get("executions_monthly"):
        daily = resumen["estimated_direct"]["executions_monthly"] / 30
        if daily > float(cap):
            alerts.append(
                {
                    "event_type": "CAPACITY_THRESHOLD",
                    "severity": "HIGH",
                    "title": "Capacidad comprometida supera límite configurado",
                }
            )
    return alerts


def list_transversal(db: Session, org_id: str) -> list[ConsumptionPlannerTransversal]:
    get_or_create_org_config(db, org_id)
    return (
        db.query(ConsumptionPlannerTransversal)
        .filter(ConsumptionPlannerTransversal.organization_id == org_id)
        .order_by(ConsumptionPlannerTransversal.capability_code)
        .all()
    )


def transversal_to_dict(row: ConsumptionPlannerTransversal) -> dict[str, Any]:
    return {
        "id": row.id,
        "capability_code": row.capability_code,
        "consumption_class": row.consumption_class,
        "activation_type": row.activation_type,
        "is_deterministic": row.is_deterministic,
        "executions_per_period": float(row.executions_per_period),
        "period_days": row.period_days,
        "tokens_in_avg": row.tokens_in_avg,
        "tokens_out_avg": row.tokens_out_avg,
        "provider": row.provider,
        "model_name": row.model_name,
        "tools_cost_estimated": float(row.tools_cost_estimated),
        "infra_cost_estimated": float(row.infra_cost_estimated),
        "enabled": row.enabled,
    }


def update_transversal(
    db: Session,
    org_id: str,
    transversal_id: str,
    data: dict[str, Any],
    user: User,
) -> ConsumptionPlannerTransversal:
    row = (
        db.query(ConsumptionPlannerTransversal)
        .filter(
            ConsumptionPlannerTransversal.id == transversal_id,
            ConsumptionPlannerTransversal.organization_id == org_id,
        )
        .first()
    )
    if not row:
        raise ValueError("Capacidad transversal no encontrada")
    for field in (
        "activation_type",
        "is_deterministic",
        "executions_per_period",
        "period_days",
        "tokens_in_avg",
        "tokens_out_avg",
        "provider",
        "model_name",
        "tools_cost_estimated",
        "infra_cost_estimated",
        "enabled",
    ):
        if data.get(field) is not None:
            setattr(row, field, data[field])
    row.updated_at = _utcnow()
    write_audit(
        db,
        action="consumption_planner.transversal.updated",
        organization_id=org_id,
        user_id=user.id,
        detail=f"transversal:{row.capability_code}",
        commit=False,
    )
    db.flush()
    return row


def presupuesto_summary(db: Session, org_id: str) -> dict[str, Any]:
    config = get_or_create_org_config(db, org_id)
    resumen = org_resumen(db, org_id)
    budgets = db.query(FinOpsBudget).filter(FinOpsBudget.organization_id == org_id, FinOpsBudget.active.is_(True)).all()
    included = float(config.included_consumption_usd or 0)
    projected = resumen["consumo_proyectado_mes"]
    real = resumen["consumo_real"]
    thresholds = _json_loads(config.alert_thresholds_json) or DEFAULT_ALERT_THRESHOLDS
    limit = sum(float(b.amount_limit) for b in budgets) if budgets else included
    utilization = (projected / limit * 100) if limit > 0 else None
    return {
        "currency": config.currency,
        "presupuesto_ia": limit,
        "consumo_incluido": included,
        "consumo_real": real,
        "consumo_proyectado": projected,
        "sobreconsumo": max(0.0, projected - included),
        "porcentaje_utilizado": round(utilization, 2) if utilization else None,
        "proyeccion_cierre_mes": projected,
        "alert_thresholds": thresholds,
        "budgets": [
            {
                "id": b.id,
                "name": b.name,
                "amount_limit": float(b.amount_limit),
                "currency": b.currency,
                "policy": b.policy,
                "alert_threshold_pct": b.alert_threshold_pct,
            }
            for b in budgets
        ],
    }


def save_simulation(db: Session, org_id: str, user: User, name: str, params: dict[str, Any], results: dict[str, Any]) -> ConsumptionPlannerSimulation:
    row = ConsumptionPlannerSimulation(
        organization_id=org_id,
        name=name,
        params_json=_json_dumps(params),
        results_json=_json_dumps(results),
        created_by=user.id,
    )
    db.add(row)
    db.flush()
    return row
