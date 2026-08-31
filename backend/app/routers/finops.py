from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.finops_models import FinOpsBudget, FinOpsRate, FinOpsValueRecord
from app.models import User
from app.orchestration_models import AIEmployee, FinOpsRecord, WorkPlan
from app.permissions import check_permission
from app.schemas_finops import (
    BudgetIn,
    BudgetOut,
    BudgetPatch,
    ConsumptionIn,
    ConsumptionOut,
    DashboardSummary,
    DrillDownNode,
    OpportunityEconomicsOut,
    RateIn,
    RateOut,
    RatePatch,
    ValueIn,
    ValueOut,
)
from app.services import finops_service as svc
from app.audit import write_audit

router = APIRouter(prefix="/api/finops", tags=["finops"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    return svc.dashboard_summary(db, user.organization_id, period_start=period_start, period_end=period_end)


@router.get("/consumptions", response_model=list[ConsumptionOut])
def list_consumptions(
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    opportunity_id: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    category: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    rows = svc.query_consumptions(
        db,
        user.organization_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        opportunity_id=opportunity_id,
        provider=provider,
        model_name=model_name,
        category=category,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
    )
    return [svc.serialize_consumption(r) for r in rows]


@router.post("/consumptions", response_model=ConsumptionOut)
def create_consumption(
    body: ConsumptionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.manage", db)
    try:
        record = svc.registrar_consumo(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            employee_id=body.employee_id,
            work_plan_id=body.work_plan_id,
            task_id=body.task_id,
            opportunity_id=body.opportunity_id,
            execution_ref=body.execution_ref,
            provider=body.provider,
            model_name=body.model_name,
            category=body.category,
            tokens_in=body.tokens_in,
            tokens_out=body.tokens_out,
            quantity=body.quantity,
            unit=body.unit,
            duration_ms=body.duration_ms,
            currency=body.currency,
            cost=body.cost,
            rate_id=body.rate_id,
        )
    except svc.FinOpsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except svc.FinOpsBudgetBlockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return svc.serialize_consumption(record)


@router.get("/opportunities/{opportunity_id}/economics", response_model=OpportunityEconomicsOut)
def opportunity_economics(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    try:
        return svc.summarize_opportunity_economics(db, user.organization_id, opportunity_id)
    except svc.FinOpsValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rates", response_model=list[RateOut])
def list_rates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "finops.rates", db)
    return (
        db.query(FinOpsRate)
        .filter(FinOpsRate.organization_id == user.organization_id)
        .order_by(FinOpsRate.created_at.desc())
        .all()
    )


@router.post("/rates", response_model=RateOut)
def create_rate(body: RateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "finops.rates", db)
    row = FinOpsRate(organization_id=user.organization_id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="finops.rate.created",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=f"tarifa:{row.id}",
    )
    return row


@router.patch("/rates/{rate_id}", response_model=RateOut)
def patch_rate(
    rate_id: str,
    body: RatePatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.rates", db)
    row = (
        db.query(FinOpsRate)
        .filter(FinOpsRate.id == rate_id, FinOpsRate.organization_id == user.organization_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Tarifa no encontrada")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="finops.rate.updated",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=f"tarifa:{row.id}",
    )
    return row


@router.get("/values", response_model=list[ValueOut])
def list_values(
    opportunity_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    query = (
        db.query(FinOpsValueRecord)
        .filter(FinOpsValueRecord.organization_id == user.organization_id)
        .order_by(FinOpsValueRecord.created_at.desc())
    )
    if opportunity_id:
        query = query.filter(FinOpsValueRecord.opportunity_id == opportunity_id)
    return query.limit(200).all()


@router.post("/values", response_model=ValueOut)
def create_value(body: ValueIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "finops.manage", db)
    try:
        return svc.registrar_valor(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            **body.model_dump(),
        )
    except svc.FinOpsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/budgets", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "finops.budget", db)
    rows = (
        db.query(FinOpsBudget)
        .filter(FinOpsBudget.organization_id == user.organization_id)
        .order_by(FinOpsBudget.period_start.desc())
        .all()
    )
    return [svc.serialize_budget_detail(db, row) for row in rows]


@router.post("/budgets", response_model=BudgetOut)
def create_budget(body: BudgetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "finops.budget", db)
    row = FinOpsBudget(organization_id=user.organization_id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="finops.budget.created",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=f"presupuesto:{row.id}",
    )
    return svc.serialize_budget_detail(db, row)


@router.patch("/budgets/{budget_id}", response_model=BudgetOut)
def patch_budget(
    budget_id: str,
    body: BudgetPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.budget", db)
    row = (
        db.query(FinOpsBudget)
        .filter(FinOpsBudget.id == budget_id, FinOpsBudget.organization_id == user.organization_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="finops.budget.updated",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=f"presupuesto:{row.id}",
    )
    return svc.serialize_budget_detail(db, row)


@router.get("/drill-down", response_model=list[DrillDownNode])
def drill_down(
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    if work_plan_id:
        plan = (
            db.query(WorkPlan)
            .filter(WorkPlan.id == work_plan_id, WorkPlan.organization_id == user.organization_id)
            .first()
        )
        if not plan:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    if employee_id:
        employee = (
            db.query(AIEmployee)
            .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == user.organization_id)
            .first()
        )
        if not employee:
            raise HTTPException(status_code=404, detail="Empleado IA no encontrado")
    return svc.build_drill_down(db, user.organization_id, employee_id=employee_id, work_plan_id=work_plan_id)
