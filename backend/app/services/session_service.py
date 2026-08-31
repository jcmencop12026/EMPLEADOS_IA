"""Gestión de sesiones de usuario — Bloque 1300.

Estrategia de revocación:
- Cada login crea un registro `user_sessions` con UUID (`sid`).
- El JWT de acceso incluye `sid` y `type=access`.
- `get_current_user` valida que la sesión exista, no esté revocada y no haya expirado.
- Una consulta indexada por PK por request; sin lista negra global de JWT.
- Tokens legacy sin `sid` siguen aceptándose para compatibilidad, pero no son revocables.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.security_models import UserSession
from app.services.security_policy_service import get_or_create_policy


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_active(session: UserSession) -> bool:
    if session.revoked_at is not None:
        return False
    return _as_utc(session.expires_at) > _utcnow()


def list_active_sessions(db: Session, user_id: str) -> list[UserSession]:
    rows = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.created_at.asc())
        .all()
    )
    return [row for row in rows if _is_active(row)]


def count_active_sessions(db: Session, user_id: str) -> int:
    return len(list_active_sessions(db, user_id))


def create_session(
    db: Session,
    *,
    user: User,
    ip_address: str | None,
    user_agent: str | None,
    mfa_verified: bool,
    auth_method: str | None = None,
    identity_provider_id: str | None = None,
) -> UserSession:
    policy = get_or_create_policy(db, user.organization_id)
    active = list_active_sessions(db, user.id)
    if len(active) >= policy.max_active_sessions:
        if policy.excess_session_policy == "RECHAZAR_NUEVA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ha alcanzado el máximo de sesiones activas. Cierre otra sesión e intente nuevamente.",
            )
        oldest = active[0]
        revoke_session(db, oldest, reason="max_sessions_exceeded")

    expires_at = _utcnow() + timedelta(minutes=policy.session_duration_minutes)
    session = UserSession(
        user_id=user.id,
        organization_id=user.organization_id,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:300] or None,
        expires_at=expires_at,
        mfa_verified=mfa_verified,
        auth_method=auth_method,
        identity_provider_id=identity_provider_id,
    )
    db.add(session)
    db.flush()
    return session


def get_valid_session(db: Session, session_id: str) -> UserSession | None:
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not session or not _is_active(session):
        return None
    return session


def touch_session(db: Session, session: UserSession) -> None:
    now = _utcnow()
    if (_as_utc(now) - _as_utc(session.last_activity_at)).total_seconds() >= 300:
        session.last_activity_at = now
        db.flush()


def revoke_session(db: Session, session: UserSession, *, reason: str) -> None:
    if session.revoked_at is None:
        session.revoked_at = _utcnow()
        session.revoke_reason = reason[:120]
        db.flush()


def revoke_other_sessions(db: Session, user_id: str, keep_session_id: str, *, reason: str) -> int:
    revoked = 0
    for session in list_active_sessions(db, user_id):
        if session.id != keep_session_id:
            revoke_session(db, session, reason=reason)
            revoked += 1
    return revoked


def revoke_all_user_sessions(db: Session, user_id: str, *, reason: str, except_session_id: str | None = None) -> int:
    revoked = 0
    for session in list_active_sessions(db, user_id):
        if except_session_id and session.id == except_session_id:
            continue
        revoke_session(db, session, reason=reason)
        revoked += 1
    return revoked


def list_user_sessions(db: Session, user_id: str) -> list[UserSession]:
    rows = list_active_sessions(db, user_id)
    return sorted(rows, key=lambda s: _as_utc(s.last_activity_at), reverse=True)


def list_org_sessions(db: Session, organization_id: str, limit: int = 100) -> list[UserSession]:
    rows = (
        db.query(UserSession)
        .filter(UserSession.organization_id == organization_id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_activity_at.desc())
        .limit(limit * 2)
        .all()
    )
    active = [row for row in rows if _is_active(row)]
    return active[:limit]
