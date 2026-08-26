from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import CapabilityEventType
from app.orchestration_models import AIEmployee, Capability, EmployeeCapability
from app.services.authorization import get_capability, get_employee


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug_code(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _capability_out(cap: Capability) -> dict[str, Any]:
    return {
        "id": cap.id,
        "organization_id": cap.organization_id,
        "code": cap.code,
        "name": cap.name,
        "description": cap.description,
        "category": cap.category,
        "status": "ACTIVA" if cap.is_active else "INACTIVA",
        "risk_level": cap.risk_level.upper() if cap.risk_level else "LOW",
        "requires_approval": cap.requires_approval,
        "inputs": json.loads(cap.inputs_json) if cap.inputs_json else [],
        "outputs": json.loads(cap.outputs_json) if cap.outputs_json else [],
        "executor_types": json.loads(cap.executor_types_json) if cap.executor_types_json else [],
        "created_at": cap.created_at.isoformat() if cap.created_at else None,
        "updated_at": cap.updated_at.isoformat() if cap.updated_at else None,
    }


def list_capabilities(
    db: Session,
    org_id: str,
    *,
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    include_inactive: bool = True,
) -> list[dict[str, Any]]:
    q = db.query(Capability).filter(Capability.organization_id == org_id)
    if not include_inactive:
        q = q.filter(Capability.is_active.is_(True))
    if category:
        q = q.filter(Capability.category == category)
    if status == "ACTIVA":
        q = q.filter(Capability.is_active.is_(True))
    elif status == "INACTIVA":
        q = q.filter(Capability.is_active.is_(False))
    rows = q.order_by(Capability.name).all()
    if search:
        needle = search.lower()
        rows = [r for r in rows if needle in r.name.lower() or needle in r.code.lower()]
    return [_capability_out(r) for r in rows]


def get_capability_detail(db: Session, org_id: str, capability_id: str) -> dict[str, Any] | None:
    try:
        cap = get_capability(db, org_id, capability_id)
    except Exception:
        return None
    return _capability_out(cap)


def create_capability(
    db: Session,
    org_id: str,
    user_id: str,
    *,
    name: str,
    code: str | None = None,
    description: str | None = None,
    category: str | None = None,
    risk_level: str = "LOW",
    requires_approval: bool = False,
) -> dict[str, Any]:
    final_code = code or _slug_code(name)
    existing = (
        db.query(Capability)
        .filter(Capability.organization_id == org_id, Capability.code == final_code)
        .first()
    )
    if existing:
        return {"error": "Ya existe una capacidad con ese código"}
    cap = Capability(
        organization_id=org_id,
        code=final_code,
        name=name,
        description=description,
        category=category,
        risk_level=risk_level.lower(),
        requires_approval=requires_approval,
    )
    db.add(cap)
    db.commit()
    write_audit(db, action=CapabilityEventType.CREATED, organization_id=org_id, user_id=user_id, detail=final_code)
    return _capability_out(cap)


def update_capability(
    db: Session,
    org_id: str,
    user_id: str,
    capability_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    cap = get_capability(db, org_id, capability_id)
    if "name" in payload:
        cap.name = payload["name"]
    if "description" in payload:
        cap.description = payload["description"]
    if "category" in payload:
        cap.category = payload["category"]
    if "risk_level" in payload:
        cap.risk_level = str(payload["risk_level"]).lower()
    if "requires_approval" in payload:
        cap.requires_approval = bool(payload["requires_approval"])
    if "code" in payload and payload["code"] != cap.code:
        dup = (
            db.query(Capability)
            .filter(Capability.organization_id == org_id, Capability.code == payload["code"], Capability.id != cap.id)
            .first()
        )
        if dup:
            return {"error": "Ya existe una capacidad con ese código"}
        cap.code = payload["code"]
    cap.updated_at = _utcnow()
    db.commit()
    write_audit(db, action=CapabilityEventType.UPDATED, organization_id=org_id, user_id=user_id, detail=cap.code)
    return _capability_out(cap)


def set_capability_status(
    db: Session,
    org_id: str,
    user_id: str,
    capability_id: str,
    *,
    active: bool,
) -> dict[str, Any]:
    cap = get_capability(db, org_id, capability_id)
    cap.is_active = active
    cap.updated_at = _utcnow()
    db.commit()
    write_audit(
        db,
        action=CapabilityEventType.UPDATED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{cap.code}:{'ACTIVA' if active else 'INACTIVA'}",
    )
    return _capability_out(cap)


def list_employee_capabilities(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    assigned_ids = {
        link.capability_id
        for link in db.query(EmployeeCapability)
        .filter(EmployeeCapability.employee_id == employee.id, EmployeeCapability.is_active.is_(True))
        .all()
    }
    all_caps = list_capabilities(db, org_id, include_inactive=True)
    assigned = [c for c in all_caps if c["id"] in assigned_ids]
    available = [c for c in all_caps if c["id"] not in assigned_ids and c["status"] == "ACTIVA"]
    return {"assigned": assigned, "available": available}


def assign_capability(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    capability_id: str,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    cap = get_capability(db, org_id, capability_id)
    if not cap.is_active:
        return {"error": "La capacidad está inactiva"}
    link = (
        db.query(EmployeeCapability)
        .filter(EmployeeCapability.employee_id == employee.id, EmployeeCapability.capability_id == cap.id)
        .first()
    )
    if link:
        link.is_active = True
    else:
        db.add(EmployeeCapability(employee_id=employee.id, capability_id=cap.id, is_active=True))
    db.commit()
    write_audit(
        db,
        action=CapabilityEventType.ASSIGNED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{cap.code}",
    )
    return list_employee_capabilities(db, org_id, employee_id)


def remove_capability(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    capability_id: str,
) -> dict[str, Any]:
    employee = get_employee(db, org_id, employee_id)
    cap = get_capability(db, org_id, capability_id)
    link = (
        db.query(EmployeeCapability)
        .filter(EmployeeCapability.employee_id == employee.id, EmployeeCapability.capability_id == cap.id)
        .first()
    )
    if not link:
        return {"error": "Asignación no encontrada"}
    link.is_active = False
    db.commit()
    write_audit(
        db,
        action=CapabilityEventType.REMOVED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"{employee.code}:{cap.code}",
    )
    return list_employee_capabilities(db, org_id, employee_id)
