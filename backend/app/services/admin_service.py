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
from app.permissions import (
    SYSTEM_ROLE_CODES,
    assert_permission_subset,
    assert_role_assignable,
    is_system_role,
    resolve_authoritative_role,
    user_permissions,
)
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
        .order_by(Role.organization_id.is_(None).asc())
        .first()
    )
    if not role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol no válido para la organización")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol de otra organización")
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
    actor: User | None = None,
) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya existe")
    if actor:
        assert_role_assignable(actor, role, org_id, db)
    else:
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
    actor: User | None = None,
) -> User:
    if role is not None:
        if actor and actor.id == user.id and role != user.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puede auto-elevar su propio rol")
        if actor:
            assert_role_assignable(actor, role, user.organization_id, db)
        else:
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
    if user.id == actor_id and status_value != USER_STATUS_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puede desactivarse a sí mismo")
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


def assign_role_permissions(
    db: Session,
    *,
    role: Role,
    org_id: str,
    actor_id: str,
    permission_codes: list[str],
    actor: User | None = None,
) -> Role:
    if role.is_system and role.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pueden modificar permisos de roles de sistema")
    if role.organization_id and role.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")
    if actor:
        assert_permission_subset(actor, set(permission_codes), db, action="asignar permisos")
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


SCIM_RATE_LIMIT_NOTE = (
    "P2 conocido: límite de tasa SCIM en memoria (120 solicitudes/minuto por token). "
    "Limitación administrativa documentada; no afecta la operación normal de aprovisionamiento."
)


def _safe_subject_ref(value: str | None) -> str | None:
    if not value:
        return None
    trimmed = value.strip()
    if len(trimmed) <= 12:
        return trimmed
    return f"{trimmed[:8]}…"


def _identity_origin_for_user(db: Session, user: User) -> dict:
    from app.identity_models import IdentityProvider, UserExternalIdentity
    from app.security_models import UserSession

    link = (
        db.query(UserExternalIdentity, IdentityProvider)
        .join(IdentityProvider, IdentityProvider.id == UserExternalIdentity.provider_id)
        .filter(UserExternalIdentity.user_id == user.id, UserExternalIdentity.organization_id == user.organization_id)
        .first()
    )
    if link:
        ext, provider = link
        return {
            "source": "SSO",
            "provider_code": provider.code,
            "provider_name": provider.name,
            "external_subject_ref": _safe_subject_ref(ext.external_subject),
        }
    latest_session = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .order_by(UserSession.created_at.desc())
        .first()
    )
    if latest_session and (latest_session.auth_method or "").upper() == "SSO":
        provider_name = None
        provider_code = None
        if latest_session.identity_provider_id:
            provider = db.query(IdentityProvider).filter(IdentityProvider.id == latest_session.identity_provider_id).first()
            if provider:
                provider_name = provider.name
                provider_code = provider.code
        return {
            "source": "SSO",
            "provider_code": provider_code,
            "provider_name": provider_name,
            "external_subject_ref": None,
        }
    return {
        "source": "LOCAL",
        "provider_code": None,
        "provider_name": None,
        "external_subject_ref": None,
    }


def _mfa_overview_for_user(db: Session, user: User) -> dict:
    from app.security_models import UserMfaSettings
    from app.services.mfa_service import mfa_status
    from app.services.security_policy_service import get_or_create_policy, is_mfa_required_for_user

    status = mfa_status(db, user)
    settings_row = db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user.id).first()
    policy = get_or_create_policy(db, user.organization_id)
    return {
        "enabled": bool(status["enabled"]),
        "enrollment_pending": bool(status["enrollment_pending"]),
        "confirmed_at": status["confirmed_at"],
        "updated_at": settings_row.updated_at if settings_row else None,
        "mfa_required_by_policy": is_mfa_required_for_user(db, user),
        "policy_mfa_mode": policy.mfa_mode,
        "allowed_method": "TOTP",
    }


def _provision_overview_for_user(db: Session, user: User) -> dict:
    from app.scim_models import ScimUserResource

    scim = db.query(ScimUserResource).filter(ScimUserResource.user_id == user.id).first()
    if scim:
        return {
            "status": scim.provision_status,
            "external_id": scim.external_id,
            "scim_resource_id": scim.id,
            "updated_at": scim.updated_at,
        }
    return {
        "status": "MANUAL",
        "external_id": None,
        "scim_resource_id": None,
        "updated_at": None,
    }


def _role_name_for_user(db: Session, user: User) -> str | None:
    role = resolve_authoritative_role(db, user)
    return role.name if role else user.role


def list_users_overview(
    db: Session,
    org_id: str,
    *,
    q: str | None = None,
    status_filter: str | None = None,
) -> list[dict]:
    org = get_organization(db, org_id)
    users = list_users(db, org_id, q=q, status_filter=status_filter)
    out: list[dict] = []
    for user in users:
        out.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "role_name": _role_name_for_user(db, user),
                "status": user.status,
                "is_active": user.is_active,
                "organization_id": user.organization_id,
                "organization_name": org.name,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "mfa": _mfa_overview_for_user(db, user),
                "identity_origin": _identity_origin_for_user(db, user),
                "provisioning": _provision_overview_for_user(db, user),
            }
        )
    return out


def _user_audit_entries(db: Session, org_id: str, target_user: User, limit: int = 30) -> list[dict]:
    from app.identity_models import IdentityLoginAudit
    from app.models import AuditLog
    from app.scim_models import ScimAuditLog, ScimUserResource
    from app.security_models import SecurityEvent

    entries: list[dict] = []
    for row in (
        db.query(IdentityLoginAudit)
        .filter(
            IdentityLoginAudit.organization_id == org_id,
            IdentityLoginAudit.user_id == target_user.id,
        )
        .order_by(IdentityLoginAudit.created_at.desc())
        .limit(limit)
    ):
        entries.append(
            {
                "stream": "identidad",
                "action": f"login.{row.login_method.lower()}",
                "result": row.result,
                "actor_id": row.user_id,
                "organization_id": row.organization_id,
                "detail": row.detail,
                "correlation_id": None,
                "created_at": row.created_at,
            }
        )
    for row in (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.organization_id == org_id,
            SecurityEvent.user_id == target_user.id,
        )
        .order_by(SecurityEvent.created_at.desc())
        .limit(limit)
    ):
        entries.append(
            {
                "stream": "seguridad",
                "action": row.event_type,
                "result": "OK",
                "actor_id": row.user_id,
                "organization_id": row.organization_id,
                "detail": row.detail,
                "correlation_id": None,
                "created_at": row.created_at,
            }
        )
    resource_hint = target_user.id
    for row in (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org_id,
            or_(
                AuditLog.user_id == target_user.id,
                AuditLog.detail.ilike(f"%{resource_hint}%"),
            ),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ):
        entries.append(
            {
                "stream": "auditoria",
                "action": row.action,
                "result": "OK",
                "actor_id": row.user_id,
                "organization_id": row.organization_id,
                "detail": row.detail,
                "correlation_id": None,
                "created_at": row.created_at,
            }
        )
    scim = db.query(ScimUserResource).filter(ScimUserResource.user_id == target_user.id).first()
    if scim:
        for row in (
            db.query(ScimAuditLog)
            .filter(
                ScimAuditLog.organization_id == org_id,
                ScimAuditLog.resource_id == scim.id,
            )
            .order_by(ScimAuditLog.created_at.desc())
            .limit(limit)
        ):
            entries.append(
                {
                    "stream": "scim",
                    "action": row.action,
                    "result": row.result,
                    "actor_id": None,
                    "organization_id": row.organization_id,
                    "detail": row.detail,
                    "correlation_id": row.correlation_id,
                    "created_at": row.created_at,
                }
            )
    entries.sort(key=lambda item: item["created_at"], reverse=True)
    return entries[:limit]


def get_user_identity_detail(db: Session, org_id: str, user_id: str) -> dict:
    from app.services.session_service import list_user_sessions

    target = get_user_in_org(db, user_id, org_id)
    org = get_organization(db, org_id)
    role = resolve_authoritative_role(db, target)
    perms = sorted(user_permissions(target, db))
    permissions_effective = [
        {
            "code": code,
            "source": "role",
            "role_code": role.code if role else target.role,
            "organization_id": org_id,
        }
        for code in perms
    ]
    sessions = list_user_sessions(db, target.id)
    scim_events: list[dict] = []
    provision = _provision_overview_for_user(db, target)
    if provision.get("scim_resource_id"):
        from app.scim_models import ScimAuditLog

        scim_events = [
            {
                "action": row.action,
                "result": row.result,
                "detail": row.detail,
                "correlation_id": row.correlation_id,
                "created_at": row.created_at.isoformat(),
            }
            for row in (
                db.query(ScimAuditLog)
                .filter(
                    ScimAuditLog.organization_id == org_id,
                    ScimAuditLog.resource_id == provision["scim_resource_id"],
                )
                .order_by(ScimAuditLog.created_at.desc())
                .limit(20)
            )
        ]
    return {
        "user": target,
        "organization_name": org.name,
        "role_name": _role_name_for_user(db, target),
        "mfa": _mfa_overview_for_user(db, target),
        "identity_origin": _identity_origin_for_user(db, target),
        "provisioning": provision,
        "permissions_effective": permissions_effective,
        "sessions": [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "created_at": s.created_at,
                "last_activity_at": s.last_activity_at,
                "expires_at": s.expires_at,
                "mfa_verified": s.mfa_verified,
                "auth_method": s.auth_method,
            }
            for s in sessions
        ],
        "audit_entries": _user_audit_entries(db, org_id, target),
        "scim_user_events": scim_events,
    }


def security_summary(db: Session, org_id: str) -> dict:
    users = db.query(User).filter(User.organization_id == org_id).all()
    roles = list_roles(db, org_id)
    from app.models import AuditLog
    from app.security_models import UserMfaSettings
    from app.services.scim_audit import get_metrics

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
    mfa_enabled_count = (
        db.query(UserMfaSettings)
        .filter(UserMfaSettings.organization_id == org_id, UserMfaSettings.enabled.is_(True))
        .count()
    )
    return {
        "users_active": sum(1 for u in users if u.status == USER_STATUS_ACTIVE),
        "users_inactive": sum(1 for u in users if u.status == USER_STATUS_INACTIVE),
        "users_blocked": sum(1 for u in users if u.status == USER_STATUS_BLOCKED),
        "roles_total": len(roles),
        "mfa_enabled_count": mfa_enabled_count,
        "scim_metrics": get_metrics(db, org_id),
        "scim_rate_limit_note": SCIM_RATE_LIMIT_NOTE,
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
