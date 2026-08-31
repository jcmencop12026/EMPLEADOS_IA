"""Políticas de seguridad por organización — Bloque 1300."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import User
from app.security_models import OrganizationSecurityPolicy, UserMfaSettings


def get_or_create_policy(db: Session, organization_id: str) -> OrganizationSecurityPolicy:
    policy = (
        db.query(OrganizationSecurityPolicy)
        .filter(OrganizationSecurityPolicy.organization_id == organization_id)
        .first()
    )
    if policy:
        return policy
    policy = OrganizationSecurityPolicy(organization_id=organization_id)
    db.add(policy)
    db.flush()
    return policy


def parse_required_roles(raw: str | None) -> set[str]:
    if not raw:
        return set()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return {str(item).strip().lower() for item in data if str(item).strip()}
    except json.JSONDecodeError:
        pass
    return set()


def user_has_mfa_enabled(db: Session, user_id: str) -> bool:
    row = db.query(UserMfaSettings).filter(UserMfaSettings.user_id == user_id).first()
    return bool(row and row.enabled)


def is_mfa_required_for_user(db: Session, user: User) -> bool:
    policy = get_or_create_policy(db, user.organization_id)
    mode = (policy.mfa_mode or "OPCIONAL").upper()
    if mode == "DESACTIVADO":
        return False
    required_roles = parse_required_roles(policy.mfa_required_roles_json)
    if user.role and user.role.strip().lower() in required_roles:
        return True
    if mode == "OBLIGATORIO":
        return True
    if mode == "OPCIONAL":
        return user_has_mfa_enabled(db, user.id)
    return False


def update_policy(
    db: Session,
    *,
    organization_id: str,
    updates: dict,
) -> OrganizationSecurityPolicy:
    policy = get_or_create_policy(db, organization_id)
    if "mfa_mode" in updates and updates["mfa_mode"] is not None:
        policy.mfa_mode = str(updates["mfa_mode"]).upper()
    if "mfa_required_roles" in updates:
        roles = updates["mfa_required_roles"]
        policy.mfa_required_roles_json = json.dumps(roles) if roles is not None else None
    for field in (
        "session_duration_minutes",
        "max_active_sessions",
        "login_max_attempts",
        "lockout_minutes",
        "revoke_sessions_on_password_change",
        "excess_session_policy",
    ):
        if field in updates and updates[field] is not None:
            setattr(policy, field, updates[field])
    db.flush()
    return policy
