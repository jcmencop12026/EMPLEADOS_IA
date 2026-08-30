"""Servicio SCIM — grupos (1380)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.scim_enums import PROTECTED_SCIM_ROLES, ScimAuditAction
from app.scim_models import ScimGroup, ScimGroupMember, ScimGroupRoleMapping, ScimUserResource
from app.services.scim_audit import log_scim_audit
from app.services.scim_patch import PROTECTED_GROUP_PATHS, ScimPatchError, apply_patch
from app.services.scim_response import group_to_scim
from app.services.scim_user_service import ScimUserError, _resolve_role_from_groups


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _members_payload(db: Session, group_id: str) -> list[dict]:
    rows = db.query(ScimGroupMember).filter(ScimGroupMember.group_id == group_id).all()
    out = []
    for m in rows:
        scim_user = db.query(ScimUserResource).filter(ScimUserResource.user_id == m.user_id).first()
        if scim_user:
            out.append({"value": scim_user.id, "display": scim_user.display_name or scim_user.user_name})
    return out


def get_group(db: Session, organization_id: str, group_id: str, *, base_url: str) -> dict:
    group = db.query(ScimGroup).filter(ScimGroup.id == group_id, ScimGroup.organization_id == organization_id).first()
    if not group:
        raise ScimUserError("Grupo no encontrado", status=404)
    return group_to_scim(group, _members_payload(db, group.id), base_url=base_url)


def list_groups(db: Session, organization_id: str, *, base_url: str, start_index: int = 1, count: int = 100, filters: dict | None = None) -> tuple[list[dict], int]:
    q = db.query(ScimGroup).filter(ScimGroup.organization_id == organization_id)
    if filters and "displayName" in filters:
        q = q.filter(ScimGroup.display_name == filters["displayName"])
    if filters and "externalId" in filters:
        q = q.filter(ScimGroup.external_id == filters["externalId"])
    total = q.count()
    rows = q.order_by(ScimGroup.created_at).offset(max(0, start_index - 1)).limit(count).all()
    return [group_to_scim(g, _members_payload(db, g.id), base_url=base_url) for g in rows], total


def create_group(db: Session, organization_id: str, payload: dict, *, base_url: str, token_id: str | None = None) -> dict:
    display_name = payload.get("displayName")
    if not display_name:
        raise ScimUserError("displayName es obligatorio", scim_type="invalidValue")
    external_id = payload.get("externalId")
    if external_id:
        dup = db.query(ScimGroup).filter(ScimGroup.organization_id == organization_id, ScimGroup.external_id == external_id).first()
        if dup:
            raise ScimUserError("externalId duplicado", status=409, scim_type="uniqueness")
    group = ScimGroup(
        organization_id=organization_id,
        external_id=external_id,
        display_name=display_name,
        active=payload.get("active", True),
    )
    db.add(group)
    db.flush()
    members = payload.get("members") or []
    _sync_members(db, organization_id, group, members, token_id=token_id)
    log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.GROUP_CREATE,
                   resource_type="Group", resource_id=group.id, result="EXITOSO")
    return group_to_scim(group, _members_payload(db, group.id), base_url=base_url)


def update_group(db: Session, organization_id: str, group_id: str, payload: dict, *, base_url: str, token_id: str | None = None) -> dict:
    group = db.query(ScimGroup).filter(ScimGroup.id == group_id, ScimGroup.organization_id == organization_id).first()
    if not group:
        raise ScimUserError("Grupo no encontrado", status=404)
    if "displayName" in payload:
        group.display_name = payload["displayName"]
    if "externalId" in payload:
        group.external_id = payload["externalId"]
    if "members" in payload:
        _sync_members(db, organization_id, group, payload["members"], token_id=token_id, replace=True)
    group.version += 1
    group.updated_at = _utcnow()
    db.flush()
    log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.GROUP_UPDATE,
                   resource_type="Group", resource_id=group.id, result="EXITOSO")
    return group_to_scim(group, _members_payload(db, group.id), base_url=base_url)


def patch_group(db: Session, organization_id: str, group_id: str, operations: list[dict], *, base_url: str, token_id: str | None = None) -> dict:
    group = db.query(ScimGroup).filter(ScimGroup.id == group_id, ScimGroup.organization_id == organization_id).first()
    if not group:
        raise ScimUserError("Grupo no encontrado", status=404)
    current = {"displayName": group.display_name, "externalId": group.external_id, "members": _members_payload(db, group.id)}
    try:
        patched = apply_patch(current, operations, protected=PROTECTED_GROUP_PATHS)
    except ScimPatchError as exc:
        raise ScimUserError(str(exc), status=400, scim_type="invalidSyntax") from exc
    return update_group(db, organization_id, group_id, patched, base_url=base_url, token_id=token_id)


def delete_group(db: Session, organization_id: str, group_id: str, *, token_id: str | None = None) -> None:
    group = db.query(ScimGroup).filter(ScimGroup.id == group_id, ScimGroup.organization_id == organization_id).first()
    if not group:
        raise ScimUserError("Grupo no encontrado", status=404)
    group.active = False
    db.query(ScimGroupMember).filter(ScimGroupMember.group_id == group.id).delete()
    log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.GROUP_DELETE,
                   resource_type="Group", resource_id=group.id, result="EXITOSO")


def _sync_members(db: Session, organization_id: str, group: ScimGroup, members: list, *, token_id: str | None, replace: bool = False) -> None:
    if replace:
        db.query(ScimGroupMember).filter(ScimGroupMember.group_id == group.id).delete()
    for m in members:
        scim_user_id = m.get("value") if isinstance(m, dict) else m
        scim_row = db.query(ScimUserResource).filter(
            ScimUserResource.id == scim_user_id,
            ScimUserResource.organization_id == organization_id,
        ).first()
        if not scim_row:
            continue
        user = db.query(User).filter(User.id == scim_row.user_id).first()
        if not user or user.role in PROTECTED_SCIM_ROLES:
            log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.PRIVILEGE_DENIED, result="RECHAZADO", detail="miembro protegido")
            continue
        exists = db.query(ScimGroupMember).filter(
            ScimGroupMember.group_id == group.id,
            ScimGroupMember.user_id == scim_row.user_id,
        ).first()
        if not exists:
            db.add(ScimGroupMember(group_id=group.id, user_id=scim_row.user_id, organization_id=organization_id))
            log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.MEMBERSHIP_ADD,
                           resource_type="Group", resource_id=group.id, result="EXITOSO", detail=scim_row.id)
        role = _resolve_role_from_groups(db, organization_id, [group.display_name])
        if role and role not in PROTECTED_SCIM_ROLES:
            user.role = role


def upsert_group_role_mapping(db: Session, organization_id: str, external_group: str, role_code: str) -> dict:
    if role_code in PROTECTED_SCIM_ROLES:
        raise ValueError("Rol no permitido en mapeo SCIM")
    row = db.query(ScimGroupRoleMapping).filter(
        ScimGroupRoleMapping.organization_id == organization_id,
        ScimGroupRoleMapping.external_group == external_group,
    ).first()
    if not row:
        row = ScimGroupRoleMapping(organization_id=organization_id, external_group=external_group, role_code=role_code)
        db.add(row)
    else:
        row.role_code = role_code
        row.is_active = True
    db.flush()
    return {"id": row.id, "external_group": row.external_group, "role_code": row.role_code}


def list_group_role_mappings(db: Session, organization_id: str) -> list[dict]:
    rows = db.query(ScimGroupRoleMapping).filter(
        ScimGroupRoleMapping.organization_id == organization_id,
        ScimGroupRoleMapping.is_active.is_(True),
    ).all()
    return [{"id": r.id, "external_group": r.external_group, "role_code": r.role_code} for r in rows]
