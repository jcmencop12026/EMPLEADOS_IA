"""Schemas — Valoración económica y ROI (1210)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ValuationCreateIn(BaseModel):
    value_type: str = "AHORRO"
    scope: str = "INTERNO"
    currency: str = "USD"


class ExpectedValueIn(BaseModel):
    gross_value: Decimal | None = None
    probability: Decimal | None = Field(None, ge=0, le=1)
    execution_cost_expected: Decimal | None = None
    period_days: int | None = Field(None, ge=1)
    value_nature: str = "ESTIMADA"
    assumptions: str | None = None
    source: str | None = None
    evidence: str | None = None


class ScenarioIn(BaseModel):
    value_amount: Decimal | None = None
    probability: Decimal | None = Field(None, ge=0, le=1)
    cost: Decimal | None = None
    period_days: int | None = Field(None, ge=1)
    assumptions: str | None = None


class RealValueIn(BaseModel):
    materialized_value: Decimal | None = None
    attributable_value: Decimal | None = None
    value_nature: str = "ESTIMADO"
    attribution_level: str = "NO ATRIBUIBLE"
    attribution_pct: Decimal | None = Field(None, ge=0, le=100)
    source: str | None = None
    evidence: str | None = None
    responsible_id: str | None = None
    justification: str | None = None
    external_measurement_ref: str | None = None


class ExecutionCostIn(BaseModel):
    cost_type: str
    amount: Decimal = Field(..., gt=0)
    currency: str | None = None
    finops_record_id: str | None = None
    description: str | None = None
    source: str | None = None


class ValuationSummaryOut(BaseModel):
    has_valuation: bool
    opportunity_id: str
    valuation: dict[str, Any] | None = None
    expected: dict[str, Any] | None = None
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    real: dict[str, Any] | None = None
    execution_costs: list[dict[str, Any]] = Field(default_factory=list)
    finops_ia_cost: Decimal | None = None
    finops_ia_cost_label: str | None = None
    total_execution_cost: Decimal | None = None
    gross_expected: Decimal | None = None
    adjusted_expected: Decimal | None = None
    materialized_value: Decimal | None = None
    attributable_value: Decimal | None = None
    net_benefit: Decimal | None = None
    return_percent: Decimal | None = None
    return_label: str = "NO CALCULABLE"
    payback_days: int | None = None
    payback_label: str = "NO CALCULABLE"
    missing_for_calculation: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)


class ValuationOut(BaseModel):
    id: str
    opportunity_id: str
    value_type: str
    scope: str
    currency: str
    status: str
    version: int
    validated_at: datetime | None
    created_at: datetime
