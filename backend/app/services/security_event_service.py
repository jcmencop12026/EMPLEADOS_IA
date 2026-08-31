"""Eventos de seguridad — Bloque 1300."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.events.bus import EventMessage, publish
from app.security_models import SecurityEvent

ALERT_EVENT_TYPES = {
    "LOGIN_FALLIDO",
    "MFA_FALLIDO",
    "MFA_DESHABILITADO",
    "CAMBIO_PASSWORD",
    "SESION_REVOCADA",
    "BLOQUEO_TEMPORAL",
}


def log_security_event(
    db: Session,
    *,
    organization_id: str,
    event_type: str,
    user_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    commit: bool = False,
) -> None:
    db.add(
        SecurityEvent(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            detail=detail,
            ip_address=ip_address,
        )
    )
    if event_type in ALERT_EVENT_TYPES:
        publish(
            EventMessage(
                event_type="TENANT_SECURITY_EVENT",
                organization_id=organization_id,
                user_id=user_id,
                payload={"kind": event_type.lower(), "detail": detail},
            ),
            db,
        )
    if commit:
        db.commit()


def list_security_events(
    db: Session,
    *,
    organization_id: str,
    limit: int = 50,
    event_type: str | None = None,
) -> list[SecurityEvent]:
    q = db.query(SecurityEvent).filter(SecurityEvent.organization_id == organization_id)
    if event_type:
        q = q.filter(SecurityEvent.event_type == event_type)
    return q.order_by(SecurityEvent.created_at.desc()).limit(limit).all()
