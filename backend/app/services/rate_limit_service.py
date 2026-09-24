"""Protección fuerza bruta y rate limiting — Bloque 1300."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.security_models import LoginAttempt
from app.services.security_event_service import log_security_event
from app.services.security_policy_service import get_or_create_policy


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _identifier(username: str, ip: str | None) -> str:
    user_key = username.strip().lower()
    ip_key = (ip or "unknown").strip()
    return f"{user_key}|{ip_key}"


def check_login_allowed(
    db: Session,
    *,
    username: str,
    organization_id: str,
    ip_address: str | None,
) -> None:
    policy = get_or_create_policy(db, organization_id)
    window_start = _utcnow() - timedelta(minutes=policy.lockout_minutes)
    identifier = _identifier(username, ip_address)
    failures = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= window_start,
        )
        .count()
    )
    if failures >= policy.login_max_attempts:
        log_security_event(
            db,
            organization_id=organization_id,
            event_type="BLOQUEO_TEMPORAL",
            detail=f"Intentos excesivos para {username.strip().lower()}",
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Espere unos minutos e intente nuevamente.",
        )


def record_login_attempt(
    db: Session,
    *,
    username: str,
    ip_address: str | None,
    success: bool,
) -> None:
    db.add(
        LoginAttempt(
            identifier=_identifier(username, ip_address),
            ip_address=ip_address,
            success=success,
        )
    )


_mfa_attempts: dict[str, list[datetime]] = {}
_recovery_attempts: dict[str, list[datetime]] = {}


def _prune_attempts(store: dict[str, list[datetime]], key: str, window_minutes: int) -> list[datetime]:
    cutoff = _utcnow() - timedelta(minutes=window_minutes)
    attempts = [ts for ts in store.get(key, []) if ts >= cutoff]
    store[key] = attempts
    return attempts


def check_mfa_rate_limit(*, user_id: str, ip_address: str | None, max_attempts: int = 10, window_minutes: int = 15) -> None:
    key = f"{user_id}|{ip_address or 'unknown'}"
    attempts = _prune_attempts(_mfa_attempts, key, window_minutes)
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de verificación MFA. Intente más tarde.",
        )
    attempts.append(_utcnow())
    _mfa_attempts[key] = attempts


def check_recovery_rate_limit(*, ip_address: str | None, max_attempts: int = 5, window_minutes: int = 60) -> None:
    key = ip_address or "unknown"
    attempts = _prune_attempts(_recovery_attempts, key, window_minutes)
    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes de recuperación. Intente más tarde.",
        )
    attempts.append(_utcnow())
    _recovery_attempts[key] = attempts
