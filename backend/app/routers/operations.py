from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.orchestration_models import ApprovalRequest, EmployeeTask, FinOpsRecord, WorkEvent, WorkPlan
from app.permissions import check_permission
from app.schemas_operations import (
    OperationActivityOut,
    OperationApprovalOut,
    OperationDetailOut,
    OperationExecutionOut,
    OperationItemOut,
    OperationResultOut,
    OperationSummaryOut,
    OperationTaskOut,
    OperationUpdateRequest,
)
from app.schemas_orchestration import ApprovalDecisionRequest, ApprovalOut, ExecutionOut, PlanResponse, WorkEventOut
from app.services import agent_factory
from app.services import operations_center
from app.services.coordinator import decide_approval, execute_plan

router = APIRouter(prefix="/api/operations", tags=["operations"])


def _not_found(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/summary", response_model=OperationSummaryOut)
def operations_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    return operations_center.get_summary(db, user.organization_id)


@router.get("/center", response_model=list[OperationItemOut])
def operations_center_list(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    employee_id: str | None = None,
    prioridad: str | None = None,
    proceso: str | None = None,
    bucket: str | None = None,
    vencimiento_filtro: str | None = None,
    orden: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "operations.view")
    return operations_center.list_operations(
        db,
        user.organization_id,
        search=search,
        status=status_filter,
        employee_id=employee_id,
        prioridad=prioridad,
        proceso=proceso,
        bucket=bucket,
        vencimiento_filtro=vencimiento_filtro,
        orden=orden,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get("/center/{plan_id}", response_model=OperationDetailOut)
def operations_center_detail(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.get_operation_detail(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.patch("/center/{plan_id}", response_model=OperationDetailOut)
def operations_center_update(
    plan_id: str,
    body: OperationUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "operations.manage")
    try:
        return operations_center.update_operation(
            db,
            organization_id=user.organization_id,
            plan_id=plan_id,
            prioridad=body.prioridad,
            employee_id=body.employee_id,
            vencimiento=body.vencimiento,
            sin_vencimiento=bool(body.sin_vencimiento),
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.get("/center/{plan_id}/tasks", response_model=list[OperationTaskOut])
def operations_center_tasks(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.list_operation_tasks(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/center/{plan_id}/executions", response_model=list[OperationExecutionOut])
def operations_center_executions(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.list_operation_executions(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/center/{plan_id}/approvals", response_model=list[OperationApprovalOut])
def operations_center_approvals(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.list_operation_approvals(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/center/{plan_id}/results", response_model=OperationResultOut)
def operations_center_results(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.get_operation_results(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.get("/center/{plan_id}/activity", response_model=list[OperationActivityOut])
def operations_center_activity(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    try:
        return operations_center.list_operation_activity(db, user.organization_id, plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


@router.post("/center/{plan_id}/cancel", response_model=OperationDetailOut)
def operations_center_cancel(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.cancel")
    try:
        return operations_center.cancel_operation(
            db, organization_id=user.organization_id, plan_id=plan_id, user_id=user.id
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.post("/center/{plan_id}/pause", response_model=OperationDetailOut)
def operations_center_pause(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.manage")
    try:
        return operations_center.pause_operation(db, organization_id=user.organization_id, plan_id=plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.post("/center/{plan_id}/resume", response_model=OperationDetailOut)
def operations_center_resume(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.manage")
    try:
        return operations_center.resume_operation(db, organization_id=user.organization_id, plan_id=plan_id)
    except LookupError as exc:
        raise _not_found(exc) from exc
    except ValueError as exc:
        raise _bad_request(exc) from exc


@router.post("/center/{plan_id}/run", response_model=PlanResponse)
def operations_center_run(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.manage")
    plan = operations_center.get_plan(db, user.organization_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="La operación no existe o no está disponible.")
    result = execute_plan(db, plan_id=plan_id, user_id=user.id)
    return PlanResponse(**result)


@router.get("/employees")
def list_employees(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    return agent_factory.list_employees(db, user.organization_id)


@router.get("/executions", response_model=list[ExecutionOut])
def list_executions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    rows = (
        db.query(WorkPlan)
        .filter(WorkPlan.organization_id == user.organization_id)
        .order_by(WorkPlan.created_at.desc())
        .limit(100)
        .all()
    )
    return rows


@router.get("/executions/{plan_id}", response_model=PlanResponse)
def get_execution(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    plan = (
        db.query(WorkPlan)
        .filter(WorkPlan.id == plan_id, WorkPlan.organization_id == user.organization_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).all()
    import json

    result = json.loads(plan.result_json) if plan.result_json else None
    return PlanResponse(
        plan_id=plan.id,
        correlation_id=plan.correlation_id,
        status=plan.status,
        objective=plan.objective,
        summary=plan.summary,
        confidence=plan.confidence,
        approval_status=plan.approval_status,
        error=plan.error,
        result=result,
        tasks=[
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "executor_type": t.executor_type,
                "confidence": t.confidence,
                "approval_status": t.approval_status,
            }
            for t in tasks
        ],
        started_at=plan.started_at.isoformat() if plan.started_at else None,
        completed_at=plan.completed_at.isoformat() if plan.completed_at else None,
    )


@router.post("/executions/{plan_id}/run", response_model=PlanResponse)
def run_execution(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.manage")
    plan = (
        db.query(WorkPlan)
        .filter(WorkPlan.id == plan_id, WorkPlan.organization_id == user.organization_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    result = execute_plan(db, plan_id=plan_id, user_id=user.id)
    return PlanResponse(**result)


@router.get("/approvals/pending", response_model=list[ApprovalOut])
def pending_approvals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    rows = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.organization_id == user.organization_id, ApprovalRequest.status == "PENDING")
        .order_by(ApprovalRequest.created_at.desc())
        .all()
    )
    return rows


@router.post("/approvals/{approval_id}/decide", response_model=PlanResponse)
def approval_decide(
    approval_id: str,
    body: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "operations.approve")
    result = decide_approval(
        db,
        approval_id=approval_id,
        organization_id=user.organization_id,
        user_id=user.id,
        decision=body.decision,
        comment=body.comment,
    )
    if result.get("error") and "plan_id" not in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return PlanResponse(**result)


@router.get("/events", response_model=list[WorkEventOut])
def list_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    rows = (
        db.query(WorkEvent)
        .filter(WorkEvent.organization_id == user.organization_id)
        .order_by(WorkEvent.created_at.desc())
        .limit(200)
        .all()
    )
    return rows


@router.get("/finops/{plan_id}")
def finops_for_plan(plan_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "operations.view")
    rows = (
        db.query(FinOpsRecord)
        .filter(FinOpsRecord.organization_id == user.organization_id, FinOpsRecord.work_plan_id == plan_id)
        .all()
    )
    return [
        {
            "id": r.id,
            "model_name": r.model_name,
            "provider": r.provider,
            "tokens_in": r.tokens_in,
            "tokens_out": r.tokens_out,
            "cost": r.cost,
            "duration_ms": r.duration_ms,
        }
        for r in rows
    ]
