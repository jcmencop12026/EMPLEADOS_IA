from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.database import get_db
from app.models import User
from app.permissions import check_permission
from app.orchestration_models import ApprovalRequest, EmployeeTask, FinOpsRecord, WorkEvent, WorkPlan
from app.schemas_orchestration import ApprovalDecisionRequest, ApprovalOut, ExecutionOut, PlanResponse, WorkEventOut
from app.services import agent_factory
from app.services.coordinator import decide_approval, execute_plan

router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("/employees")
def list_employees(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return agent_factory.list_employees(db, user.organization_id)


@router.get("/executions", response_model=list[ExecutionOut])
def list_executions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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
    if result.get("error") == "Aprobación no encontrada":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    if result.get("error") and "plan_id" not in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return PlanResponse(**result)


@router.get("/events", response_model=list[WorkEventOut])
def list_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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
