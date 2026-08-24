"""Catálogo de permisos y roles — CURSOR-840.

Modelo de autorización (runtime):
- Fuente de roles: tabla `roles` (org-específico prioriza sobre global de sistema).
- Fuente de permisos: tabla `role_permissions` vía `role_permission_codes()`.
- Bootstrap: `seed_permissions.bootstrap_permissions()` crea roles/permisos de sistema.
- Política: DENY BY DEFAULT / FAIL CLOSED — sin fallback permisivo en runtime.
"""
from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Permission, Role, RolePermission, User

logger = logging.getLogger(__name__)

EMPLOYEE_PERMISSIONS = {
    "employee.view",
    "employee.create",
    "employee.edit",
    "employee.test",
    "employee.certify",
    "employee.publish",
    "employee.activate",
    "employee.admin",
}

ADMIN_PERMISSIONS = {
    "admin.user.view",
    "admin.user.create",
    "admin.user.edit",
    "admin.user.activate",
    "admin.user.deactivate",
    "admin.user.reset_password",
    "admin.role.view",
    "admin.role.create",
    "admin.role.edit",
    "admin.role.assign_permissions",
    "admin.organization.view",
    "admin.organization.edit",
    "admin.config.view",
    "admin.config.edit",
    "admin.security.view",
}

OPERATIONS_PERMISSIONS = {
    "operations.view",
    "operations.execute",
}

AUDIT_PERMISSIONS = {
    "audit.view",
}

ALL_PERMISSIONS: dict[str, tuple[str, str]] = {
    "employee.view": ("Empleados IA", "Ver directorio de empleados"),
    "employee.create": ("Empleados IA", "Crear empleados"),
    "employee.edit": ("Empleados IA", "Editar empleados"),
    "employee.test": ("Empleados IA", "Ejecutar pruebas"),
    "employee.certify": ("Empleados IA", "Certificar empleados"),
    "employee.publish": ("Empleados IA", "Publicar empleados"),
    "employee.activate": ("Empleados IA", "Activar empleados"),
    "employee.admin": ("Empleados IA", "Administrar empleados"),
    "operations.view": ("Operaciones", "Ver ejecuciones y operaciones"),
    "operations.execute": ("Operaciones", "Ejecutar solicitudes"),
    "audit.view": ("Auditoría", "Ver registros de auditoría"),
    "admin.user.view": ("Administración", "Ver usuarios"),
    "admin.user.create": ("Administración", "Crear usuarios"),
    "admin.user.edit": ("Administración", "Editar usuarios"),
    "admin.user.activate": ("Administración", "Activar usuarios"),
    "admin.user.deactivate": ("Administración", "Desactivar usuarios"),
    "admin.user.reset_password": ("Administración", "Restablecer contraseña"),
    "admin.role.view": ("Administración", "Ver roles"),
    "admin.role.create": ("Administración", "Crear roles"),
    "admin.role.edit": ("Administración", "Editar roles"),
    "admin.role.assign_permissions": ("Administración", "Asignar permisos a roles"),
    "admin.organization.view": ("Administración", "Ver organización"),
    "admin.organization.edit": ("Administración", "Editar organización"),
    "admin.config.view": ("Administración", "Ver configuración"),
    "admin.config.edit": ("Administración", "Editar configuración"),
    "admin.security.view": ("Administración", "Ver panel de seguridad"),
}

SYSTEM_ROLE_CODES = {"admin", "operator", "viewer"}

PROTECTED_ASSIGNMENT_ROLE_CODES = {"superadmin", "platform_admin", "SUPERADMIN"}

# Referencia estática para seed/tests — NO usar como fuente runtime de permisos.
ROLE_PERMISSIONS_FALLBACK: dict[str, set[str]] = {
    "admin": EMPLOYEE_PERMISSIONS | ADMIN_PERMISSIONS | OPERATIONS_PERMISSIONS | AUDIT_PERMISSIONS,
    "operator": {
        "employee.view",
        "employee.create",
        "employee.edit",
        "employee.test",
        "operations.view",
        "operations.execute",
        "audit.view",
        "admin.organization.view",
        "admin.config.view",
    },
    "viewer": {
        "employee.view",
        "operations.view",
        "audit.view",
        "admin.organization.view",
    },
}


def is_role_strictly_active(role: Role) -> bool:
    """Solo True booleano inequívoco cuenta como activo."""
    return role.is_active is True


def find_role_candidates_for_user(db: Session, user: User) -> list[Role]:
    role_code = (user.role or "").strip()
    if not role_code:
        return []
    return (
        db.query(Role)
        .filter(
            Role.code == role_code,
            (Role.organization_id == user.organization_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc(), Role.created_at.asc())
        .all()
    )


def find_role_candidates_for_code(db: Session, role_code: str, org_id: str) -> list[Role]:
    code = (role_code or "").strip()
    if not code:
        return []
    return (
        db.query(Role)
        .filter(
            Role.code == code,
            (Role.organization_id == org_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc(), Role.created_at.asc())
        .all()
    )


def resolve_authoritative_role(db: Session, user: User) -> Role | None:
    """Resuelve un único rol autoritativo o None (ambigüedad/inactivo → DENY)."""
    candidates = find_role_candidates_for_user(db, user)
    if not candidates:
        return None

    org_roles = [r for r in candidates if r.organization_id == user.organization_id]
    if org_roles:
        if len(org_roles) > 1:
            logger.warning("roles_ambiguous org=%s code=%s count=%s", user.organization_id, user.role, len(org_roles))
            return None
        role = org_roles[0]
        return role if is_role_strictly_active(role) else None

    global_roles = [r for r in candidates if r.organization_id is None]
    if len(global_roles) != 1:
        logger.warning("roles_ambiguous_global code=%s count=%s", user.role, len(global_roles))
        return None
    role = global_roles[0]
    return role if is_role_strictly_active(role) else None


def resolve_role_for_assignable(db: Session, role_code: str, org_id: str) -> Role | None:
    candidates = find_role_candidates_for_code(db, role_code, org_id)
    if not candidates:
        return None
    org_roles = [r for r in candidates if r.organization_id == org_id]
    if org_roles:
        if len(org_roles) > 1:
            return None
        role = org_roles[0]
        return role if is_role_strictly_active(role) else None
    global_roles = [r for r in candidates if r.organization_id is None]
    if len(global_roles) != 1:
        return None
    role = global_roles[0]
    return role if is_role_strictly_active(role) else None


def find_role_record_for_user(db: Session, user: User) -> Role | None:
    """Compat: registro de rol sin validar activo (usar resolve_authoritative_role en runtime)."""
    candidates = find_role_candidates_for_user(db, user)
    if not candidates:
        return None
    org_roles = [r for r in candidates if r.organization_id == user.organization_id]
    if org_roles:
        return org_roles[0] if len(org_roles) == 1 else None
    global_roles = [r for r in candidates if r.organization_id is None]
    return global_roles[0] if len(global_roles) == 1 else None


def resolve_role_for_user(db: Session, user: User) -> Role | None:
    return resolve_authoritative_role(db, user)


def role_permission_codes(db: Session, role: Role) -> set[str]:
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    return {row[0] for row in rows}


def user_permissions(user: User, db: Session | None = None) -> set[str]:
    """DENY BY DEFAULT — permisos solo desde rol autoritativo en BD."""
    if db is None:
        return set()
    try:
        role = resolve_authoritative_role(db, user)
        if role is None:
            return set()
        return role_permission_codes(db, role)
    except Exception:
        logger.exception("role_permission_resolution_failed user=%s", user.id)
        return set()


def assert_permission_subset(actor: User, requested: set[str], db: Session, *, action: str) -> None:
    allowed = user_permissions(actor, db)
    extra = requested - allowed
    if extra:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No puede {action}: permisos no autorizados ({', '.join(sorted(extra))})",
        )


def assert_role_assignable(actor: User, role_code: str, org_id: str, db: Session) -> None:
    normalized = role_code.strip().lower()
    if normalized in PROTECTED_ASSIGNMENT_ROLE_CODES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol de plataforma no asignable")
    role = resolve_role_for_assignable(db, role_code, org_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol no válido para la organización")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol de otra organización")
    assert_permission_subset(actor, role_permission_codes(db, role), db, action="asignar rol")


def check_permission(user: User, permission: str, db: Session | None = None) -> None:
    if permission not in user_permissions(user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción.",
        )


def require_permission(permission: str):
    def checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        check_permission(user, permission, db)
        return user

    return checker


def is_system_role(code: str) -> bool:
    return code in SYSTEM_ROLE_CODES
