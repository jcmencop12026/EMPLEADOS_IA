from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import ToolEventType, ToolPermission
from app.orchestration_models import AIEmployee, Capability, EmployeeToolGrant, Tool
from app.services.authorization import get_capability, get_employee, get_tool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug_code(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _tool_out(tool: Tool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "organization_id": tool.organization_id,
        "capability_id": tool.capability_id,
        "code": tool.code,
        "name": tool.name,
        "description": tool.description,
        "tool_type": tool.executor_type,
        "status": "ACTIVA" if tool.is_active else "INACTIVA",
        "risk_level": tool.risk_level.upper() if tool.risk_level else "LOW",
        "requires_approval": tool.requires_approval,
        "configuration": json.loads(tool.config_json) if tool.config_json else {},
        "timeout_seconds": tool.timeout_seconds,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
    }


def list_tools(
    db: Session,
    org_id: str,
    *,
    search: str | None = None,
    capability_id: str | None = None,
    status: str | None = None,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    q = db.query(Tool).filter(Tool.organization_id == org_id)
    if capability_id:
        q = q.filter(Tool.capability_id == capability_id)
    if not include_inactive:
        q = q.filter(Tool.is_active.is_(True))
    if status == "ACTIVA":
        q = q.filter(Tool.is_active.is_(True))
    elif status == "INACTIVA":
        q = q.filter(Tool.is_active.is_(False))
    rows = q.order_by(Tool.name).all()
    if search:
        needle = search.lower()
        rows = [r for r in rows if needle in r.name.lower() or needle in r.code.lower()]
    return [_tool_out(r) for r in rows]


def get_tool_detail(db: Session, org_id: str, tool_id: str) -> dict[str, Any] | None:
    try:
        tool = get_tool(db, org_id, tool_id)
    except Exception:
        return None
    return _tool_out(tool)


def create_tool(
    db: Session,
    org_id: str,
    user_id: str,
    *,
    name: str,
    capability_id: str,
    code: str | None = None,
    description: str | None = None,
    tool_type: str = "PYTHON",
    risk_level: str = "LOW",
    requires_approval: bool = False,
    configuration: dict | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    get_capability(db, org_id, capability_id)
    final_code = code or _slug_code(name)
    existing = db.query(Tool).filter(Tool.organization_id == org_id, Tool.code == final_code).first()
    if existing:
        return {"error": "Ya existe una herramienta con ese código"}
    tool = Tool(
        organization_id=org_id,
        capability_id=capability_id,
        code=final_code,
        name=name,
        description=description,
        executor_type=tool_type,
        risk_level=risk_level.lower(),
        requires_approval=requires_approval,
        config_json=json.dumps(configuration or {}, ensure_ascii=False),
        timeout_seconds=timeout_seconds,
    )
    db.add(tool)
    db.commit()
    write_audit(db, action=ToolEventType.CREATED, organization_id=org_id, user_id=user_id, detail=final_code)
    return _tool_out(tool)


def update_tool(
    db: Session,
    org_id: str,
    user_id: str,
    tool_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    tool = get_tool(db, org_id, tool_id)
    if "name" in payload:
        tool.name = payload["name"]
    if "description" in payload:
        tool.description = payload["description"]
    if "tool_type" in payload:
        tool.executor_type = payload["tool_type"]
    if "risk_level" in payload:
        tool.risk_level = str(payload["risk_level"]).lower()
    if "requires_approval" in payload:
        tool.requires_approval = bool(payload["requires_approval"])
    if "configuration" in payload:
        tool.config_json = json.dumps(payload["configuration"] or {}, ensure_ascii=False)
    if "timeout_seconds" in payload:
        tool.timeout_seconds = payload["timeout_seconds"]
    if "capability_id" in payload:
        get_capability(db, org_id, payload["capability_id"])
        tool.capability_id = payload["capability_id"]
    if "code" in payload and payload["code"] != tool.code:
        dup = (
            db.query(Tool)
            .filter(Tool.organization_id == org_id, Tool.code == payload["code"], Tool.id != tool.id)
            .first()
        )
        if dup:
            return {"error": "Ya existe una herramienta con ese código"}
        tool.code = payload["code"]
    tool.updated_at = _utcnow()
    db.commit()
    write_audit(db, action=ToolEventType.UPDATED, organization_id=org_id, user_id=user_id, detail=tool.code)
    return _tool_out(tool)


def set_tool_status(
    db: Session,
    org_id: str,
    user_id: str,
    tool_id: str,
    *,
    active: bool,
) -> dict[str, Any]:
    tool = get_tool(db, org_id, tool_id)
    tool.is_active = active
    tool.updated_at = _utcnow()
    db.commit()
    write_audit(
        db,
        action=ToolEventType.UPDATED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{tool.code}:{'ACTIVA' if active else 'INACTIVA'}",
    )
    return _tool_out(tool)


def list_employee_tools(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    grants = (
        db.query(EmployeeToolGrant, Tool)
        .join(Tool, Tool.id == EmployeeToolGrant.tool_id)
        .filter(EmployeeToolGrant.employee_id == employee.id, Tool.organization_id == org_id)
        .all()
    )
    assigned_ids = {tool.id for _, tool in grants}
    assigned = []
    for grant, tool in grants:
        item = _tool_out(tool)
        item["permission"] = grant.permission
        assigned.append(item)
    available = [t for t in list_tools(db, org_id, include_inactive=False) if t["id"] not in assigned_ids]
    return {"assigned": assigned, "available": available}


def assign_tool(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    tool_id: str,
    *,
    permission: str = ToolPermission.ALLOW,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    tool = get_tool(db, org_id, tool_id)
    if not tool.is_active:
        return {"error": "La herramienta está inactiva"}
    grant = (
        db.query(EmployeeToolGrant)
        .filter(EmployeeToolGrant.employee_id == employee.id, EmployeeToolGrant.tool_id == tool.id)
        .first()
    )
    if grant:
        grant.permission = permission
    else:
        db.add(EmployeeToolGrant(employee_id=employee.id, tool_id=tool.id, permission=permission))
    db.commit()
    write_audit(
        db,
        action=ToolEventType.ASSIGNED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{tool.code}:{permission}",
    )
    return list_employee_tools(db, org_id, employee_id)


def remove_tool(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    tool_id: str,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    tool = get_tool(db, org_id, tool_id)
    grant = (
        db.query(EmployeeToolGrant)
        .filter(EmployeeToolGrant.employee_id == employee.id, EmployeeToolGrant.tool_id == tool.id)
        .first()
    )
    if not grant:
        return {"error": "Asignación no encontrada"}
    db.delete(grant)
    db.commit()
    write_audit(
        db,
        action=ToolEventType.REMOVED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{tool.code}",
    )
    return list_employee_tools(db, org_id, employee_id)
