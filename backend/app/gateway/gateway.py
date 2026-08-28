"""Servicio principal del LLM Gateway — selección, fallback y orquestación."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.gateway.adapters.base import BaseLlmAdapter
from app.gateway.adapters.ollama_adapter import OllamaAdapter
from app.gateway.adapters.openai_adapter import OpenAIAdapter
from app.gateway.errors import FALLBACK_ELIGIBLE, LlmErrorCategory, LlmGatewayError
from app.gateway.secrets import resolve_secret
from app.gateway.types import GatewayRequest, GatewayResponse, LlmMessage
from app.llm_models import LlmInferenceLog, LlmProviderConfig

_ADAPTER_REGISTRY: dict[str, type[BaseLlmAdapter]] = {
    "openai": OpenAIAdapter,
    "ollama": OllamaAdapter,
}


@dataclass
class ProviderSelection:
    config: LlmProviderConfig
    model: str


def get_adapter(provider_type: str, transport: Any | None = None) -> BaseLlmAdapter:
    cls = _ADAPTER_REGISTRY.get(provider_type.lower())
    if not cls:
        raise ValueError(f"Proveedor no soportado: {provider_type}")
    return cls(transport=transport)


def list_provider_configs(
    db: Session,
    organization_id: str,
    *,
    enabled_only: bool = False,
) -> list[LlmProviderConfig]:
    query = db.query(LlmProviderConfig).filter(LlmProviderConfig.organization_id == organization_id)
    if enabled_only:
        query = query.filter(LlmProviderConfig.is_enabled.is_(True))
    return query.order_by(LlmProviderConfig.priority.asc(), LlmProviderConfig.name.asc()).all()


def select_primary_provider(
    db: Session,
    organization_id: str,
    *,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
) -> ProviderSelection | None:
    configs = list_provider_configs(db, organization_id, enabled_only=True)
    if not configs:
        return None

    if preferred_provider:
        for cfg in configs:
            if cfg.provider_type.lower() == preferred_provider.lower() and not cfg.is_fallback:
                model = preferred_model or cfg.model_default or "gpt-4o-mini"
                return ProviderSelection(config=cfg, model=model)

    primary = next((c for c in configs if not c.is_fallback), configs[0])
    model = preferred_model or primary.model_default or _default_model(primary.provider_type)
    return ProviderSelection(config=primary, model=model)


def select_fallback_provider(
    db: Session,
    organization_id: str,
    *,
    exclude_provider: str | None = None,
) -> ProviderSelection | None:
    configs = list_provider_configs(db, organization_id, enabled_only=True)
    fallback_cfg = next((c for c in configs if c.is_fallback), None)
    if not fallback_cfg:
        fallback_cfg = next(
            (c for c in configs if c.provider_type.lower() != (exclude_provider or "").lower()),
            None,
        )
    if not fallback_cfg or fallback_cfg.provider_type.lower() == (exclude_provider or "").lower():
        return None
    model = fallback_cfg.model_default or _default_model(fallback_cfg.provider_type)
    return ProviderSelection(config=fallback_cfg, model=model)


def _default_model(provider_type: str) -> str:
    if provider_type.lower() == "openai":
        return "gpt-4o-mini"
    if provider_type.lower() == "ollama":
        return "llama3.2"
    return "default"


def _invoke_adapter(
    adapter: BaseLlmAdapter,
    request: GatewayRequest,
    config: LlmProviderConfig,
) -> GatewayResponse:
    api_key = resolve_secret(config.secret_ref)
    enriched = GatewayRequest(
        provider=config.provider_type,
        model=request.model,
        messages=request.messages,
        system_instructions=request.system_instructions,
        parameters=request.parameters,
        timeout_seconds=request.timeout_seconds or config.timeout_seconds,
        metadata=request.metadata,
        endpoint=config.endpoint or request.endpoint,
        secret_ref=config.secret_ref,
        organization_id=request.organization_id,
        employee_id=request.employee_id,
        trace_id=request.trace_id,
    )
    return adapter.complete(enriched, api_key=api_key)


def complete(
    db: Session,
    *,
    organization_id: str,
    messages: list[LlmMessage],
    system_instructions: str | None = None,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
    fallback_model: str | None = None,
    parameters: dict[str, Any] | None = None,
    timeout_seconds: int | None = None,
    metadata: dict[str, Any] | None = None,
    employee_id: str | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    enable_fallback: bool = True,
    transport: Any | None = None,
) -> GatewayResponse:
    trace_id = str(uuid.uuid4())
    base_request = GatewayRequest(
        provider=preferred_provider or "",
        model=preferred_model or "",
        messages=messages,
        system_instructions=system_instructions,
        parameters=parameters or {},
        timeout_seconds=timeout_seconds or 60,
        metadata=metadata or {},
        organization_id=organization_id,
        employee_id=employee_id,
        trace_id=trace_id,
    )

    primary_sel = select_primary_provider(
        db,
        organization_id,
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
    )
    if not primary_sel:
        error = LlmGatewayError.from_category(
            LlmErrorCategory.CONFIGURATION_ERROR,
            technical_detail="No hay proveedores IA habilitados.",
        )
        response = GatewayResponse(error=error, trace_id=trace_id)
        _persist_inference_log(db, organization_id, response, employee_id, work_plan_id, task_id)
        return response

    adapter = get_adapter(primary_sel.config.provider_type, transport=transport)
    primary_request = GatewayRequest(
        provider=primary_sel.config.provider_type,
        model=primary_sel.model,
        messages=messages,
        system_instructions=system_instructions,
        parameters=parameters or {},
        timeout_seconds=timeout_seconds or primary_sel.config.timeout_seconds,
        metadata=metadata or {},
        organization_id=organization_id,
        employee_id=employee_id,
        trace_id=trace_id,
    )
    result = _invoke_adapter(adapter, primary_request, primary_sel.config)
    result.trace_id = trace_id
    result.initial_provider = primary_sel.config.provider_type

    if result.success:
        _persist_inference_log(db, organization_id, result, employee_id, work_plan_id, task_id)
        return result

    initial_error = result.error
    if not enable_fallback or not initial_error or initial_error.category not in FALLBACK_ELIGIBLE:
        _persist_inference_log(db, organization_id, result, employee_id, work_plan_id, task_id)
        return result

    fallback_sel = select_fallback_provider(db, organization_id, exclude_provider=primary_sel.config.provider_type)
    if not fallback_sel:
        result.error = LlmGatewayError.from_category(
            LlmErrorCategory.ALL_PROVIDERS_FAILED,
            technical_detail=initial_error.message,
        )
        result.initial_error = initial_error
        _persist_inference_log(db, organization_id, result, employee_id, work_plan_id, task_id)
        return result

    fb_model = fallback_model or fallback_sel.model
    fb_adapter = get_adapter(fallback_sel.config.provider_type, transport=transport)
    fb_request = GatewayRequest(
        provider=fallback_sel.config.provider_type,
        model=fb_model,
        messages=messages,
        system_instructions=system_instructions,
        parameters=parameters or {},
        timeout_seconds=timeout_seconds or fallback_sel.config.timeout_seconds,
        metadata=metadata or {},
        organization_id=organization_id,
        employee_id=employee_id,
        trace_id=trace_id,
    )
    fb_result = _invoke_adapter(fb_adapter, fb_request, fallback_sel.config)
    fb_result.trace_id = trace_id
    fb_result.initial_provider = primary_sel.config.provider_type
    fb_result.fallback_provider = fallback_sel.config.provider_type
    fb_result.fallback_used = True
    fb_result.initial_error = initial_error

    if not fb_result.success:
        fb_result.error = LlmGatewayError.from_category(
            LlmErrorCategory.ALL_PROVIDERS_FAILED,
            technical_detail=f"Principal: {initial_error.message}; Fallback: {fb_result.error.message if fb_result.error else 'error'}",
        )
        fb_result.initial_error = initial_error

    _persist_inference_log(db, organization_id, fb_result, employee_id, work_plan_id, task_id)
    return fb_result


def test_provider_connection(
    db: Session,
    organization_id: str,
    provider_id: str,
    *,
    transport: Any | None = None,
) -> GatewayResponse:
    config = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.id == provider_id, LlmProviderConfig.organization_id == organization_id)
        .first()
    )
    if not config:
        return GatewayResponse(
            error=LlmGatewayError.from_category(
                LlmErrorCategory.CONFIGURATION_ERROR,
                technical_detail="Proveedor no encontrado.",
            ),
        )

    model = config.model_default or _default_model(config.provider_type)
    adapter = get_adapter(config.provider_type, transport=transport)
    request = GatewayRequest(
        provider=config.provider_type,
        model=model,
        messages=[LlmMessage(role="user", content="Responde únicamente: OK")],
        system_instructions="Eres un asistente de prueba de conexión.",
        timeout_seconds=min(config.timeout_seconds, 30),
        trace_id=str(uuid.uuid4()),
    )
    return _invoke_adapter(adapter, request, config)


def _persist_inference_log(
    db: Session,
    organization_id: str,
    response: GatewayResponse,
    employee_id: str | None,
    work_plan_id: str | None,
    task_id: str | None,
) -> LlmInferenceLog:
    status = "OK" if response.success else "ERROR"
    error = response.error
    tokens_total = response.tokens_total
    if tokens_total is None and response.tokens_in is not None and response.tokens_out is not None:
        tokens_total = response.tokens_in + response.tokens_out
    log = LlmInferenceLog(
        organization_id=organization_id,
        trace_id=response.trace_id or str(uuid.uuid4()),
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        provider=response.provider,
        model=response.model,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        tokens_total=tokens_total,
        latency_ms=response.latency_ms,
        status=status,
        finish_reason=response.finish_reason,
        error_category=error.category if error else None,
        error_message=error.message if error else None,
        initial_provider=response.initial_provider,
        fallback_provider=response.fallback_provider,
        fallback_used=response.fallback_used,
        metadata_json=json.dumps(response.raw_metadata or {}, ensure_ascii=False) if response.raw_metadata else None,
    )
    db.add(log)
    db.flush()
    return log
