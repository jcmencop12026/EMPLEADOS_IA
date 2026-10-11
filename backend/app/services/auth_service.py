from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.config import settings
from app.events.bus import EventMessage, publish
from app.models import AuthLoginAttempt, User
from app.security import create_access_token, verify_password


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def invalidate_user_sessions(db: Session, user: User) -> None:
    user.token_version = int(user.token_version or 0) + 1
    user.updated_at = _utcnow()


def record_login_attempt(
    db: Session,
    *,
    username: str,
    user: User | None,
    success: bool,
    failure_reason: str | None = None,
) -> None:
    row = AuthLoginAttempt(
        username=username,
        user_id=user.id if user else None,
        organization_id=user.organization_id if user else None,
        success=success,
        failure_reason=failure_reason,
    )
    db.add(row)


def _is_locked(user: User) -> bool:
    if user.locked_until is None:
        return False
    return _as_utc(user.locked_until) > _utcnow()


def _clear_lock_if_expired(user: User) -> None:
    if user.locked_until and _as_utc(user.locked_until) <= _utcnow():
        user.locked_until = None
        user.failed_login_count = 0


def _register_failed_login(db: Session, user: User, username: str) -> None:
    user.failed_login_count = int(user.failed_login_count or 0) + 1
    if user.failed_login_count >= settings.login_max_failed_attempts:
        user.locked_until = _utcnow() + timedelta(minutes=settings.login_lockout_minutes)
        publish(
            EventMessage(
                event_type="TENANT_SECURITY_EVENT",
                organization_id=user.organization_id,
                user_id=user.id,
                payload={"kind": "account_locked", "username": username},
            ),
            db,
        )
    record_login_attempt(db, username=username, user=user, success=False, failure_reason="invalid_password")
    publish(
        EventMessage(
            event_type="TENANT_SECURITY_EVENT",
            organization_id=user.organization_id,
            user_id=user.id,
            payload={"kind": "invalid_login", "username": username},
        ),
        db,
    )
    write_audit(
        db,
        action="auth.login.failed",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=username,
    )


def authenticate_user(db: Session, username: str, password: str) -> tuple[User, str]:
    """Valida credenciales y emite token JWT con versión de sesión."""
    normalized = username.strip()
    user = db.query(User).filter(User.username == normalized).first()
    if not user:
        record_login_attempt(db, username=normalized, user=None, success=False, failure_reason="unknown_user")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    _clear_lock_if_expired(user)
    if _is_locked(user) or user.status == "BLOCKED":
        record_login_attempt(db, username=normalized, user=user, success=False, failure_reason="locked")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario bloqueado temporalmente")

    if not user.is_active or user.status != "ACTIVE":
        record_login_attempt(db, username=normalized, user=user, success=False, failure_reason="inactive")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o bloqueado")

    if not verify_password(password, user.password_hash):
        _register_failed_login(db, user, normalized)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = _utcnow()
    record_login_attempt(db, username=normalized, user=user, success=True)
    token = create_access_token(
        user.id,
        {"role": user.role, "org": user.organization_id, "tv": int(user.token_version or 0)},
    )
    write_audit(
        db,
        action="auth.login",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=user.username,
    )
    db.commit()
    return user, token


def logout_user(db: Session, user: User) -> None:
    invalidate_user_sessions(db, user)
    write_audit(
        db,
        action="auth.logout",
        organization_id=user.organization_id,
        user_id=user.id,
        detail=user.username,
    )
    db.commit()
