"""Autenticación y tokens SCIM (1380)."""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.identity_models import OrganizationIdentitySettings
from app.scim_enums import ScimAuditAction
from app.scim_models import ScimMetrics, ScimToken
from app.services.scim_audit import log_scim_audit, record_scim_metric

_scim_rate_store: dict[str, list[float]] = {}
SCIM_RATE_LIMIT = 120
SCIM_RATE_WINDOW_SEC = 60


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_scim_enabled(db: Session, organization_id: str) -> bool:
    row = db.query(OrganizationIdentitySettings).filter(
        OrganizationIdentitySettings.organization_id == organization_id
    ).first()
    return bool(row and row.scim_enabled)


def get_or_create_metrics(db: Session, organization_id: str) -> ScimMetrics:
    row = db.query(ScimMetrics).filter(ScimMetrics.organization_id == organization_id).first()
    if row:
        return row
    row = ScimMetrics(organization_id=organization_id)
    db.add(row)
    db.flush()
    return row


def create_token(db: Session, organization_id: str, *, name: str = "Token SCIM", expires_days: int | None = None) -> tuple[ScimToken, str]:
    settings = db.query(OrganizationIdentitySettings).filter(
        OrganizationIdentitySettings.organization_id == organization_id
    ).first()
    if settings:
        settings.scim_enabled = True
        settings.scim_prepared = True
    plain = secrets.token_urlsafe(40)
    row = ScimToken(
        organization_id=organization_id,
        name=name,
        token_hash=_hash_token(plain),
        token_prefix=plain[:8],
        expires_at=_utcnow() + timedelta(days=expires_days) if expires_days else None,
    )
    db.add(row)
    db.flush()
    log_scim_audit(db, organization_id=organization_id, token_id=row.id, action=ScimAuditAction.TOKEN_CREATE, result="EXITOSO")
    return row, plain


def rotate_token(db: Session, organization_id: str, token_id: str) -> tuple[ScimToken, str]:
    old = db.query(ScimToken).filter(
        ScimToken.id == token_id, ScimToken.organization_id == organization_id, ScimToken.revoked_at.is_(None)
    ).first()
    if not old:
        raise ValueError("Token no encontrado")
    old.revoked_at = _utcnow()
    new_row, plain = create_token(db, organization_id, name=f"Rotación de {old.name}")
    log_scim_audit(db, organization_id=organization_id, token_id=new_row.id, action=ScimAuditAction.TOKEN_ROTATE, result="EXITOSO", detail=token_id)
    return new_row, plain


def revoke_token(db: Session, organization_id: str, token_id: str) -> None:
    row = db.query(ScimToken).filter(ScimToken.id == token_id, ScimToken.organization_id == organization_id).first()
    if not row:
        raise ValueError("Token no encontrado")
    row.revoked_at = _utcnow()
    log_scim_audit(db, organization_id=organization_id, token_id=row.id, action=ScimAuditAction.TOKEN_REVOKE, result="EXITOSO")


def list_tokens(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = db.query(ScimToken).filter(ScimToken.organization_id == organization_id).order_by(ScimToken.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "token_prefix": r.token_prefix,
            "masked": f"{r.token_prefix}…",
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
            "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
            "active": r.revoked_at is None and (not r.expires_at or _ensure_aware(r.expires_at) > _utcnow()),
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def authenticate_scim_token(db: Session, token: str) -> ScimToken:
    token_hash = _hash_token(token)
    row = db.query(ScimToken).filter(ScimToken.token_hash == token_hash).first()
    if not row:
        raise ValueError("Token inválido")
    if row.revoked_at:
        raise ValueError("Token revocado")
    if row.expires_at and _ensure_aware(row.expires_at) < _utcnow():
        raise ValueError("Token expirado")
    if not is_scim_enabled(db, row.organization_id):
        raise ValueError("SCIM deshabilitado para la organización")
    row.last_used_at = _utcnow()
    return row


def check_scim_rate_limit(db: Session, *, organization_id: str, token_id: str) -> None:
    key = f"{organization_id}|{token_id}"
    now = time.time()
    window = [t for t in _scim_rate_store.get(key, []) if now - t < SCIM_RATE_WINDOW_SEC]
    if len(window) >= SCIM_RATE_LIMIT:
        record_scim_metric(db, organization_id, rate_limited_delta=1)
        log_scim_audit(db, organization_id=organization_id, token_id=token_id, action=ScimAuditAction.RATE_LIMITED, result="RECHAZADO")
        raise ValueError("RATE_LIMIT")
    window.append(now)
    _scim_rate_store[key] = window


def set_scim_enabled(db: Session, organization_id: str, enabled: bool) -> None:
    settings = db.query(OrganizationIdentitySettings).filter(
        OrganizationIdentitySettings.organization_id == organization_id
    ).first()
    if not settings:
        from app.services.identity_service import get_or_create_identity_settings
        settings = get_or_create_identity_settings(db, organization_id)
    settings.scim_enabled = enabled
    settings.scim_prepared = True
