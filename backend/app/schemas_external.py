"""Schemas — Inteligencia externa (1240)."""

from typing import Any

from pydantic import BaseModel, Field


class ExternalContextIn(BaseModel):
    sector: str | None = None
    mercado: str | None = None
    productos_servicios: str | None = None
    geografias: str | None = None
    clientes_objetivo: str | None = None
    procesos_clave: str | None = None
    estrategia: str | None = None
    dominios: list[str] | None = None
    freshness_recent_days: int | None = Field(None, ge=1, le=365)
    freshness_stale_days: int | None = Field(None, ge=1, le=730)


class ExternalSourceCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=200)
    source_type: str
    ingestion_channel: str
    url_reference: str | None = None
    descripcion: str | None = None
    sector: str | None = None
    pais_region: str | None = None
    frecuencia_esperada: str | None = None
    confiabilidad: float = Field(0.5, ge=0, le=1)


class ExternalSourcePatch(BaseModel):
    name: str | None = None
    descripcion: str | None = None
    url_reference: str | None = None
    sector: str | None = None
    pais_region: str | None = None
    frecuencia_esperada: str | None = None
    estado: str | None = None
    confiabilidad: float | None = Field(None, ge=0, le=1)
    is_active: bool | None = None


class ExternalSignalIngest(BaseModel):
    source_code: str
    hecho_observado: str = Field(..., min_length=5)
    evento: str | None = None
    dominio: str | None = None
    tipo: str | None = None
    titulo: str | None = None
    referencia: str | None = None
    reference_url: str | None = None
    published_at: str | None = None
    captured_at: str | None = None
    classification: str | None = None
    relevance: str | None = None
    interpretacion: str | None = None
    hipotesis: str | None = None
    oportunidad_propuesta: str | None = None
    confidence_level: float | None = Field(None, ge=0, le=1)
    idempotency_key: str | None = None
    is_risk: bool = False
    risk_type: str | None = None
    competitor: dict[str, Any] | None = None
    regulation: dict[str, Any] | None = None
    technology: dict[str, Any] | None = None
    demand: dict[str, Any] | None = None
    auto_process: bool = False


class ClassificationPatch(BaseModel):
    classification: str


class RelevancePatch(BaseModel):
    relevance: str


class RiskRegister(BaseModel):
    risk_type: str | None = None
