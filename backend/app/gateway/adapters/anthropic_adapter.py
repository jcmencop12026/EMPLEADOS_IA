"""Adaptador Anthropic — preparado/configurable vía API HTTP."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.adapters.http_utils import map_http_status_to_error, request_with_timeout
from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.types import GatewayRequest, GatewayResponse, LlmMessage

DEFAULT_ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
DEFAULT_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicAdapter(BaseLlmAdapter):
    provider_type = "anthropic"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def capabilities(self) -> dict[str, Any]:
        return {"chat": True, "vision": False, "tools": True, "streaming": False}

    def list_models(self, *, api_key: str | None = None) -> list[str]:
        return ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]

    def validate_credentials(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.complete(
            GatewayRequest(
                provider=self.provider_type,
                model=request.model or "claude-3-haiku-20240307",
                messages=[LlmMessage(role="user", content="Responde únicamente: OK")],
                system_instructions="Prueba de conexión.",
                timeout_seconds=min(request.timeout_seconds, 30),
                trace_id=request.trace_id,
            ),
            api_key=api_key,
        )

    def normalize_error(self, status: int, body_text: str, *, model: str) -> LlmGatewayError:
        return map_http_status_to_error(status, body_text, provider=self.provider_type, model=model)

    def complete(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        provider = self.provider_type
        model = request.model
        if not api_key:
            return GatewayResponse(
                provider=provider,
                model=model,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.CONFIGURATION_ERROR,
                    provider=provider,
                    model=model,
                    technical_detail="NO CONFIGURADO — falta credencial Anthropic.",
                ),
            )

        endpoint = request.endpoint or DEFAULT_ANTHROPIC_ENDPOINT
        messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        system = request.system_instructions or next((m.content for m in request.messages if m.role == "system"), None)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": (request.parameters or {}).get("max_tokens", 1024),
            "messages": messages,
        }
        if system:
            payload["system"] = system

        headers = {
            "x-api-key": api_key,
            "anthropic-version": DEFAULT_ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        response, latency, transport_error = request_with_timeout(
            transport=self._transport,
            timeout=request.timeout_seconds,
            method="POST",
            url=endpoint,
            headers=headers,
            json_body=payload,
            provider=provider,
            model=model,
        )
        if transport_error:
            return GatewayResponse(provider=provider, model=model, latency_ms=latency, trace_id=request.trace_id, error=transport_error)
        assert response is not None
        if response.status_code != 200:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=self.normalize_error(response.status_code, response.text, model=model),
            )
        try:
            data = response.json()
            content = data.get("content") or []
            text = content[0].get("text", "") if content else ""
            usage = data.get("usage") or {}
            tokens_in = usage.get("input_tokens")
            tokens_out = usage.get("output_tokens")
            tokens_total = (tokens_in or 0) + (tokens_out or 0) if tokens_in is not None else None
            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                tokens_total=tokens_total,
                latency_ms=latency,
                finish_reason=data.get("stop_reason"),
                trace_id=request.trace_id,
                raw_metadata={"id": data.get("id")},
            )
        except (json.JSONDecodeError, KeyError, TypeError, IndexError) as exc:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.INVALID_RESPONSE,
                    provider=provider,
                    model=model,
                    technical_detail=str(exc),
                ),
            )
