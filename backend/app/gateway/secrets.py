"""Manejo seguro de secretos — referencias env, sin exposición en logs/API."""

from __future__ import annotations

import os
import re


_SECRET_PATTERN = re.compile(r"(sk-[a-zA-Z0-9]{4,})[a-zA-Z0-9_-]+")
_API_KEY_PATTERN = re.compile(r"(api[_-]?key[\"']?\s*[:=]\s*[\"']?)([a-zA-Z0-9_-]{8,})", re.IGNORECASE)


def build_env_secret_ref(env_var: str) -> str:
    return f"env:{env_var}"


def parse_secret_ref(secret_ref: str | None) -> tuple[str, str] | None:
    """Devuelve (source, key) — source='env' para variables de entorno."""
    if not secret_ref:
        return None
    if secret_ref.startswith("env:"):
        return "env", secret_ref[4:]
    return "env", secret_ref


def resolve_secret(secret_ref: str | None) -> str | None:
    parsed = parse_secret_ref(secret_ref)
    if not parsed:
        return None
    source, key = parsed
    if source == "env":
        return os.environ.get(key) or None
    return None


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return value[:4] + "…" + value[-2:]


def sanitize_for_log(text: str) -> str:
    if not text:
        return text
    text = _SECRET_PATTERN.sub(r"\1…", text)
    text = _API_KEY_PATTERN.sub(r"\1***", text)
    return text


def secret_configured(secret_ref: str | None) -> bool:
    return bool(resolve_secret(secret_ref))
