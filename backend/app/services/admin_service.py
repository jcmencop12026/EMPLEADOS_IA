from __future__ import annotations

import json
import secrets
import string
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import Organization, Permission, Role, RolePermission, User
from app.permissions import SYSTEM_ROLE_CODES, is_system_role
from app.security import hash_password

USER_STATUS_ACTIVE = "ACTIVE"
USER_STATUS_INACTIVE = "INACTIVE"
USER_STATUS_BLOCKED = "BLOCKED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_timezone(tz: str) -> None:
    try:
        ZoneInfo(tz)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Zona horaria no válida") from exc


def _generate_temp_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_user_in_org(db: Session, user_id: str, org_id: str) -> User:
    row = db.query(User).filter(User.id == user_id, User.organization_id == org_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return row


def get_role_for_org(db: Session, role_code: str, org_id: str) -> Role:
    role = (
        db.query(Role)
        .filter(
            Role.code == role_code,
            Role.is_active.is_(True),
            or_(Role.organization_id.is_(None), Role.organization_id == org_id),
        )
        .first()
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol no válido para la organización")
    return role


def list_users(db: Session, org_id: str, *, q: str | None = None, status_filter: str | None = None) -> list[User]:
    query = db.query(User).filter(User.organization_id == org_id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like), User.full_name.ilike(like)))
    if status_filter:
        query = query.filter(User.status == status_filter)
    return query.order_by(User.username.asc()).all()


def create_user(
    db: Session,
    *,
    org_id: str,
    actor_id: str,
    username: str,
    password: str,
    role: str,
    email: str | None,
    full_name: str | None,
) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya existe")
    get_role_for_org(db, role, org_id)
    row = User(
        organization_id=org_id,
        username=username.strip(),
        password_hash=hash_password(password),
        email=email.strip() if email else None,
        full_name=full_name.strip() if full_name else None,
        role=role,
        status=USER_STATUS_ACTIVE,
        is_active=True,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        action="admin.user.created",
        organization_id=org_id,
        user_id=actor_id,
        detail=json.dumps({"resource_id": row.id, "username": row.username}, ensure_ascii=False),
    )
    return row


def update_user(
    db: Session,
    *,
    user: User,
    actor_id: str,
    email: str | None = None,
    full_name: str | None = None,
    role: str | None = None,
) -> User:
    if role is not None:
        get_role_for_org(db, role, user.organization_id)
        user.role = role
    if email is not None:
        user.email = email.strip() or None
    if full_name is not None:
        user.full_name = full_name.strip() or None
    user.updated_by_id = actor_id
    user.updated_at = _utcnow()
    db.commit()
    db.refresh(user)
    write_audit(
        db,
        action="admin.user.updated",
        organization_id=user.organization_id,
        user_id=actor_id,
        detail=json.dumps({"resource_id": user.id, "username": user.username}, ensure_ascii=False),
    )
    return user


def set_user_status(db: Session, *, user: User, actor_id: str, status_value: str) -> User:
    if status_value not in (USER_STATUS_ACTIVE, USER_STATUS_INACTIVE, USER_STATUS_BLOCKED):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado no válido")
    user.status = status_value
    user.is_active = status_value == USER_STATUS_ACTIVE
    user.updated_by_id = actor_id
    user.updated_at = _utcnow()
    db.commit()
    db.refresh(user)
    action = "admin.user.activated" if status_value == USER_STATUS_ACTIVE else "admin.user.deactivated"
    if status_value == USER_STATUS_BLOCKED:
        action = "admin.user.deactivated"
    write_audit(
        db,
        action=action,
        organization_id=user.organization_id,
        user_id=actor_id,
        detail=json.dumps({"resource_id": user.id, "status": status_value}, ensure_ascii=False),
    )
    return user


def reset_user_password(db: Session, *, user: User, actor_id: str, new_password: str | None = None) -> str:
    temp = new_password or _generate_temp_password()
    user.password_hash = hash_password(temp)
    user.updated_by_id = actor_id
    user.updated_at = _utcnow()
    db.commit()
    write_audit(
        db,
        action="admin.user.password_reset",
        organization_id=user.organization_id,
        user_id=actor_id,
        detail=json.dumps({"resource_id": user.id, "username": user.username}, ensure_ascii=False),
    )
    return temp


def list_roles(db: Session, org_id: str) -> list[Role]:
    return (
        db.query(Role)
        .filter(or_(Role.organization_id.is_(None), Role.organization_id == org_id))
        .order_by(Role.is_system.desc(), Role.name.asc())
        .all()
    )


def create_role(
    db: Session,
    *,
    org_id: str,
    actor_id: str,
    code: str,
    name: str,
    description: str | None,
) -> Role:
    if is_system_role(code):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Código reservado para rol de sistema")
    exists = (
        db.query(Role)
        .filter(Role.code == code, or_(Role.organization_id == org_id, Role.organization_id.is_(None)))
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código de rol ya existe")
    row = Role(
        organization_id=org_id,
        code=code,
        name=name,
        description=description,
        is_system=False,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(db, action="admin.role.created", organization_id=org_id, user_id=actor_id, detail=row.code)
    return row


def update_role(db: Session, *, role: Role, org_id: str, actor_id: str, name: str | None, description: str | None, is_active: bool | None) -> Role:
    if role.is_system and role.organization_id is None:
        if name is not None and name != role.name:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede renombrar un rol de sistema")
        if is_active is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede desactivar un rol de sistema")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if is_active is not None and not role.is_system:
        role.is_active = is_active
    role.updated_at = _utcnow()
    db.commit()
    db.refresh(role)
    write_audit(db, action="admin.role.updated", organization_id=org_id, user_id=actor_id, detail=role.code)
    return role


def assign_role_permissions(db: Session, *, role: Role, org_id: str, actor_id: str, permission_codes: list[str]) -> Role:
    if role.is_system and role.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pueden modificar permisos de roles de sistema")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    perms = db.query(Permission).filter(Permission.code.in_(permission_codes)).all()
    if len(perms) != len(set(permission_codes)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Permiso no válido")
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    for perm in perms:
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.commit()
    write_audit(
        db,
        action="admin.role.permissions_updated",
        organization_id=org_id,
        user_id=actor_id,
        detail=json.dumps({"role": role.code, "permissions": permission_codes}, ensure_ascii=False),
    )
    db.refresh(role)
    return role


def permission_matrix(db: Session, org_id: str) -> dict:
    permissions = db.query(Permission).order_by(Permission.module, Permission.code).all()
    roles = list_roles(db, org_id)
    matrix: dict[str, dict[str, bool]] = {}
    for role in roles:
        codes = {
            p.code
            for p in db.query(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == role.id)
            .all()
        }
        matrix[role.id] = {perm.code: perm.code in codes for perm in permissions}
    return {
        "permissions": [
            {"code": p.code, "module": p.module, "description": p.description}
            for p in permissions
        ],
        "roles": [
            {
                "id": r.id,
                "code": r.code,
                "name": r.name,
                "is_system": r.is_system,
                "organization_id": r.organization_id,
            }
            for r in roles
        ],
        "matrix": matrix,
    }


def get_organization(db: Session, org_id: str) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organización no encontrada")
    return org


def update_organization(
    db: Session,
    *,
    org: Organization,
    actor_id: str,
    name: str | None,
    timezone: str | None,
) -> Organization:
    if name is not None:
        org.name = name.strip()
    if timezone is not None:
        _validate_timezone(timezone)
        org.timezone = timezone
    org.updated_at = _utcnow()
    db.commit()
    db.refresh(org)
    write_audit(
        db,
        action="admin.organization.updated",
        organization_id=org.id,
        user_id=actor_id,
        detail=json.dumps({"name": org.name, "timezone": org.timezone}, ensure_ascii=False),
    )
    return org


def get_org_config(org: Organization) -> dict:
    if not org.config_json:
        return default_org_config()
    try:
        data = json.loads(org.config_json)
        base = default_org_config()
        base.update(data)
        return base
    except json.JSONDecodeError:
        return default_org_config()


def default_org_config() -> dict:
    return {
        "language": "es",
        "timezone": "America/Bogota",
        "date_format": "DD/MM/YYYY",
        "time_format": "24h",
    }


def update_org_config(db: Session, *, org: Organization, actor_id: str, config: dict) -> dict:
    current = get_org_config(org)
    allowed = {"language", "timezone", "date_format", "time_format"}
    for key, value in config.items():
        if key in allowed:
            current[key] = value
    if "timezone" in config:
        _validate_timezone(str(config["timezone"]))
        org.timezone = str(config["timezone"])
    org.config_json = json.dumps(current, ensure_ascii=False)
    org.updated_at = _utcnow()
    db.commit()
    write_audit(
        db,
        action="admin.config.updated",
        organization_id=org.id,
        user_id=actor_id,
        detail=json.dumps({k: current[k] for k in allowed if k in config}, ensure_ascii=False),
    )
    return current


def security_summary(db: Session, org_id: str) -> dict:
    users = db.query(User).filter(User.organization_id == org_id).all()
    roles = list_roles(db, org_id)
    from app.models import AuditLog

    recent = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org_id,
            AuditLog.action.in_(
                [
                    "admin.user.created",
                    "admin.user.updated",
                    "admin.user.activated",
                    "admin.user.deactivated",
                    "admin.user.password_reset",
                    "admin.role.created",
                    "admin.role.updated",
                    "admin.organization.updated",
                    "admin.config.updated",
                    "auth.login",
                ]
            ),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "users_active": sum(1 for u in users if u.status == USER_STATUS_ACTIVE),
        "users_inactive": sum(1 for u in users if u.status == USER_STATUS_INACTIVE),
        "users_blocked": sum(1 for u in users if u.status == USER_STATUS_BLOCKED),
        "roles_total": len(roles),
        "recent_events": [
            {
                "action": row.action,
                "detail": row.detail,
                "user_id": row.user_id,
                "created_at": row.created_at.isoformat(),
            }
            for row in recent
        ],
    }
