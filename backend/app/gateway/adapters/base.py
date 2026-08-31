"""Adaptador base para proveedores LLM — contrato común Bloque 1270."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.gateway.types import GatewayRequest, GatewayResponse


class BaseLlmAdapter(ABC):
    provider_type: str

    @abstractmethod
    def complete(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        ...

    def test_connection(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.validate_credentials(request, api_key=api_key)

    def validate_credentials(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.complete(request, api_key=api_key)

    def health(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.validate_credentials(request, api_key=api_key)

    def list_models(self, *, api_key: str | None = None) -> list[str]:
        return []

    def capabilities(self) -> dict[str, Any]:
        return {"chat": True, "vision": False, "tools": False, "streaming": False}

    def usage(self, response: GatewayResponse) -> dict[str, Any]:
        return {
            "tokens_in": response.tokens_in,
            "tokens_out": response.tokens_out,
            "tokens_total": response.tokens_total,
            "latency_ms": response.latency_ms,
        }

    def normalize_error(self, status: int, body_text: str, *, model: str):
        from app.gateway.adapters.http_utils import map_http_status_to_error

        return map_http_status_to_error(status, body_text, provider=self.provider_type, model=model)
