"""Esquemas API — Integraciones (1330)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConnectorCreate(BaseModel):
    code: str
    name: str
    descripcion: str | None = None
    connector_type: str
    auth_type: str = "NINGUNA"
    secret_env_var: str | None = None
    config: dict[str, Any] | None = None
    mapping: list[dict[str, Any]] | None = None
    schema: dict[str, Any] | None = None
    destination_type: str | None = None
    signal_source_code: str | None = None
    trigger_mode: str = "MANUAL"
    retry_max: int = 3
    timeout_ms: int = 30000
    allow_internal_urls: bool = False
    generate_webhook_token: bool = False


class ConnectorUpdate(BaseModel):
    name: str | None = None
    descripcion: str | None = None
    config: dict[str, Any] | None = None
    mapping: list[dict[str, Any]] | None = None
    schema: dict[str, Any] | None = None
    destination_type: str | None = None
    signal_source_code: str | None = None
    status: str | None = None
    secret_env_var: str | None = None


class ExecuteRequest(BaseModel):
    idempotency_key: str | None = None
    payload: dict[str, Any] | None = None


class WebhookReceiveRequest(BaseModel):
    token: str
    payload: dict[str, Any] = Field(default_factory=dict)
