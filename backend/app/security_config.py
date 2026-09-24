"""Validación de configuración sensible — hardening V1."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRET = "change-me-in-env-local-dev-only"
DEFAULT_BOOTSTRAP_ADMIN_PASSWORD = "Admin2026*"
MIN_JWT_SECRET_LENGTH = 32


def validate_security_settings(
    *,
    database_url: str,
    jwt_secret: str,
    bootstrap_admin_password: str,
    app_env: str = "dev",
    cors_origins: str = "",
) -> None:
    """Refuse insecure defaults outside local SQLite dev unless explicitly allowed."""
    allow_insecure = os.environ.get("ALLOW_INSECURE_DEV_DEFAULTS", "").lower() in {"1", "true", "yes"}
    is_sqlite = database_url.startswith("sqlite")
    is_production = app_env == "prod"

    if jwt_secret == DEFAULT_JWT_SECRET:
        if not is_sqlite and not allow_insecure:
            raise RuntimeError(
                "JWT_SECRET no configurado: defina una clave segura en .env para entornos PostgreSQL/producción."
            )
        if is_sqlite:
            logger.warning("JWT_SECRET por defecto — aceptable solo en desarrollo local SQLite.")

    if not is_sqlite and not allow_insecure and len(jwt_secret) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET demasiado corto: use al menos {MIN_JWT_SECRET_LENGTH} caracteres en producción."
        )

    if bootstrap_admin_password == DEFAULT_BOOTSTRAP_ADMIN_PASSWORD:
        if not is_sqlite and not allow_insecure:
            raise RuntimeError(
                "BOOTSTRAP_ADMIN_PASSWORD no configurado: defina una contraseña segura en .env "
                "para entornos PostgreSQL/producción."
            )
        if is_sqlite:
            logger.warning(
                "BOOTSTRAP_ADMIN_PASSWORD por defecto — aceptable solo en desarrollo local SQLite."
            )

    if is_production and not allow_insecure:
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        if not origins:
            raise RuntimeError(
                "CORS_ORIGINS no configurado: defina orígenes explícitos en producción (sin wildcard)."
            )
        if any(origin == "*" for origin in origins):
            raise RuntimeError(
                "CORS_ORIGINS no puede incluir '*' en producción."
            )
