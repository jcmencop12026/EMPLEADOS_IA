"""Identidad pública de login — sin autenticación (solo branding no sensible)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Organization
from app.services import admin_service as admin_svc

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/login-identity")
def login_identity(db: Session = Depends(get_db)) -> dict:
    """Branding configurado para pantalla de login (bootstrap org)."""
    org = db.query(Organization).order_by(Organization.created_at.asc()).first()
    if not org:
        return {
            "display_name": settings.bootstrap_org_name,
            "logo_url": None,
            "logo_compact_url": None,
            "accent_color": "#1d4ed8",
            "platform_name": "EIAAX",
            "has_configured_logo": False,
        }
    config = admin_svc.get_org_config(org)
    logo_url = config.get("enterprise_logo_url")
    logo_compact = config.get("enterprise_logo_compact_url")
    has_logo = bool(logo_url and str(logo_url).strip())
    return {
        "display_name": config.get("enterprise_display_name") or org.name,
        "logo_url": logo_url if has_logo else None,
        "logo_compact_url": logo_compact if has_logo else None,
        "accent_color": config.get("enterprise_accent_color") or "#1d4ed8",
        "platform_name": "EIAAX",
        "has_configured_logo": has_logo,
    }
