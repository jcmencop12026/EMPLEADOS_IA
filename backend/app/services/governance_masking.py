"""Funciones de enmascaramiento — BLOQUE 1350."""
from __future__ import annotations

import re


def mask_email(value: str) -> str:
    if not value or "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 4:
        return "***"
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_identifier(value: str) -> str:
    if not value:
        return "***"
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def mask_account_number(value: str) -> str:
    if not value:
        return "***"
    clean = re.sub(r"\s", "", value)
    if len(clean) <= 4:
        return "*" * len(clean)
    return "*" * (len(clean) - 4) + clean[-4:]


def mask_confidential_text(value: str, visible: int = 0) -> str:
    if not value:
        return ""
    if visible <= 0:
        return "[CONFIDENCIAL]"
    if len(value) <= visible:
        return value
    return value[:visible] + "…"


def apply_mask(field_type: str, value: str) -> str:
    """Aplica enmascaramiento según tipo de campo."""
    mapping = {
        "email": mask_email,
        "correo": mask_email,
        "phone": mask_phone,
        "telefono": mask_phone,
        "identifier": mask_identifier,
        "identificador": mask_identifier,
        "account": mask_account_number,
        "cuenta": mask_account_number,
        "confidential": mask_confidential_text,
        "confidencial": mask_confidential_text,
    }
    fn = mapping.get((field_type or "").lower())
    if fn is None:
        return mask_confidential_text(value)
    return fn(value)


def sanitize_secret_fields(data: dict, secret_keys: set[str] | None = None) -> dict:
    """Elimina valores sensibles de un dict — solo referencias permitidas."""
    keys = secret_keys or {
        "password", "api_key", "apikey", "jwt", "token", "secret",
        "mfa_secret", "access_token", "refresh_token",
    }
    out = {}
    for k, v in data.items():
        lk = k.lower()
        if lk in keys or any(s in lk for s in ("password", "secret", "token", "api_key", "jwt")):
            out[k] = "CONFIGURADO" if v else "NO_CONFIGURADO"
        elif isinstance(v, dict):
            out[k] = sanitize_secret_fields(v, keys)
        else:
            out[k] = v
    return out
