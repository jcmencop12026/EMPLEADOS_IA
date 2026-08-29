"""Adaptador base para proveedores LLM."""

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
        return self.complete(request, api_key=api_key)
