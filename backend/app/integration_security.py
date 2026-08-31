"""Seguridad — SSRF, URLs y sanitización (1330)."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

_BLOCKED_HOSTS = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal",
})
_METADATA_IPS = frozenset({"169.254.169.254", "fd00:ec2::254"})


class SSRFError(ValueError):
    pass


def is_private_or_blocked_host(host: str) -> bool:
    if not host:
        return True
    host_lower = host.lower().strip("[]")
    if host_lower in _BLOCKED_HOSTS:
        return True
    if host_lower.endswith(".local") or host_lower.endswith(".internal"):
        return True
    try:
        addr = ipaddress.ip_address(host_lower)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or str(addr) in _METADATA_IPS
        )
    except ValueError:
        return False


def validate_external_url(url: str, *, allow_internal: bool = False) -> str:
    if not url or not url.strip():
        raise SSRFError("URL no especificada")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SSRFError("Solo se permiten esquemas http/https")
    host = parsed.hostname
    if not host:
        raise SSRFError("Host no válido en URL")
    if not allow_internal and is_private_or_blocked_host(host):
        raise SSRFError(f"Acceso a host interno o bloqueado no permitido: {host}")
    return url.strip()


def redact_sensitive_headers(headers: dict | None) -> dict:
    if not headers:
        return {}
    sensitive = re.compile(r"(authorization|api[_-]?key|token|secret|cookie)", re.I)
    return {k: ("[CONFIGURADO]" if sensitive.search(k) else v) for k, v in headers.items()}
