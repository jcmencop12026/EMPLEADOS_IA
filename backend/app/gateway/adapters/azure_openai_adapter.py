"""Adaptador Azure OpenAI — preparado/configurable."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.adapters.http_utils import map_http_status_to_error, request_with_timeout
from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.secrets import sanitize_for_log
from app.gateway.types import GatewayRequest, GatewayResponse, LlmMessage

DEFAULT_API_VERSION = "2024-02-15-preview"


class AzureOpenAIAdapter(BaseLlmAdapter):
    provider_type = "azure-openai"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._transport = transport

    def capabilities(self) -> dict[str, Any]:
        return {"chat": True, "vision": False, "tools": True, "streaming": False}

    def list_models(self, *, api_key: str | None = None) -> list[str]:
        return ["gpt-4o-mini", "gpt-4o"]

    def _deployment(self, request: GatewayRequest) -> str:
        params = request.parameters or {}
        if params.get("deployment"):
            return str(params["deployment"])
        meta = request.metadata or {}
        if meta.get("deployment"):
            return str(meta["deployment"])
        return request.model

    def _build_url(self, request: GatewayRequest) -> str | None:
        if not request.endpoint:
            return None
        deployment = self._deployment(request)
        base = request.endpoint.rstrip("/")
        api_version = (request.parameters or {}).get("api_version", DEFAULT_API_VERSION)
        return f"{base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    def validate_credentials(self, request: GatewayRequest, *, api_key: str | None = None) -> GatewayResponse:
        return self.complete(
            GatewayRequest(
                provider=self.provider_type,
                model=request.model or "gpt-4o-mini",
                messages=[LlmMessage(role="user", content="Responde únicamente: OK")],
                system_instructions="Prueba de conexión.",
                endpoint=request.endpoint,
                timeout_seconds=min(request.timeout_seconds, 30),
                trace_id=request.trace_id,
                parameters=request.parameters,
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
                    technical_detail="NO CONFIGURADO — falta credencial Azure OpenAI.",
                ),
            )
        url = self._build_url(request)
        if not url:
            return GatewayResponse(
                provider=provider,
                model=model,
                trace_id=request.trace_id,
                error=LlmGatewayError.from_category(
                    LlmErrorCategory.CONFIGURATION_ERROR,
                    provider=provider,
                    model=model,
                    technical_detail="NO CONFIGURADO — endpoint Azure requerido.",
                ),
            )

        messages: list[dict[str, str]] = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        payload: dict[str, Any] = {"messages": messages}
        params = request.parameters or {}
        if "temperature" in params:
            payload["temperature"] = params["temperature"]
        if "max_tokens" in params:
            payload["max_tokens"] = params["max_tokens"]

        headers = {"api-key": api_key, "content-type": "application/json"}
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
            choices = data.get("choices") or []
            text = choices[0].get("message", {}).get("content", "") if choices else ""
            usage = data.get("usage") or {}
            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                tokens_in=usage.get("prompt_tokens"),
                tokens_out=usage.get("completion_tokens"),
                tokens_total=usage.get("total_tokens"),
                latency_ms=latency,
                finish_reason=choices[0].get("finish_reason") if choices else None,
                trace_id=request.trace_id,
                raw_metadata={"response_id": data.get("id")},
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
                    technical_detail=sanitize_for_log(str(exc)),
                ),
            )
