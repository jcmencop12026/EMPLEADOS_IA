"""Adaptador Google Gemini — preparado/configurable vía API HTTP."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.adapters.http_utils import map_http_status_to_error, request_with_timeout
from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.types import GatewayRequest, GatewayResponse, LlmMessage

DEFAULT_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAdapter(BaseLlmAdapter):
    provider_type = "gemini"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def capabilities(self) -> dict[str, Any]:
        return {"chat": True, "vision": True, "tools": False, "streaming": False}

    def list_models(self, *, api_key: str | None = None) -> list[str]:
        return ["gemini-1.5-flash", "gemini-1.5-pro"]

    def validate_credentials(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.complete(
            GatewayRequest(
                provider=self.provider_type,
                model=request.model or "gemini-1.5-flash",
                messages=[LlmMessage(role="user", content="Responde únicamente: OK")],
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
                    technical_detail="NO CONFIGURADO — falta credencial Gemini.",
                ),
            )

        base = request.endpoint or DEFAULT_GEMINI_BASE
        url = f"{base.rstrip('/')}/{model}:generateContent?key={api_key}"
        parts: list[dict[str, str]] = []
        if request.system_instructions:
            parts.append({"text": f"Sistema: {request.system_instructions}"})
        for msg in request.messages:
            parts.append({"text": f"{msg.role}: {msg.content}"})
        payload = {"contents": [{"role": "user", "parts": parts}]}
        headers = {"content-type": "application/json"}

        response, latency, transport_error = request_with_timeout(
            transport=self._transport,
            timeout=request.timeout_seconds,
            method="POST",
            url=url,
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
            candidates = data.get("candidates") or []
            content = candidates[0].get("content", {}).get("parts", []) if candidates else []
            text = content[0].get("text", "") if content else ""
            usage = data.get("usageMetadata") or {}
            tokens_in = usage.get("promptTokenCount")
            tokens_out = usage.get("candidatesTokenCount")
            tokens_total = usage.get("totalTokenCount")
            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                tokens_total=tokens_total,
                latency_ms=latency,
                finish_reason=candidates[0].get("finishReason") if candidates else None,
                trace_id=request.trace_id,
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
