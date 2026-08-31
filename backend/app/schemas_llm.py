"""Schemas Pydantic para LLM Gateway y proveedores IA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LlmProviderOut(BaseModel):
    id: str
    organization_id: str
    name: str
    provider_type: str
    provider_label: str | None = None
    adapter_mode: str | None = None
    model_default: str | None = None
    endpoint: str | None = None
    timeout_seconds: int = 60
    priority: int = 100
    is_enabled: bool = True
    is_fallback: bool = False
    secret_ref: str | None = None
    secret_configured: bool = False
    secret_masked: str | None = None
    health_status: str | None = None
    health_detail: str | None = None
    config_json: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LlmProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    provider_type: str = Field(..., min_length=1, max_length=40)
    model_default: str | None = None
    endpoint: str | None = None
    timeout_seconds: int = Field(default=60, ge=5, le=600)
    priority: int = Field(default=100, ge=0, le=10000)
    is_enabled: bool = True
    is_fallback: bool = False
    secret_env_var: str | None = Field(
        default=None,
        description="Nombre de variable de entorno para el secreto (no se almacena el valor).",
    )
    config_json: dict[str, Any] | None = None


class LlmProviderUpdate(BaseModel):
    name: str | None = None
    model_default: str | None = None
    endpoint: str | None = None
    timeout_seconds: int | None = Field(default=None, ge=5, le=600)
    priority: int | None = Field(default=None, ge=0, le=10000)
    is_enabled: bool | None = None
    is_fallback: bool | None = None
    secret_env_var: str | None = None
    config_json: dict[str, Any] | None = None


class LlmTestConnectionResult(BaseModel):
    success: bool
    status: str
    message: str
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    error_category: str | None = None


class LlmInferenceLogOut(BaseModel):
    id: str
    trace_id: str
    employee_id: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    tokens_total: int | None = None
    latency_ms: int | None = None
    cost: float | None = None
    status: str
    finish_reason: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    fallback_used: bool = False
    initial_provider: str | None = None
    fallback_provider: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LlmCompleteRequest(BaseModel):
    prompt: str
    system_instructions: str | None = None
    provider: str | None = None
    model: str | None = None
    parameters: dict[str, Any] | None = None
    timeout_seconds: int | None = None
    employee_id: str | None = None
    include_knowledge: bool = False
    knowledge_query: str | None = None


class LlmCompleteResponse(BaseModel):
    text: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    tokens_total: int | None = None
    latency_ms: int | None = None
    finish_reason: str | None = None
    trace_id: str | None = None
    fallback_used: bool = False
    error: dict[str, Any] | None = None


class LlmObservabilitySummary(BaseModel):
    periodo: str | None = None
    total_inferencias: int = 0
    exitosas: int = 0
    errores: int = 0
    tasa_exito: float | None = None
    latencia_promedio_ms: float | None = None
    tokens_total: int | None = None
    costo_total: float | None = None
    fallbacks: int = 0
    por_proveedor: dict[str, int] = Field(default_factory=dict)
    errores_por_categoria: dict[str, int] = Field(default_factory=dict)


class LlmProviderHealthOut(BaseModel):
    provider_id: str
    provider_type: str
    nombre: str
    etiqueta: str
    modo: str | None = None
    estado: str
    detalle: str
    habilitado: bool
    configurado: bool
    es_fallback: bool = False
    prioridad: int = 100
    latencia_ms: int | None = None


class LlmRoutingExplainOut(BaseModel):
    seleccionado: dict[str, Any] | None = None
    razones: list[str] = Field(default_factory=list)


class LlmModelCatalogCreate(BaseModel):
    provider_type: str
    model_id: str
    display_name: str
    estado: str = "HABILITADO"
    capabilities: dict[str, Any] | None = None
    context_window: int | None = None
    modalities: list[str] | None = None
    cost_hint: dict[str, Any] | None = None
    priority: int = 100
    is_enabled: bool = True


class LlmModelCatalogOut(BaseModel):
    id: str
    provider_type: str
    model_id: str
    display_name: str
    estado: str
    capabilities: dict[str, Any] = Field(default_factory=dict)
    context_window: int | None = None
    modalities: list[str] = Field(default_factory=list)
    cost_hint: dict[str, Any] | None = None
    priority: int = 100
    is_enabled: bool = True


class LlmRoutingPolicyCreate(BaseModel):
    name: str
    preferred_provider: str | None = None
    preferred_model: str | None = None
    required_capability: str | None = None
    fallback_allowed: bool = True
    max_cost_per_1k_tokens: float | None = None
    credential_scope: str = "ORGANIZACION"
    priority: int = 100
    is_active: bool = True


class LlmRoutingPolicyUpdate(BaseModel):
    name: str | None = None
    preferred_provider: str | None = None
    preferred_model: str | None = None
    required_capability: str | None = None
    fallback_allowed: bool | None = None
    max_cost_per_1k_tokens: float | None = None
    credential_scope: str | None = None
    priority: int | None = None
    is_active: bool | None = None


class LlmRoutingPolicyOut(BaseModel):
    id: str
    name: str
    preferred_provider: str | None = None
    preferred_model: str | None = None
    required_capability: str | None = None
    fallback_allowed: bool = True
    max_cost_per_1k_tokens: float | None = None
    credential_scope: str = "ORGANIZACION"
    priority: int = 100
    is_active: bool = True
