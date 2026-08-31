"""Recuperación de contraseña — Bloque 1300."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.models import User
from app.security_models import PasswordResetToken
from app.security import hash_password
from app.services.mfa_crypto import hash_reset_token
from app.services.security_event_service import log_security_event
from app.services.session_service import revoke_all_user_sessions


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def request_password_reset(db: Session, *, email_or_username: str) -> str | None:
    """Genera token si el usuario existe; retorna token plano o None."""
    identifier = email_or_username.strip()
    user = (
        db.query(User)
        .filter((User.username == identifier) | (User.email == identifier))
        .first()
    )
    if not user or not user.is_active or user.status != "ACTIVE":
        return None

    raw_token = secrets.token_urlsafe(32)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": _utcnow()})

    db.add(
        PasswordResetToken(
            user_id=user.id,
            organization_id=user.organization_id,
            token_hash=hash_reset_token(raw_token),
            expires_at=_utcnow() + timedelta(hours=1),
        )
    )
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="RECUPERACION_PASSWORD",
        detail="solicitud",
    )
    db.flush()
    return raw_token


def reset_password_with_token(db: Session, *, token: str, new_password: str) -> None:
    token_hash = hash_reset_token(token.strip())
    row = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > _utcnow(),
        )
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación no es válido o ha expirado.",
        )

    user = db.query(User).filter(User.id == row.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo restablecer la contraseña.")

    user.password_hash = hash_password(new_password)
    row.used_at = _utcnow()
    revoke_all_user_sessions(db, user.id, reason="password_reset")
    log_security_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="CAMBIO_PASSWORD",
        detail="recuperacion",
    )
    write_audit(
        db,
        action="auth.password_reset",
        organization_id=user.organization_id,
        user_id=user.id,
        commit=False,
    )
    db.flush()
