from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_factory import EmployeeCreateRequest, EmployeeOut, EmployeeUpdateRequest, TemplateOut
from app.schemas_orchestration import PlanResponse, RouteTaskRequest
from app.services import agent_factory
from app.services.coordinator import route_task

router = APIRouter(prefix="/api/agent-factory", tags=["agent-factory"])


@router.post("/coordinator/route", response_model=PlanResponse)
def coordinator_route(
    body: RouteTaskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = route_task(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        request=body.request,
        context=body.context,
        auto_execute=body.auto_execute,
    )
    return PlanResponse(**result)


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(
    lifecycle_status: str | None = Query(None, alias="status"),
    specialty: str | None = None,
    capability: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.view")
    return agent_factory.list_employees(
        db, user.organization_id, status=lifecycle_status, specialty=specialty, capability=capability,
    )


@router.get("/employees/{employee_id}")
def get_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view")
    detail = agent_factory.get_employee_detail(db, user.organization_id, employee_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    return detail


@router.post("/employees")
def create_employee(
    body: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.create")
    return agent_factory.create_employee(
        db, user.organization_id, user.id,
        name=body.name, specialty=body.specialty, role=body.role,
        objective=body.objective, template_code=body.template_code,
    )


@router.patch("/employees/{employee_id}")
def update_employee(
    employee_id: str,
    body: EmployeeUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit")
    result = agent_factory.update_employee(
        db, user.organization_id, user.id, employee_id, body.model_dump(exclude_none=True),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/test")
def test_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.test")
    result = agent_factory.run_employee_tests(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/certify")
def certify_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.certify")
    result = agent_factory.certify_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/publish")
def publish_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.publish")
    result = agent_factory.publish_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/activate")
def activate_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.activate")
    result = agent_factory.activate_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/pause")
def pause_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.admin")
    result = agent_factory.pause_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/employees/{employee_id}/metrics")
def employee_metrics(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view")
    result = agent_factory.get_employee_metrics(db, user.organization_id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view")
    return agent_factory.list_templates(db)


@router.get("/capabilities")
def list_capabilities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view")
    return agent_factory.list_capabilities(db, user.organization_id)


@router.get("/tools")
def list_tools(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view")
    return agent_factory.list_tools(db, user.organization_id)
