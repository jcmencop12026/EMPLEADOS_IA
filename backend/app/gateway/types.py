"""Tipos de contrato del LLM Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LlmMessage:
    role: str
    content: str


@dataclass
class GatewayRequest:
    provider: str
    model: str
    messages: list[LlmMessage]
    system_instructions: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)
    endpoint: str | None = None
    secret_ref: str | None = None
    organization_id: str | None = None
    employee_id: str | None = None
    trace_id: str | None = None


@dataclass
class GatewayResponse:
    text: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    tokens_total: int | None = None
    latency_ms: int | None = None
    finish_reason: str | None = None
    error: Any | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    initial_provider: str | None = None
    fallback_provider: str | None = None
    fallback_used: bool = False
    initial_error: Any | None = None

    @property
    def success(self) -> bool:
        return self.error is None and self.text is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "tokens_total": self.tokens_total,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "error": self.error.to_dict() if self.error else None,
            "raw_metadata": self.raw_metadata,
            "trace_id": self.trace_id,
            "initial_provider": self.initial_provider,
            "fallback_provider": self.fallback_provider,
            "fallback_used": self.fallback_used,
            "initial_error": self.initial_error.to_dict() if self.initial_error else None,
        }
