from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_850 import TestLabRunRequest
from app.services import test_lab_service

router = APIRouter(prefix="/api/test-lab", tags=["test-lab"])


@router.get("/runs")
def list_runs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "test_lab.view")
    return test_lab_service.list_test_runs(db, user.organization_id)


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "test_lab.view")
    detail = test_lab_service.get_test_run(db, user.organization_id, run_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    return detail


@router.post("/run")
def run_test(body: TestLabRunRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "test_lab.run")
    return test_lab_service.execute_test_lab(
        db,
        user.organization_id,
        user.id,
        employee_id=body.employee_id,
        task_description=body.task_description,
        context=body.context,
        capability_id=body.capability_id,
        tool_id=body.tool_id,
        knowledge_source_ids=body.knowledge_source_ids,
        auto_execute=body.auto_execute,
    )
