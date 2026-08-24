"""Validación central de destinatarios tenant-scoped para notificaciones (CODEX-820)."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import User

logger = logging.getLogger(__name__)


def validate_notification_recipient(
    db: Session,
    *,
    organization_id: str,
    recipient_user_id: str | None,
) -> bool:
    """True si el destinatario es válido para el tenant; False → DENY (no notificar)."""
    if not organization_id or not str(organization_id).strip():
        return False
    if not recipient_user_id:
        return True
    user = db.query(User).filter(User.id == recipient_user_id).first()
    if user is None:
        logger.warning(
            "notification_recipient_missing org=%s recipient=%s",
            organization_id,
            recipient_user_id,
        )
        return False
    if user.organization_id != organization_id:
        logger.warning(
            "notification_recipient_cross_tenant org=%s recipient=%s recipient_org=%s",
            organization_id,
            recipient_user_id,
            user.organization_id,
        )
        return False
    return True
