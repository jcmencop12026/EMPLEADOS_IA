from __future__ import annotations

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import ToolEventType, ToolPermission
from app.orchestration_models import (
    AIEmployee,
    Capability,
    EmployeeCapability,
    EmployeeKnowledgeSource,
    EmployeeToolGrant,
    KnowledgeSource,
    Tool,
)


class AuthorizationError(PermissionError):
    def __init__(self, message: str, *, audit_action: str | None = None):
        super().__init__(message)
        self.audit_action = audit_action


def _assert_same_org(entity_org: str, org_id: str, label: str) -> None:
    if entity_org != org_id:
        raise AuthorizationError(f"Acceso denegado: {label} pertenece a otra organización")


def get_employee(db: Session, org_id: str, employee_id: str) -> AIEmployee:
    employee = db.query(AIEmployee).filter(AIEmployee.id == employee_id).first()
    if not employee:
        raise AuthorizationError("Empleado no encontrado")
    _assert_same_org(employee.organization_id, org_id, "empleado")
    return employee


def get_capability(db: Session, org_id: str, capability_id: str) -> Capability:
    capability = db.query(Capability).filter(Capability.id == capability_id).first()
    if not capability:
        raise AuthorizationError("Capacidad no encontrada")
    _assert_same_org(capability.organization_id, org_id, "capacidad")
    return capability


def get_tool(db: Session, org_id: str, tool_id: str) -> Tool:
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise AuthorizationError("Herramienta no encontrada")
    _assert_same_org(tool.organization_id, org_id, "herramienta")
    return tool


def get_knowledge_source(db: Session, org_id: str, source_id: str) -> KnowledgeSource:
    source = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
    if not source:
        raise AuthorizationError("Fuente de conocimiento no encontrada")
    _assert_same_org(source.organization_id, org_id, "fuente de conocimiento")
    return source


def assert_employee_has_capability(
    db: Session,
    *,
    org_id: str,
    employee_id: str,
    capability_id: str,
) -> Capability:
    employee = get_employee(db, org_id, employee_id)
    capability = get_capability(db, org_id, capability_id)
    if not capability.is_active:
        raise AuthorizationError("Capacidad desactivada")
    link = (
        db.query(EmployeeCapability)
        .filter(
            EmployeeCapability.employee_id == employee.id,
            EmployeeCapability.capability_id == capability.id,
            EmployeeCapability.is_active.is_(True),
        )
        .first()
    )
    if not link:
        raise AuthorizationError("El empleado no tiene asignada esta capacidad")
    return capability


def assert_employee_tool_authorized(
    db: Session,
    *,
    org_id: str,
    employee_id: str,
    tool_id: str,
    capability_id: str | None = None,
    user_id: str | None = None,
) -> Tool:
    employee = get_employee(db, org_id, employee_id)
    tool = get_tool(db, org_id, tool_id)

    if not tool.is_active:
        raise AuthorizationError("Herramienta desactivada", audit_action=ToolEventType.DENIED)

    if capability_id:
        assert_employee_has_capability(db, org_id=org_id, employee_id=employee.id, capability_id=capability_id)
    elif tool.capability_id:
        assert_employee_has_capability(db, org_id=org_id, employee_id=employee.id, capability_id=tool.capability_id)

    grant = (
        db.query(EmployeeToolGrant)
        .filter(EmployeeToolGrant.employee_id == employee.id, EmployeeToolGrant.tool_id == tool.id)
        .first()
    )
    if not grant:
        if user_id:
            write_audit(
                db,
                action=ToolEventType.DENIED,
                organization_id=org_id,
                user_id=user_id,
                detail=f"Empleado {employee.id} sin herramienta {tool.code}",
            )
        raise AuthorizationError("El empleado no tiene autorización para esta herramienta", audit_action=ToolEventType.DENIED)

    if grant.permission == ToolPermission.DENY:
        if user_id:
            write_audit(
                db,
                action=ToolEventType.DENIED,
                organization_id=org_id,
                user_id=user_id,
                detail=f"Empleado {employee.id} DENY en herramienta {tool.code}",
            )
        raise AuthorizationError("Herramienta denegada para el empleado asignado", audit_action=ToolEventType.DENIED)

    return tool


def assert_employee_knowledge_access(
    db: Session,
    *,
    org_id: str,
    employee_id: str,
    knowledge_source_id: str,
) -> KnowledgeSource:
    get_employee(db, org_id, employee_id)
    source = get_knowledge_source(db, org_id, knowledge_source_id)
    if not source.is_active:
        raise AuthorizationError("Fuente de conocimiento desactivada")
    link = (
        db.query(EmployeeKnowledgeSource)
        .filter(
            EmployeeKnowledgeSource.employee_id == employee_id,
            EmployeeKnowledgeSource.knowledge_source_id == knowledge_source_id,
            EmployeeKnowledgeSource.is_active.is_(True),
        )
        .first()
    )
    if not link:
        raise AuthorizationError("El empleado no tiene asignada esta fuente de conocimiento")
    return source


def assert_employee_knowledge_access_batch(
    db: Session,
    *,
    org_id: str,
    employee_id: str,
    knowledge_source_ids: list[str],
) -> list[KnowledgeSource]:
    return [
        assert_employee_knowledge_access(
            db, org_id=org_id, employee_id=employee_id, knowledge_source_id=kid,
        )
        for kid in knowledge_source_ids
    ]
