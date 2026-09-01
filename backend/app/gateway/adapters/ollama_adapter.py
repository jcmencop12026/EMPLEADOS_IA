"""Adaptador Ollama — inferencia local/configurable."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.secrets import sanitize_for_log
from app.gateway.types import GatewayRequest, GatewayResponse

DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"


class OllamaAdapter(BaseLlmAdapter):
    provider_type = "ollama"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def _chat_url(self, base_url: str) -> str:
        base = base_url.rstrip("/")
        return f"{base}/api/chat"

    def _build_messages(self, request: GatewayRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def complete(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        provider = self.provider_type
        model = request.model
        base_url = request.endpoint or DEFAULT_OLLAMA_BASE
        url = self._chat_url(base_url)

        payload: dict[str, Any] = {
            "model": model,
            "messages": self._build_messages(request),
            "stream": False,
        }
        params = request.parameters or {}
        options: dict[str, Any] = {}
        if "temperature" in params:
            options["temperature"] = params["temperature"]
        if options:
            payload["options"] = options

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        start = time.monotonic()
        try:
            with httpx.Client(transport=self._transport, timeout=request.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
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
        if response.status_code == 404:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.MODEL_NOT_FOUND,
                    provider=provider,
                    model=model,
                    technical_detail=sanitize_for_log(response.text[:300]),
                ),
            )
        if response.status_code != 200:
            return GatewayResponse(
                provider=provider,
                model=model,
                latency_ms=latency,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.PROVIDER_UNAVAILABLE,
                    provider=provider,
                    model=model,
                    technical_detail=sanitize_for_log(response.text[:300]),
                ),
            )

        try:
            data = response.json()
            message = data.get("message") or {}
            text = message.get("content", "")
            if not text:
                return GatewayResponse(
                    provider=provider,
                    model=model,
                    latency_ms=latency,
                    trace_id=request.trace_id,
                    error=LlmGatewayError.from_category(LlmErrorCategory.INVALID_RESPONSE, provider=provider, model=model),
                )

            tokens_in = data.get("prompt_eval_count")
            tokens_out = data.get("eval_count")
            tokens_total = None
            if tokens_in is not None and tokens_out is not None:
                tokens_total = tokens_in + tokens_out

            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                tokens_total=tokens_total,
                latency_ms=latency,
                finish_reason="stop",
                trace_id=request.trace_id,
                raw_metadata={"done": data.get("done")},
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
