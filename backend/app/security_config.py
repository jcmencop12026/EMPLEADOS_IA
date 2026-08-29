"""Validación de configuración sensible — hardening V1."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRET = "change-me-in-env-local-dev-only"
DEFAULT_BOOTSTRAP_ADMIN_PASSWORD = "Admin2026*"


def validate_security_settings(*, database_url: str, jwt_secret: str, bootstrap_admin_password: str) -> None:
    """Refuse insecure defaults outside local SQLite dev unless explicitly allowed."""
    allow_insecure = os.environ.get("ALLOW_INSECURE_DEV_DEFAULTS", "").lower() in {"1", "true", "yes"}
    is_sqlite = database_url.startswith("sqlite")

    if jwt_secret == DEFAULT_JWT_SECRET:
        if not is_sqlite and not allow_insecure:
            raise RuntimeError(
                "JWT_SECRET no configurado: defina una clave segura en .env para entornos PostgreSQL/producción."
            )
        if is_sqlite:
            logger.warning("JWT_SECRET por defecto — aceptable solo en desarrollo local SQLite.")

    if bootstrap_admin_password == DEFAULT_BOOTSTRAP_ADMIN_PASSWORD and not is_sqlite:
        logger.warning(
            "BOOTSTRAP_ADMIN_PASSWORD por defecto detectado en entorno no-SQLite — cambiar antes de producción."
        )
