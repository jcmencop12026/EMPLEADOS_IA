from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_850 import ToolAssignRequest, ToolCreateRequest, ToolUpdateRequest
from app.services import tools_service

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
def list_tools(
    search: str | None = None,
    capability_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.view", db)
    return tools_service.list_tools(
        db, user.organization_id, search=search, capability_id=capability_id, status=status,
    )


@router.get("/employees/{employee_id}/assignments")
def employee_tool_assignments(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.view", db)
    return tools_service.list_employee_tools(db, user.organization_id, employee_id)


@router.post("/employees/{employee_id}/assign")
def assign_tool(
    employee_id: str,
    body: ToolAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.manage", db)
    result = tools_service.assign_tool(
        db, user.organization_id, user.id, employee_id, body.tool_id, permission=body.permission,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.delete("/employees/{employee_id}/assign/{tool_id}")
def remove_tool(
    employee_id: str,
    tool_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.manage", db)
    result = tools_service.remove_tool(db, user.organization_id, user.id, employee_id, tool_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.get("/{tool_id}")
def get_tool(tool_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "tool.view", db)
    detail = tools_service.get_tool_detail(db, user.organization_id, tool_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Herramienta no encontrada")
    return detail


@router.post("")
def create_tool(
    body: ToolCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.manage", db)
    result = tools_service.create_tool(
        db, user.organization_id, user.id,
        name=body.name, capability_id=body.capability_id, code=body.code,
        description=body.description, tool_type=body.tool_type, risk_level=body.risk_level,
        requires_approval=body.requires_approval, configuration=body.configuration,
        timeout_seconds=body.timeout_seconds,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.patch("/{tool_id}")
def update_tool(
    tool_id: str,
    body: ToolUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "tool.manage", db)
    result = tools_service.update_tool(
        db, user.organization_id, user.id, tool_id, body.model_dump(exclude_none=True),
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/{tool_id}/activate")
def activate_tool(tool_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "tool.manage", db)
    return tools_service.set_tool_status(db, user.organization_id, user.id, tool_id, active=True)


@router.post("/{tool_id}/deactivate")
def deactivate_tool(tool_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "tool.manage", db)
    return tools_service.set_tool_status(db, user.organization_id, user.id, tool_id, active=False)
