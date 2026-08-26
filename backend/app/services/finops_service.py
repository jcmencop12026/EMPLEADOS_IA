from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.finops_enums import FinOpsBudgetState
from app.finops_models import FinOpsBudget, FinOpsRate, FinOpsValueRecord
from app.orchestration_models import AIEmployee, FinOpsRecord, WorkPlan

COST_UNAVAILABLE = "Costo no disponible"
VALUE_UNAVAILABLE = "Valor no disponible"
ROI_UNAVAILABLE = "ROI no disponible"


class FinOpsValidationError(ValueError):
    """Referencias cruzadas o datos inválidos en operaciones FinOps."""


def _validate_org_refs(
    db: Session,
    organization_id: str,
    *,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
) -> None:
    from app.orchestration_models import EmployeeTask

    if employee_id:
        employee = (
            db.query(AIEmployee)
            .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == organization_id)
            .first()
        )
        if not employee:
            raise FinOpsValidationError("Empleado IA no encontrado en la organización.")
    if work_plan_id:
        plan = (
            db.query(WorkPlan)
            .filter(WorkPlan.id == work_plan_id, WorkPlan.organization_id == organization_id)
            .first()
        )
        if not plan:
            raise FinOpsValidationError("Trabajo no encontrado en la organización.")
    if task_id:
        task = db.query(EmployeeTask).filter(EmployeeTask.id == task_id).first()
        if not task:
            raise FinOpsValidationError("Tarea no encontrada.")
        plan = db.query(WorkPlan).filter(WorkPlan.id == task.work_plan_id).first()
        if not plan or plan.organization_id != organization_id:
            raise FinOpsValidationError("Tarea no pertenece a la organización.")
        if work_plan_id and task.work_plan_id != work_plan_id:
            raise FinOpsValidationError("La tarea no pertenece al trabajo indicado.")


def _cost_currencies(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> set[str]:
    query = db.query(FinOpsRecord.currency).filter(
        FinOpsRecord.organization_id == organization_id,
        FinOpsRecord.currency.isnot(None),
        FinOpsRecord.cost.isnot(None),
    )
    if period_start:
        query = query.filter(FinOpsRecord.created_at >= period_start)
    if period_end:
        query = query.filter(FinOpsRecord.created_at <= period_end)
    return {row[0] for row in query.distinct().all() if row[0]}


def _value_currencies(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> set[str]:
    query = db.query(FinOpsValueRecord.currency).filter(
        FinOpsValueRecord.organization_id == organization_id,
        FinOpsValueRecord.currency.isnot(None),
        FinOpsValueRecord.amount.isnot(None),
        FinOpsValueRecord.certainty != "No disponible",
    )
    if period_start:
        query = query.filter(FinOpsValueRecord.created_at >= period_start)
    if period_end:
        query = query.filter(FinOpsValueRecord.created_at <= period_end)
    return {row[0] for row in query.distinct().all() if row[0]}


def _same_currency_for_roi(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> bool:
    cost_ccy = _cost_currencies(db, organization_id, period_start=period_start, period_end=period_end)
    value_ccy = _value_currencies(db, organization_id, period_start=period_start, period_end=period_end)
    if not cost_ccy and not value_ccy:
        return True
    if not cost_ccy or not value_ccy:
        return len(cost_ccy | value_ccy) <= 1
    return cost_ccy == value_ccy and len(cost_ccy) == 1


def budget_spent_for_scope(
    db: Session,
    budget: FinOpsBudget,
) -> Decimal:
    employee_id: str | None = None
    category: str | None = None
    if budget.scope_type == "empleado" and budget.scope_id:
        employee_id = budget.scope_id
    elif budget.scope_type == "proceso" and budget.scope_id:
        category = budget.scope_id
    spent = _sum_costs(
        db,
        budget.organization_id,
        period_start=budget.period_start,
        period_end=budget.period_end,
        employee_id=employee_id,
        category=category,
    )
    return spent or Decimal("0")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _decimal(value: float | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def cost_label(cost: Decimal | float | None) -> str:
    if cost is None:
        return COST_UNAVAILABLE
    return str(_decimal(cost))


def find_active_rate(
    db: Session,
    *,
    organization_id: str,
    provider: str | None,
    model_service: str | None,
    category: str,
    at: datetime | None = None,
) -> FinOpsRate | None:
    moment = at or _utcnow()
    query = (
        db.query(FinOpsRate)
        .filter(
            FinOpsRate.organization_id == organization_id,
            FinOpsRate.active.is_(True),
            FinOpsRate.category == category,
        )
        .order_by(FinOpsRate.valid_from.desc().nullslast())
    )
    if provider:
        query = query.filter(FinOpsRate.provider == provider)
    if model_service:
        query = query.filter(FinOpsRate.model_service == model_service)
    for rate in query.all():
        valid_from = _aware(rate.valid_from)
        valid_until = _aware(rate.valid_until)
        if valid_from and valid_from > moment:
            continue
        if valid_until and valid_until < moment:
            continue
        return rate
    return None


def calculate_cost_from_rate(
    rate: FinOpsRate,
    *,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    quantity: Decimal | None = None,
) -> tuple[Decimal | None, str]:
    total = Decimal("0")
    parts = 0
    if tokens_in and rate.price_input is not None:
        total += Decimal(tokens_in) * Decimal(str(rate.price_input))
        parts += 1
    if tokens_out and rate.price_output is not None:
        total += Decimal(tokens_out) * Decimal(str(rate.price_output))
        parts += 1
    if quantity is not None and rate.unit_price is not None:
        total += quantity * Decimal(str(rate.unit_price))
        parts += 1
    if parts == 0:
        return None, COST_UNAVAILABLE
    return total, f"tarifa:{rate.id}"


def registrar_consumo(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None = None,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    execution_ref: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    category: str = "Modelo IA",
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    quantity: Decimal | None = None,
    unit: str | None = None,
    duration_ms: int | None = None,
    currency: str | None = None,
    cost: Decimal | None = None,
    rate_id: str | None = None,
) -> FinOpsRecord:
    _validate_org_refs(
        db,
        organization_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
    )
    rate_source: str | None = None
    resolved_rate_id = rate_id
    resolved_currency = currency
    resolved_cost = cost

    if resolved_cost is None:
        rate = None
        if rate_id:
            rate = (
                db.query(FinOpsRate)
                .filter(FinOpsRate.id == rate_id, FinOpsRate.organization_id == organization_id)
                .first()
            )
            if not rate:
                raise FinOpsValidationError("Tarifa no encontrada en la organización.")
        else:
            rate = find_active_rate(
                db,
                organization_id=organization_id,
                provider=provider,
                model_service=model_name,
                category=category,
            )
        if rate:
            resolved_rate_id = rate.id
            resolved_currency = resolved_currency or rate.currency
            computed, rate_source = calculate_cost_from_rate(
                rate,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                quantity=quantity,
            )
            resolved_cost = computed

    record = FinOpsRecord(
        organization_id=organization_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        execution_ref=execution_ref,
        model_name=model_name,
        provider=provider,
        category=category,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        quantity=float(quantity) if quantity is not None else None,
        unit=unit,
        cost=float(_decimal(resolved_cost).quantize(Decimal("0.000001"))) if resolved_cost is not None else None,
        currency=resolved_currency,
        rate_source=rate_source,
        rate_id=resolved_rate_id,
        duration_ms=duration_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    write_audit(
        db,
        action="finops.consumption.registered",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"consumo:{record.id}",
    )
    return record


def registrar_valor(
    db: Session,
    *,
    organization_id: str,
    user_id: str | None = None,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    value_type: str,
    certainty: str = "Estimado",
    amount: Decimal | None = None,
    currency: str | None = None,
    methodology: str | None = None,
    source: str | None = None,
    notes: str | None = None,
) -> FinOpsValueRecord:
    _validate_org_refs(
        db,
        organization_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
    )
    row = FinOpsValueRecord(
        organization_id=organization_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        value_type=value_type,
        certainty=certainty,
        amount=amount,
        currency=currency,
        methodology=methodology,
        source=source,
        notes=notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="finops.value.registered",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"valor:{row.id}",
    )
    return row


def compute_roi(
    *,
    total_cost: Decimal | None,
    total_value: Decimal | None,
    same_currency: bool = True,
) -> tuple[Decimal | None, str]:
    if not same_currency:
        return None, ROI_UNAVAILABLE
    if total_cost is None or total_value is None:
        return None, ROI_UNAVAILABLE
    if total_cost == 0:
        if total_value > 0:
            return None, "ROI infinito (costo cero)"
        return Decimal("0"), "0%"
    roi = ((total_value - total_cost) / total_cost) * Decimal("100")
    return roi.quantize(Decimal("0.01")), f"{roi.quantize(Decimal('0.01'))}%"


def _sum_costs(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    category: str | None = None,
) -> Decimal | None:
    query = db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0)).filter(
        FinOpsRecord.organization_id == organization_id
    )
    if period_start:
        query = query.filter(FinOpsRecord.created_at >= period_start)
    if period_end:
        query = query.filter(FinOpsRecord.created_at <= period_end)
    if employee_id:
        query = query.filter(FinOpsRecord.employee_id == employee_id)
    if work_plan_id:
        query = query.filter(FinOpsRecord.work_plan_id == work_plan_id)
    if category:
        query = query.filter(FinOpsRecord.category == category)
    total = query.scalar()
    if total is None:
        return None
    dec = Decimal(str(total))
    if dec == 0 and not _has_cost_rows(
        db, organization_id, period_start, period_end, employee_id, work_plan_id, category
    ):
        return None
    return dec


def _has_cost_rows(
    db: Session,
    organization_id: str,
    period_start: datetime | None,
    period_end: datetime | None,
    employee_id: str | None,
    work_plan_id: str | None,
    category: str | None = None,
) -> bool:
    query = db.query(FinOpsRecord.id).filter(
        FinOpsRecord.organization_id == organization_id,
        FinOpsRecord.cost.isnot(None),
    )
    if period_start:
        query = query.filter(FinOpsRecord.created_at >= period_start)
    if period_end:
        query = query.filter(FinOpsRecord.created_at <= period_end)
    if employee_id:
        query = query.filter(FinOpsRecord.employee_id == employee_id)
    if work_plan_id:
        query = query.filter(FinOpsRecord.work_plan_id == work_plan_id)
    if category:
        query = query.filter(FinOpsRecord.category == category)
    return query.first() is not None


def _sum_values(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    certainty: str | None = None,
) -> Decimal | None:
    query = db.query(func.coalesce(func.sum(FinOpsValueRecord.amount), 0)).filter(
        FinOpsValueRecord.organization_id == organization_id,
        FinOpsValueRecord.certainty != "No disponible",
    )
    if period_start:
        query = query.filter(FinOpsValueRecord.created_at >= period_start)
    if period_end:
        query = query.filter(FinOpsValueRecord.created_at <= period_end)
    if certainty:
        query = query.filter(FinOpsValueRecord.certainty == certainty)
    total = query.scalar()
    if total is None:
        return None
    dec = Decimal(str(total))
    if dec == 0 and not db.query(FinOpsValueRecord.id).filter(
        FinOpsValueRecord.organization_id == organization_id,
        FinOpsValueRecord.amount.isnot(None),
    ).first():
        return None
    return dec


def dashboard_summary(
    db: Session,
    organization_id: str,
    *,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict[str, Any]:
    total_cost = _sum_costs(db, organization_id, period_start=period_start, period_end=period_end)
    total_value = _sum_values(db, organization_id, period_start=period_start, period_end=period_end)
    real_value = _sum_values(
        db, organization_id, period_start=period_start, period_end=period_end, certainty="Real"
    )
    estimated_savings = real_value
    net_benefit = None
    if total_cost is not None and total_value is not None:
        net_benefit = total_value - total_cost
    same_currency = _same_currency_for_roi(
        db, organization_id, period_start=period_start, period_end=period_end
    )
    roi, roi_label = compute_roi(
        total_cost=total_cost,
        total_value=total_value,
        same_currency=same_currency,
    )

    exec_query = db.query(func.count(func.distinct(FinOpsRecord.work_plan_id))).filter(
        FinOpsRecord.organization_id == organization_id,
        FinOpsRecord.work_plan_id.isnot(None),
    )
    if period_start:
        exec_query = exec_query.filter(FinOpsRecord.created_at >= period_start)
    if period_end:
        exec_query = exec_query.filter(FinOpsRecord.created_at <= period_end)
    execution_count = exec_query.scalar() or 0

    avg_cost = None
    if execution_count and total_cost is not None:
        avg_cost = (total_cost / Decimal(execution_count)).quantize(Decimal("0.0001"))

    currency = (
        db.query(FinOpsRecord.currency)
        .filter(FinOpsRecord.organization_id == organization_id, FinOpsRecord.currency.isnot(None))
        .order_by(FinOpsRecord.created_at.desc())
        .first()
    )
    currency_val = currency[0] if currency else None

    return {
        "period_start": period_start,
        "period_end": period_end,
        "total_cost": total_cost,
        "total_cost_label": cost_label(total_cost),
        "total_value": total_value,
        "total_value_label": VALUE_UNAVAILABLE if total_value is None else str(total_value),
        "estimated_savings": estimated_savings,
        "net_benefit": net_benefit,
        "roi_percent": roi,
        "roi_label": roi_label,
        "execution_count": execution_count,
        "avg_cost_per_work": avg_cost,
        "currency": currency_val,
    }


def budget_state(spent: Decimal, limit: Decimal) -> str:
    if limit <= 0:
        return FinOpsBudgetState.NORMAL
    ratio = spent / limit
    if ratio >= 1:
        return FinOpsBudgetState.LIMITE_ALCANZADO
    if ratio >= Decimal("0.9"):
        return FinOpsBudgetState.CERCA_LIMITE
    if ratio >= Decimal("0.75"):
        return FinOpsBudgetState.ATENCION
    return FinOpsBudgetState.NORMAL


def project_budget_spend(
    db: Session,
    budget: FinOpsBudget,
) -> Decimal | None:
    now = _utcnow()
    period_end = _aware(budget.period_end)
    period_start = _aware(budget.period_start)
    if period_end is None or period_start is None:
        return None
    if now >= period_end:
        return _sum_costs(
            db,
            budget.organization_id,
            period_start=period_start,
            period_end=period_end,
        )
    elapsed = (now - period_start).total_seconds()
    total = (period_end - period_start).total_seconds()
    if total <= 0:
        return None
    spent = _sum_costs(
        db,
        budget.organization_id,
        period_start=period_start,
        period_end=now,
        employee_id=budget.scope_id if budget.scope_type == "empleado" else None,
        category=budget.scope_id if budget.scope_type == "proceso" else None,
    )
    if spent is None:
        return None
    daily = spent / Decimal(str(max(elapsed / 86400, 1 / 86400)))
    remaining_days = Decimal(str(max((period_end - now).total_seconds() / 86400, 0)))
    return (spent + daily * remaining_days).quantize(Decimal("0.01"))


def serialize_consumption(record: FinOpsRecord) -> dict[str, Any]:
    cost = _decimal(record.cost)
    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "employee_id": record.employee_id,
        "work_plan_id": record.work_plan_id,
        "task_id": record.task_id,
        "execution_ref": record.execution_ref,
        "provider": record.provider,
        "model_name": record.model_name,
        "category": record.category,
        "tokens_in": record.tokens_in,
        "tokens_out": record.tokens_out,
        "quantity": _decimal(record.quantity) if record.quantity is not None else None,
        "unit": record.unit,
        "cost": cost,
        "cost_label": cost_label(cost),
        "currency": record.currency,
        "rate_source": record.rate_source,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at,
    }


def build_drill_down(
    db: Session,
    organization_id: str,
    *,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
) -> list[dict[str, Any]]:
    if work_plan_id:
        records = (
            db.query(FinOpsRecord)
            .filter(FinOpsRecord.organization_id == organization_id, FinOpsRecord.work_plan_id == work_plan_id)
            .all()
        )
        return [
            {
                "id": r.id,
                "label": r.execution_ref or r.model_name or r.id[:8],
                "node_type": "ejecucion",
                "cost": _decimal(r.cost),
                "cost_label": cost_label(_decimal(r.cost)),
                "children": [],
            }
            for r in records
        ]

    employees = db.query(AIEmployee).filter(AIEmployee.organization_id == organization_id)
    if employee_id:
        employees = employees.filter(AIEmployee.id == employee_id)
    nodes: list[dict[str, Any]] = []
    for emp in employees.all():
        plans = (
            db.query(WorkPlan)
            .join(FinOpsRecord, FinOpsRecord.work_plan_id == WorkPlan.id)
            .filter(FinOpsRecord.organization_id == organization_id, FinOpsRecord.employee_id == emp.id)
            .distinct()
            .all()
        )
        plan_nodes = []
        for plan in plans:
            cost = _sum_costs(db, organization_id, work_plan_id=plan.id)
            plan_nodes.append(
                {
                    "id": plan.id,
                    "label": plan.objective or plan.id[:8],
                    "node_type": "trabajo",
                    "cost": cost,
                    "cost_label": cost_label(cost),
                    "children": build_drill_down(db, organization_id, work_plan_id=plan.id),
                }
            )
        emp_cost = _sum_costs(db, organization_id, employee_id=emp.id)
        nodes.append(
            {
                "id": emp.id,
                "label": emp.name,
                "node_type": "empleado",
                "cost": emp_cost,
                "cost_label": cost_label(emp_cost),
                "children": plan_nodes,
            }
        )
    return nodes
