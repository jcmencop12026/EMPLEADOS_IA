from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_factory import (
    EmployeeApprovalOut,
    EmployeeApprovalRequest,
    EmployeeCreateRequest,
    EmployeeOut,
    EmployeeRetireRequest,
    EmployeeRollbackRequest,
    EmployeeTestCaseCreateRequest,
    EmployeeTrainingRequest,
    EmployeeUpdateRequest,
    EmployeeVersionCreateRequest,
    TemplateOut,
)
from app.schemas_orchestration import ApprovalDecisionRequest, PlanResponse, RouteTaskRequest
from app.services import agent_factory, employee_lifecycle_service
from app.services.coordinator import route_task

router = APIRouter(prefix="/api/agent-factory", tags=["agent-factory"])


@router.get("/auditor-contract")
def auditor_contract(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "employee.view", db)
    return employee_lifecycle_service.auditor_contract()


@router.post("/coordinator/route", response_model=PlanResponse)
def coordinator_route(
    body: RouteTaskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "operations.execute", db)
    if body.auto_execute:
        check_permission(user, "operations.manage", db)
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
    check_permission(user, "employee.view", db)
    return agent_factory.list_employees(
        db, user.organization_id, status=lifecycle_status, specialty=specialty, capability=capability,
    )


@router.get("/employees/{employee_id}")
def get_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    detail = agent_factory.get_employee_detail(db, user.organization_id, employee_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    detail["lifecycle_phase"] = employee_lifecycle_service.lifecycle_phase(str(detail.get("lifecycle_status", "")))
    return detail


@router.get("/employees/{employee_id}/inventory")
def employee_inventory(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    inv = employee_lifecycle_service.build_inventory(db, user.organization_id, employee_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    return inv


@router.get("/employees/{employee_id}/health")
def employee_health(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    snap = employee_lifecycle_service.health_snapshot(db, user.organization_id, employee_id)
    if not snap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    return snap


@router.get("/employees/{employee_id}/validate")
def validate_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return employee_lifecycle_service.validate_configuration(db, user.organization_id, employee_id)


@router.post("/employees")
def create_employee(
    body: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.create", db)
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
    check_permission(user, "employee.edit", db)
    result = agent_factory.update_employee(
        db, user.organization_id, user.id, employee_id, body.model_dump(exclude_unset=True),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.get("/employees/{employee_id}/versions")
def list_versions(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return employee_lifecycle_service.list_versions(db, user.organization_id, employee_id)


@router.get("/employees/{employee_id}/versions/{version_num}")
def get_version(employee_id: str, version_num: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    detail = employee_lifecycle_service.get_version_detail(db, user.organization_id, employee_id, version_num)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión no encontrada")
    return detail


@router.post("/employees/{employee_id}/versions")
def create_version(
    employee_id: str,
    body: EmployeeVersionCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    result = employee_lifecycle_service.create_version(
        db, user.organization_id, user.id, employee_id,
        reason=body.reason, changed_fields=body.changed_fields,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/employees/{employee_id}/test-cases")
def list_test_cases(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return employee_lifecycle_service.list_test_cases(db, user.organization_id, employee_id)


@router.post("/employees/{employee_id}/test-cases")
def create_test_case(
    employee_id: str,
    body: EmployeeTestCaseCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    result = employee_lifecycle_service.create_test_case(
        db, user.organization_id, employee_id, body.model_dump(),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/test")
def test_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.test", db)
    result = agent_factory.run_employee_tests(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/certify")
def certify_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.certify", db)
    result = agent_factory.certify_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/request-approval")
def request_approval(
    employee_id: str,
    body: EmployeeApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    result = employee_lifecycle_service.request_approval(
        db, user.organization_id, user.id, employee_id,
        kind=body.kind, reason=body.reason, target_version=body.target_version,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/employees/{employee_id}/approvals", response_model=list[EmployeeApprovalOut])
def list_employee_approvals(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.view", db)
    rows = employee_lifecycle_service.list_employee_approvals(
        db, user.organization_id, employee_id, viewer_id=user.id,
    )
    if rows is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado")
    return rows


@router.post("/employees/{employee_id}/approvals/{approval_request_id}/decide")
def decide_employee_approval(
    employee_id: str,
    approval_request_id: str,
    body: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.approve", db)
    result = employee_lifecycle_service.decide_employee_approval(
        db,
        user.organization_id,
        user.id,
        employee_id,
        approval_request_id,
        decision=body.decision,
        comment=body.comment,
    )
    if result.get("error") == "Empleado no encontrado":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    if result.get("error") == "Aprobación de fábrica no encontrada para este empleado":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    if result.get("error"):
        code = status.HTTP_403_FORBIDDEN if "solicitante" in result["error"].lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/publish")
def publish_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.publish", db)
    result = employee_lifecycle_service.publish_with_guards(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        code = status.HTTP_403_FORBIDDEN if result.get("requires_approval") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=result)
    return result


@router.post("/employees/{employee_id}/activate")
def activate_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.activate", db)
    result = agent_factory.activate_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/pause")
def pause_employee(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.pause", db)
    result = agent_factory.pause_employee(db, user.organization_id, user.id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/retire")
def retire_employee(
    employee_id: str,
    body: EmployeeRetireRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.retire", db)
    result = employee_lifecycle_service.retire_employee(
        db, user.organization_id, user.id, employee_id, reason=body.reason,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/employees/{employee_id}/rollback")
def rollback_employee(
    employee_id: str,
    body: EmployeeRollbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.rollback", db)
    result = employee_lifecycle_service.rollback_to_version(
        db, user.organization_id, user.id, employee_id, body.target_version,
        reason=body.reason, force=body.force,
    )
    if result.get("error"):
        code = status.HTTP_403_FORBIDDEN if result.get("requires_approval") else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=result)
    return result


@router.post("/employees/{employee_id}/train")
def train_employee(
    employee_id: str,
    body: EmployeeTrainingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.train", db)
    result = employee_lifecycle_service.train_employee(
        db, user.organization_id, user.id, employee_id,
        training_type=body.training_type,
        reason=body.reason,
        source=body.source,
        config_delta=body.config_delta,
        approved_by_id=body.approved_by_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/employees/{employee_id}/metrics")
def employee_metrics(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    result = agent_factory.get_employee_metrics(db, user.organization_id, employee_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return agent_factory.list_templates(db)


@router.get("/capabilities")
def list_capabilities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return agent_factory.list_capabilities(db, user.organization_id)


@router.get("/tools")
def list_tools(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return agent_factory.list_tools(db, user.organization_id)
