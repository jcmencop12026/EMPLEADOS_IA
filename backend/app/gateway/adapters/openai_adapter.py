"""Adaptador OpenAI — integración real vía API HTTP."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.secrets import sanitize_for_log
from app.gateway.types import GatewayRequest, GatewayResponse, LlmMessage

DEFAULT_OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"


class OpenAIAdapter(BaseLlmAdapter):
    provider_type = "openai"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def _build_messages(self, request: GatewayRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def _parse_error(self, status: int, body_text: str, provider: str, model: str) -> LlmGatewayError:
        detail = sanitize_for_log(body_text[:500])
        try:
            payload = json.loads(body_text)
            api_msg = payload.get("error", {}).get("message", detail)
            detail = sanitize_for_log(str(api_msg))
            code = payload.get("error", {}).get("code", "")
        except json.JSONDecodeError:
            code = ""

        if status == 401:
            return LlmGatewayError.from_category(LlmErrorCategory.AUTH_ERROR, provider=provider, model=model, technical_detail=detail)
        if status == 429:
            return LlmGatewayError.from_category(LlmErrorCategory.RATE_LIMIT, provider=provider, model=model, technical_detail=detail)
        if status == 404 or code == "model_not_found":
            return LlmGatewayError.from_category(LlmErrorCategory.MODEL_NOT_FOUND, provider=provider, model=model, technical_detail=detail)
        if status >= 500:
            return LlmGatewayError.from_category(LlmErrorCategory.PROVIDER_UNAVAILABLE, provider=provider, model=model, technical_detail=detail)
        return LlmGatewayError.from_category(LlmErrorCategory.INVALID_RESPONSE, provider=provider, model=model, technical_detail=detail)

    def complete(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        provider = self.provider_type
        model = request.model
        endpoint = request.endpoint or DEFAULT_OPENAI_ENDPOINT

        if not api_key:
            return GatewayResponse(
                provider=provider,
                model=model,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.CONFIGURATION_ERROR,
                    provider=provider,
                    model=model,
                    technical_detail="API key no configurada (variable de entorno).",
                ),
            )

        payload: dict[str, Any] = {
            "model": model,
            "messages": self._build_messages(request),
        }
        params = request.parameters or {}
        if "temperature" in params:
            payload["temperature"] = params["temperature"]
        if "max_tokens" in params:
            payload["max_tokens"] = params["max_tokens"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start = time.monotonic()
        try:
            with httpx.Client(transport=self._transport, timeout=request.timeout_seconds) as client:
                response = client.post(endpoint, headers=headers, json=payload)
        except httpx.TimeoutException:
            latency = int((time.monotonic() - start) * 1000)
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(LlmErrorCategory.TIMEOUT, provider=provider, model=model),
            )
        except httpx.RequestError as exc:
            latency = int((time.monotonic() - start) * 1000)
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.PROVIDER_UNAVAILABLE,
                    provider=provider,
                    model=model,
                    technical_detail=sanitize_for_log(str(exc)),
                ),
            )

        latency = int((time.monotonic() - start) * 1000)
        if response.status_code != 200:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=self._parse_error(response.status_code, response.text, provider, model),
            )

        try:
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return GatewayResponse(
                    provider=provider,
                    model=model,
                    latency_ms=latency,
                    trace_id=request.trace_id,
                    error=LlmGatewayError.from_category(LlmErrorCategory.INVALID_RESPONSE, provider=provider, model=model),
                )
            choice = choices[0]
            text = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason")
            usage = data.get("usage") or {}
            tokens_in = usage.get("prompt_tokens")
            tokens_out = usage.get("completion_tokens")
            tokens_total = usage.get("total_tokens")
            if tokens_total is None and tokens_in is not None and tokens_out is not None:
                tokens_total = tokens_in + tokens_out

            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                tokens_total=tokens_total,
                latency_ms=latency,
                finish_reason=finish_reason,
                trace_id=request.trace_id,
                raw_metadata={"response_id": data.get("id")},
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.INVALID_RESPONSE,
                    provider=provider,
                    model=model,
                    technical_detail=sanitize_for_log(str(exc)),
                ),
            )
