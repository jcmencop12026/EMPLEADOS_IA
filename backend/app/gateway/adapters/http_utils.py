"""Utilidades HTTP compartidas para adaptadores LLM."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.gateway.errors import LlmErrorCategory, LlmGatewayError
from app.gateway.secrets import sanitize_for_log


def map_http_status_to_error(
    status: int,
    body_text: str,
    *,
    provider: str,
    model: str,
) -> LlmGatewayError:
    detail = sanitize_for_log(body_text[:500])
    code = ""
    try:
        payload = json.loads(body_text)
        if isinstance(payload.get("error"), dict):
            api_msg = payload["error"].get("message", detail)
            detail = sanitize_for_log(str(api_msg))
            code = str(payload["error"].get("code", ""))
        elif payload.get("message"):
            detail = sanitize_for_log(str(payload["message"]))
    except json.JSONDecodeError:
        pass

    if status == 401:
        return LlmGatewayError.from_category(LlmErrorCategory.AUTH_ERROR, provider=provider, model=model, technical_detail=detail)
    if status == 429:
        return LlmGatewayError.from_category(LlmErrorCategory.RATE_LIMIT, provider=provider, model=model, technical_detail=detail)
    if status == 404 or code in {"model_not_found", "not_found"}:
        return LlmGatewayError.from_category(LlmErrorCategory.MODEL_NOT_FOUND, provider=provider, model=model, technical_detail=detail)
    if status >= 500:
        return LlmGatewayError.from_category(LlmErrorCategory.PROVIDER_UNAVAILABLE, provider=provider, model=model, technical_detail=detail)
    return LlmGatewayError.from_category(LlmErrorCategory.INVALID_RESPONSE, provider=provider, model=model, technical_detail=detail)


def request_with_timeout(
    *,
    transport: httpx.BaseTransport | None,
    timeout: int,
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    provider: str,
    model: str,
) -> tuple[httpx.Response | None, int, LlmGatewayError | None]:
    import time

    start = time.monotonic()
    try:
        with httpx.Client(transport=transport, timeout=timeout) as client:
            response = client.request(method, url, headers=headers, json=json_body)
        latency = int((time.monotonic() - start) * 1000)
        return response, latency, None
    except httpx.TimeoutException:
        latency = int((time.monotonic() - start) * 1000)
        return None, latency, LlmGatewayError.from_category(LlmErrorCategory.TIMEOUT, provider=provider, model=model)
    except httpx.RequestError as exc:
        latency = int((time.monotonic() - start) * 1000)
        return None, latency, LlmGatewayError.from_category(
            LlmErrorCategory.PROVIDER_UNAVAILABLE,
            provider=provider,
            model=model,
            technical_detail=sanitize_for_log(str(exc)),
        )
