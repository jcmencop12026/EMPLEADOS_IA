"""Esquemas API — Modelo comercial (1280)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    code: str
    name: str
    descripcion: str | None = None
    credential_mode: str = "IA_ADMINISTRADA"
    currency: str = "USD"
    precio_base_mensual: float | None = None
    margen_minimo_pct: float = 0.15
    fraccion_valor_sugerida: float | None = 0.25
    precio_minimo: float | None = None
    precio_maximo: float | None = None
    consumo_ia_incluido_tokens: int | None = None
    presupuesto_ia_incluido: float | None = None
    excedente_ia_por_millon: float | None = None
    alerta_consumo_pct: float | None = None
    bloqueo_excedente: bool = False
    limits: dict[str, Any] | None = None
    organization_id: str | None = None


class ProposalCreate(BaseModel):
    titulo: str
    plan_id: str | None = None
    credential_mode: str = "IA_ADMINISTRADA"
    diagnostic_id: str | None = None
    currency: str = "USD"
    vigencia_hasta: datetime | None = None
    supuestos: dict[str, Any] | list[Any] | None = None
    riesgos: dict[str, Any] | list[Any] | None = None


class ValueComponentCreate(BaseModel):
    categoria: str
    naturaleza: str = "ESTIMADO"
    valor_bruto: float
    atribucion_pct: float = 0
    criterio_atribucion: str | None = None
    justificacion: str | None = None
    evidencia: str | None = None
    opportunity_id: str | None = None
    valuation_id: str | None = None
    linea_base_id: str | None = None


class ScenarioCreate(BaseModel):
    scenario_type: str
    valor_esperado: float | None = None
    valor_atribuible: float | None = None
    probabilidad: float | None = None
    costo: float | None = None
    periodo_meses: int | None = None
    riesgo_nivel: str | None = None
    explicacion: str | None = None
    es_recomendado: bool = False


class CostCreate(BaseModel):
    categoria: str
    clase_costo: str = "COSTO_INTERNO"
    monto: float
    currency: str | None = None
    finops_record_id: str | None = None
    descripcion: str | None = None
    es_recurrente: bool = False
    periodo_meses: int | None = None


class SimulateRequest(BaseModel):
    valor_bruto: float
    atribucion_pct: float = 0
    costo_total: float = 0
    fraccion_valor: float = 0.25
    margen_minimo_pct: float = 0.15


class PriceSuggestRequest(BaseModel):
    scenario_type: str = "BASE"


class FinalPriceRequest(BaseModel):
    precio_final: float
    justificacion: str | None = None


class ImportValuationRequest(BaseModel):
    opportunity_id: str
