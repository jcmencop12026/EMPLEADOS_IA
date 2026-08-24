"""Catálogo de permisos y roles — CURSOR-840.

Modelo de autorización (runtime):
- Fuente de roles: tabla `roles` (org-específico prioriza sobre global de sistema).
- Fuente de permisos: tabla `role_permissions` vía `role_permission_codes()`.
- Bootstrap: `seed_permissions.bootstrap_permissions()` crea roles/permisos de sistema.
- Fallback hardcoded (`ROLE_PERMISSIONS_FALLBACK`): solo si el rol del usuario no existe en BD.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Permission, Role, RolePermission, User

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


def resolve_role_for_user(db: Session, user: User) -> Role | None:
    """Rol efectivo: prioriza rol de la organización sobre rol global de sistema."""
    return (
        db.query(Role)
        .filter(
            Role.code == user.role,
            Role.is_active.is_(True),
            (Role.organization_id == user.organization_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc())
        .first()
    )


def role_permission_codes(db: Session, role: Role) -> set[str]:
    rows = (
        db.query(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id == role.id)
        .all()
    )
    return {row[0] for row in rows}


def user_permissions(user: User, db: Session | None = None) -> set[str]:
    """
    Fuente de verdad en runtime: permisos del rol en BD (org > global).
    Fallback hardcoded solo si el rol no existe en BD (bootstrap / tests sin seed).
    """
    if db is not None:
        role = resolve_role_for_user(db, user)
        if role:
            return role_permission_codes(db, role)
    return ROLE_PERMISSIONS_FALLBACK.get(user.role, {"employee.view"})


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
    role = (
        db.query(Role)
        .filter(
            Role.code == role_code,
            Role.is_active.is_(True),
            (Role.organization_id == org_id) | (Role.organization_id.is_(None)),
        )
        .order_by(Role.organization_id.is_(None).asc())
        .first()
    )
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
