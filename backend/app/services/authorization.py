from __future__ import annotations

from enum import StrEnum

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


class ExecutionDecision(StrEnum):
    """Resultado de la política de ejecución de herramientas.

    Precedencia: DENY > REQUIRES_APPROVAL > ALLOW
    """

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


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


def evaluate_tool_execution(
    db: Session,
    *,
    org_id: str,
    employee_id: str | None,
    tool_id: str | None,
    capability_id: str | None = None,
    user_id: str | None = None,
) -> tuple[ExecutionDecision, Tool | None, Capability | None]:
    """
    Única decisión de autorización para ejecutar una herramienta.

    Inputs: tenant, empleado, capability, tool, asignación/grant, flags requires_approval.
    No usa permisos de usuario/API como sustituto de política de tool.
    """
    if not employee_id or not tool_id:
        return ExecutionDecision.DENY, None, None

    employee = get_employee(db, org_id, employee_id)
    tool = get_tool(db, org_id, tool_id)

    if not tool.is_active:
        return ExecutionDecision.DENY, tool, None

    capability: Capability | None = None
    cap_id = capability_id or tool.capability_id
    if not cap_id:
        return ExecutionDecision.DENY, tool, None

    capability = get_capability(db, org_id, cap_id)
    if not capability.is_active:
        return ExecutionDecision.DENY, tool, capability

    cap_link = (
        db.query(EmployeeCapability)
        .filter(
            EmployeeCapability.employee_id == employee.id,
            EmployeeCapability.capability_id == capability.id,
            EmployeeCapability.is_active.is_(True),
        )
        .first()
    )
    if not cap_link:
        return ExecutionDecision.DENY, tool, capability

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
        return ExecutionDecision.DENY, tool, capability

    if grant.permission == ToolPermission.DENY:
        if user_id:
            write_audit(
                db,
                action=ToolEventType.DENIED,
                organization_id=org_id,
                user_id=user_id,
                detail=f"Empleado {employee.id} DENY en herramienta {tool.code}",
            )
        return ExecutionDecision.DENY, tool, capability

    requires_approval = (
        grant.permission == ToolPermission.REQUIRES_APPROVAL
        or capability.requires_approval
        or tool.requires_approval
    )
    if requires_approval:
        return ExecutionDecision.REQUIRES_APPROVAL, tool, capability

    return ExecutionDecision.ALLOW, tool, capability


def assert_employee_tool_authorized(
    db: Session,
    *,
    org_id: str,
    employee_id: str,
    tool_id: str,
    capability_id: str | None = None,
    user_id: str | None = None,
) -> Tool:
    decision, tool, _ = evaluate_tool_execution(
        db,
        org_id=org_id,
        employee_id=employee_id,
        tool_id=tool_id,
        capability_id=capability_id,
        user_id=user_id,
    )
    if decision == ExecutionDecision.DENY or tool is None:
        raise AuthorizationError(
            "El empleado no tiene autorización para esta herramienta",
            audit_action=ToolEventType.DENIED,
        )
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
