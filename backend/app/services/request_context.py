"""Utilidades HTTP para seguridad — Bloque 1300."""

from __future__ import annotations

from fastapi import Request


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


def client_user_agent(request: Request) -> str | None:
    ua = request.headers.get("User-Agent")
    return ua[:300] if ua else None
