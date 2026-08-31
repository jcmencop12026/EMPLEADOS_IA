"""Esquemas API — Motor Económico EIAAX."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class CostRegisterIn(BaseModel):
    amount_kind: str = "REAL"
    cost_source: str
    amount: Decimal
    currency: str = "USD"
    cost_class: str = "DIRECTO"
    scope_type: str = "ORGANIZACION"
    scope_id: str | None = None
    employee_id: str | None = None
    work_plan_id: str | None = None
    opportunity_id: str | None = None
    evaluacion_id: str | None = None
    provider: str | None = None
    model_name: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    description: str | None = None
    execution_ref: str | None = None
    register_finops: bool = True


class ValueRegisterIn(BaseModel):
    value_type: str
    value_nature: str = "ESTIMADO"
    amount: Decimal
    currency: str = "USD"
    scope_type: str = "ORGANIZACION"
    scope_id: str | None = None
    employee_id: str | None = None
    opportunity_id: str | None = None
    evaluacion_id: str | None = None
    methodology: str | None = None
    notes: str | None = None
    register_finops: bool = True


class PrivateEconomyIn(BaseModel):
    period_label: str = "MENSUAL"
    estimated_cost: float | None = None
    real_cost: float | None = None
    time_hours: float | None = None
    resources_cost: float | None = None
    ia_cost: float | None = None
    infra_cost: float | None = None
    services_cost: float | None = None
    support_cost: float | None = None
    client_value: float | None = None
    suggested_price: float | None = None
    margin: float | None = None
    roi: float | None = None
    payback_months: float | None = None
    commercial_risk_score: float | None = None
    notes: str | None = None


class PriceRecommendIn(BaseModel):
    scope_type: str = "ORGANIZACION"
    scope_id: str | None = None
    attributable_value: Decimal | None = None
    complexity: float = Field(0.5, ge=0, le=1)
    risk: float = Field(0.3, ge=0, le=1)
    urgency: float = Field(0.3, ge=0, le=1)
    reuse_factor: float = Field(0.5, ge=0, le=1)
    personalization: float = Field(0.5, ge=0, le=1)
    support_level: float = Field(0.3, ge=0, le=1)
    consumption_cost: Decimal | None = None
    infra_cost: Decimal | None = None
    currency: str = "USD"
    persist: bool = True


class EconomicEntryOut(BaseModel):
    id: str
    organization_id: str
    amount: float
    currency: str


class CostEntryOut(EconomicEntryOut):
    cost_class: str
    amount_kind: str
    cost_source: str
    scope_type: str
    finops_record_id: str | None = None


class ValueEntryOut(EconomicEntryOut):
    value_type: str
    value_nature: str
    scope_type: str
    finops_value_id: str | None = None


class EntityViewOut(BaseModel):
    organization_id: str
    vista: str
    costos: dict[str, Any]
    valores: dict[str, Any]
    roi_finops: Any = None
    costo_total_finops: Any = None
    valor_realizado_finops: Any = None
    nota_potencial: str
    economia_privada_incluida: bool = False
