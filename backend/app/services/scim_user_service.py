"""Servicio SCIM — usuarios (1380)."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.scim_enums import PROTECTED_SCIM_ROLES, ScimAuditAction, ScimProvisionStatus
from app.scim_models import ScimConflict, ScimGroupMember, ScimGroupRoleMapping, ScimIdempotencyRecord, ScimUserResource
from app.security import hash_password
from app.services.scim_audit import log_scim_audit, record_scim_metric
from app.services.scim_patch import PROTECTED_USER_PATHS, ScimPatchError, apply_patch
from app.services.scim_response import user_to_scim
from app.services.session_service import revoke_all_user_sessions


class ScimUserError(ValueError):
    def __init__(self, message: str, *, status: int = 400, scim_type: str | None = None):
        super().__init__(message)
        self.status = status
        self.scim_type = scim_type


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_role_from_groups(db: Session, organization_id: str, group_names: list[str]) -> str | None:
    if not group_names:
        return None
    mappings = db.query(ScimGroupRoleMapping).filter(
        ScimGroupRoleMapping.organization_id == organization_id,
        ScimGroupRoleMapping.is_active.is_(True),
    ).all()
    names = {n.lower() for n in group_names}
    for m in mappings:
        if m.external_group.lower() in names and m.role_code not in PROTECTED_SCIM_ROLES:
            return m.role_code
    return None


def _record_conflict(db: Session, organization_id: str, conflict_type: str, detail: str, **kwargs) -> None:
    db.add(ScimConflict(
        organization_id=organization_id,
        conflict_type=conflict_type,
        resource_type=kwargs.get("resource_type"),
        external_id=kwargs.get("external_id"),
        detail=detail,
    ))
    record_scim_metric(db, organization_id, conflicts_delta=1)
    log_scim_audit(db, organization_id=organization_id, action=ScimAuditAction.CONFLICT, result="CONFLICTO", detail=detail)


def _is_protected_user(user: User) -> bool:
    return user.role in PROTECTED_SCIM_ROLES


def get_idempotent(db: Session, organization_id: str, key: str) -> dict | None:
    row = db.query(ScimIdempotencyRecord).filter(
        ScimIdempotencyRecord.organization_id == organization_id,
        ScimIdempotencyRecord.idempotency_key == key,
    ).first()
    if row and row.response_json:
        return json.loads(row.response_json)
    return None


def save_idempotent(db: Session, organization_id: str, key: str, resource_type: str, resource_id: str, response: dict) -> None:
    existing = db.query(ScimIdempotencyRecord).filter(
        ScimIdempotencyRecord.organization_id == organization_id,
        ScimIdempotencyRecord.idempotency_key == key,
    ).first()
    if existing:
        return
    db.add(ScimIdempotencyRecord(
        organization_id=organization_id,
        idempotency_key=key,
        resource_type=resource_type,
        resource_id=resource_id,
        response_json=json.dumps(response),
    ))


def _user_groups(db: Session, user_id: str) -> list[str]:
    rows = (
        db.query(ScimGroupMember)
        .filter(ScimGroupMember.user_id == user_id)
        .all()
    )
    from app.scim_models import ScimGroup
    ids = [r.group_id for r in rows]
    if not ids:
        return []
    groups = db.query(ScimGroup).filter(ScimGroup.id.in_(ids)).all()
    return [g.display_name for g in groups]


def get_user(db: Session, organization_id: str, scim_id: str, *, base_url: str) -> dict:
    row = db.query(ScimUserResource).filter(
        ScimUserResource.id == scim_id,
        ScimUserResource.organization_id == organization_id,
    ).first()
    if not row:
        raise ScimUserError("Usuario no encontrado", status=404)
    return user_to_scim(row, base_url=base_url, groups=_user_groups(db, row.user_id))


def list_users(
    db: Session, organization_id: str, *, base_url: str,
    start_index: int = 1, count: int = 100, filters: dict | None = None,
) -> tuple[list[dict], int]:
    q = db.query(ScimUserResource).filter(ScimUserResource.organization_id == organization_id)
    if filters:
        if "userName" in filters:
            q = q.filter(ScimUserResource.user_name == filters["userName"])
        if "externalId" in filters:
            q = q.filter(ScimUserResource.external_id == filters["externalId"])
        if "displayName" in filters:
            q = q.filter(ScimUserResource.display_name == filters["displayName"])
        if "active" in filters:
            if filters["active"]:
                q = q.filter(ScimUserResource.provision_status.in_(["PROVISIONADO", "ACTIVO"]))
            else:
                q = q.filter(ScimUserResource.provision_status.in_(["SUSPENDIDO", "DESACTIVADO"]))
    total = q.count()
    rows = q.order_by(ScimUserResource.created_at).offset(max(0, start_index - 1)).limit(count).all()
    return [user_to_scim(r, base_url=base_url, groups=_user_groups(db, r.user_id)) for r in rows], total


def create_user(
    db: Session, organization_id: str, payload: dict, *, base_url: str, token_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    if idempotency_key:
        cached = get_idempotent(db, organization_id, idempotency_key)
        if cached:
            return cached

    user_name = payload.get("userName")
    if not user_name:
        raise ScimUserError("userName es obligatorio", scim_type="invalidValue")
    external_id = payload.get("externalId")
    active = payload.get("active", True)

    if external_id:
        dup = db.query(ScimUserResource).filter(
            ScimUserResource.organization_id == organization_id,
            ScimUserResource.external_id == external_id,
        ).first()
        if dup:
            raise ScimUserError("externalId duplicado", status=409, scim_type="uniqueness")

    dup_un = db.query(ScimUserResource).filter(
        ScimUserResource.organization_id == organization_id,
        ScimUserResource.user_name == user_name,
    ).first()
    if dup_un:
        raise ScimUserError("userName duplicado", status=409, scim_type="uniqueness")

    email = None
    emails = payload.get("emails") or []
    if emails and isinstance(emails, list):
        email = emails[0].get("value") if isinstance(emails[0], dict) else str(emails[0])
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if existing and existing.organization_id != organization_id:
            _record_conflict(db, organization_id, "EMAIL_CROSS_TENANT", f"Email en otra org: {email}", external_id=external_id)
            raise ScimUserError("Conflicto de correo entre organizaciones", status=409, scim_type="uniqueness")

    display_name = payload.get("displayName") or (payload.get("name") or {}).get("formatted") or user_name
    role = "viewer"
    group_names = [g.get("display") or g.get("value") for g in (payload.get("groups") or []) if isinstance(g, dict)]
    mapped = _resolve_role_from_groups(db, organization_id, group_names)
    if mapped:
        role = mapped
    if role in PROTECTED_SCIM_ROLES:
        log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.PRIVILEGE_DENIED, result="RECHAZADO", detail=role)
        raise ScimUserError("Rol no permitido vía SCIM", status=403, scim_type="mutability")

    username = f"scim-{user_name}".lower().replace(" ", "-")[:75]
    if db.query(User).filter(User.username == username).first():
        username = f"{username}-{uuid.uuid4().hex[:6]}"

    user = User(
        organization_id=organization_id,
        username=username,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        email=email,
        full_name=display_name,
        role=role,
        status="ACTIVE" if active else "DISABLED",
        is_active=bool(active),
    )
    db.add(user)
    db.flush()

    status = ScimProvisionStatus.ACTIVO if active else ScimProvisionStatus.DESACTIVADO
    scim_row = ScimUserResource(
        organization_id=organization_id,
        user_id=user.id,
        external_id=external_id,
        user_name=user_name,
        display_name=display_name,
        emails_json=json.dumps(emails) if emails else None,
        provision_status=ScimProvisionStatus.PROVISIONADO if active else ScimProvisionStatus.DESACTIVADO,
    )
    if active:
        scim_row.provision_status = ScimProvisionStatus.ACTIVO
    db.add(scim_row)
    db.flush()

    record_scim_metric(db, organization_id, users_provisioned_delta=1, users_active_delta=1 if active else 0, users_deactivated_delta=0 if active else 1)
    log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.USER_CREATE,
                   resource_type="User", resource_id=scim_row.id, result="EXITOSO")

    result = user_to_scim(scim_row, base_url=base_url, groups=group_names)
    if idempotency_key:
        save_idempotent(db, organization_id, idempotency_key, "User", scim_row.id, result)
    return result


def update_user(db: Session, organization_id: str, scim_id: str, payload: dict, *, base_url: str, token_id: str | None = None) -> dict:
    row = db.query(ScimUserResource).filter(ScimUserResource.id == scim_id, ScimUserResource.organization_id == organization_id).first()
    if not row:
        raise ScimUserError("Usuario no encontrado", status=404)
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or _is_protected_user(user):
        raise ScimUserError("Cuenta protegida", status=403, scim_type="mutability")
    return _apply_user_payload(db, row, user, payload, base_url=base_url, token_id=token_id, action=ScimAuditAction.USER_UPDATE)


def patch_user(db: Session, organization_id: str, scim_id: str, operations: list[dict], *, base_url: str, token_id: str | None = None) -> dict:
    row = db.query(ScimUserResource).filter(ScimUserResource.id == scim_id, ScimUserResource.organization_id == organization_id).first()
    if not row:
        raise ScimUserError("Usuario no encontrado", status=404)
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or _is_protected_user(user):
        raise ScimUserError("Cuenta protegida", status=403, scim_type="mutability")
    current = {
        "userName": row.user_name,
        "externalId": row.external_id,
        "displayName": row.display_name,
        "active": row.provision_status in ("PROVISIONADO", "ACTIVO"),
        "emails": json.loads(row.emails_json) if row.emails_json else [],
    }
    try:
        patched = apply_patch(current, operations, protected=PROTECTED_USER_PATHS)
    except ScimPatchError as exc:
        raise ScimUserError(str(exc), status=400, scim_type="invalidSyntax") from exc
    return _apply_user_payload(db, row, user, patched, base_url=base_url, token_id=token_id, action=ScimAuditAction.USER_PATCH)


def _apply_user_payload(db: Session, row: ScimUserResource, user: User, payload: dict, *, base_url: str, token_id: str | None, action: str) -> dict:
    if "userName" in payload and payload["userName"] != row.user_name:
        dup = db.query(ScimUserResource).filter(
            ScimUserResource.organization_id == row.organization_id,
            ScimUserResource.user_name == payload["userName"],
            ScimUserResource.id != row.id,
        ).first()
        if dup:
            raise ScimUserError("userName duplicado", status=409, scim_type="uniqueness")
        row.user_name = payload["userName"]
    if "externalId" in payload:
        row.external_id = payload["externalId"]
    if "displayName" in payload:
        row.display_name = payload["displayName"]
        user.full_name = payload["displayName"]
    if "emails" in payload:
        row.emails_json = json.dumps(payload["emails"])
        emails = payload["emails"]
        if emails:
            user.email = emails[0].get("value") if isinstance(emails[0], dict) else str(emails[0])
    if "active" in payload:
        _set_active(db, row, user, bool(payload["active"]), token_id=token_id)
    row.version += 1
    row.updated_at = _utcnow()
    db.flush()
    log_scim_audit(db, organization_id=row.organization_id, token_id=token_id, action=action,
                   resource_type="User", resource_id=row.id, result="EXITOSO")
    return user_to_scim(row, base_url=base_url, groups=_user_groups(db, row.user_id))


def _set_active(db: Session, row: ScimUserResource, user: User, active: bool, *, token_id: str | None) -> None:
    if active:
        user.is_active = True
        user.status = "ACTIVE"
        row.provision_status = ScimProvisionStatus.ACTIVO
        log_scim_audit(db, organization_id=row.organization_id, token_id=token_id, action=ScimAuditAction.USER_REACTIVATE, resource_type="User", resource_id=row.id, result="EXITOSO")
        record_scim_metric(db, row.organization_id, users_active_delta=1, users_deactivated_delta=-1 if row.provision_status == ScimProvisionStatus.DESACTIVADO else 0)
    else:
        user.is_active = False
        user.status = "DISABLED"
        row.provision_status = ScimProvisionStatus.DESACTIVADO
        revoke_all_user_sessions(db, user.id, reason="scim_deprovision")
        log_scim_audit(db, organization_id=row.organization_id, token_id=token_id, action=ScimAuditAction.USER_DEACTIVATE, resource_type="User", resource_id=row.id, result="EXITOSO")
        record_scim_metric(db, row.organization_id, users_deactivated_delta=1, users_active_delta=-1)


def delete_user(db: Session, organization_id: str, scim_id: str, *, token_id: str | None = None) -> None:
    row = db.query(ScimUserResource).filter(ScimUserResource.id == scim_id, ScimUserResource.organization_id == organization_id).first()
    if not row:
        raise ScimUserError("Usuario no encontrado", status=404)
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or _is_protected_user(user):
        raise ScimUserError("Cuenta protegida", status=403, scim_type="mutability")
    _set_active(db, row, user, False, token_id=token_id)
