from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_850 import CapabilityCreateRequest, CapabilityUpdateRequest
from app.services import capabilities_service

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("")
def list_capabilities(
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.view")
    return capabilities_service.list_capabilities(
        db, user.organization_id, search=search, category=category, status=status,
    )


@router.get("/employees/{employee_id}/assignments")
def employee_capability_assignments(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.view")
    return capabilities_service.list_employee_capabilities(db, user.organization_id, employee_id)


@router.post("/employees/{employee_id}/assign/{capability_id}")
def assign_capability(
    employee_id: str,
    capability_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.manage")
    result = capabilities_service.assign_capability(db, user.organization_id, user.id, employee_id, capability_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.delete("/employees/{employee_id}/assign/{capability_id}")
def remove_capability(
    employee_id: str,
    capability_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.manage")
    result = capabilities_service.remove_capability(db, user.organization_id, user.id, employee_id, capability_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/{capability_id}")
def get_capability(capability_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "capability.view")
    detail = capabilities_service.get_capability_detail(db, user.organization_id, capability_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capacidad no encontrada")
    return detail


@router.post("")
def create_capability(
    body: CapabilityCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.manage")
    result = capabilities_service.create_capability(
        db, user.organization_id, user.id,
        name=body.name, code=body.code, description=body.description,
        category=body.category, risk_level=body.risk_level, requires_approval=body.requires_approval,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.patch("/{capability_id}")
def update_capability(
    capability_id: str,
    body: CapabilityUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "capability.manage")
    result = capabilities_service.update_capability(
        db, user.organization_id, user.id, capability_id, body.model_dump(exclude_none=True),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/{capability_id}/activate")
def activate_capability(capability_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "capability.manage")
    return capabilities_service.set_capability_status(db, user.organization_id, user.id, capability_id, active=True)


@router.post("/{capability_id}/deactivate")
def deactivate_capability(capability_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "capability.manage")
    return capabilities_service.set_capability_status(db, user.organization_id, user.id, capability_id, active=False)
