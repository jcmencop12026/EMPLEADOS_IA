from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ConsumptionIn(BaseModel):
    employee_id: str | None = None
    work_plan_id: str | None = None
    task_id: str | None = None
    opportunity_id: str | None = None
    execution_ref: str | None = None
    provider: str | None = None
    model_name: str | None = None
    category: str = "Modelo IA"
    tokens_in: int | None = None
    tokens_out: int | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    duration_ms: int | None = None
    currency: str | None = None
    cost: Decimal | None = None
    rate_id: str | None = None


class ConsumptionOut(BaseModel):
    id: str
    organization_id: str
    employee_id: str | None
    work_plan_id: str | None
    task_id: str | None
    opportunity_id: str | None
    execution_ref: str | None
    provider: str | None
    model_name: str | None
    category: str | None
    tokens_in: int | None
    tokens_out: int | None
    quantity: Decimal | None
    unit: str | None
    cost: Decimal | None
    cost_label: str
    currency: str | None
    rate_source: str | None
    duration_ms: int | None
    created_at: datetime


class RateIn(BaseModel):
    provider: str | None = None
    model_service: str | None = None
    category: str = "Modelo IA"
    unit: str | None = None
    price_input: Decimal | None = None
    price_output: Decimal | None = None
    unit_price: Decimal | None = None
    currency: str = "USD"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    active: bool = True


class RatePatch(BaseModel):
    provider: str | None = None
    model_service: str | None = None
    category: str | None = None
    unit: str | None = None
    price_input: Decimal | None = None
    price_output: Decimal | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    active: bool | None = None


class RateOut(BaseModel):
    id: str
    organization_id: str
    provider: str | None
    model_service: str | None
    category: str
    unit: str | None
    price_input: Decimal | None
    price_output: Decimal | None
    unit_price: Decimal | None
    currency: str
    valid_from: datetime | None
    valid_until: datetime | None
    active: bool
    created_at: datetime


class ValueIn(BaseModel):
    employee_id: str | None = None
    work_plan_id: str | None = None
    opportunity_id: str | None = None
    task_id: str | None = None
    value_type: str
    certainty: str = "Estimado"
    amount: Decimal | None = None
    currency: str | None = None
    methodology: str | None = None
    source: str | None = None
    notes: str | None = None


class ValueOut(BaseModel):
    id: str
    organization_id: str
    employee_id: str | None
    work_plan_id: str | None
    opportunity_id: str | None
    task_id: str | None
    value_type: str
    certainty: str
    amount: Decimal | None
    currency: str | None
    methodology: str | None
    source: str | None
    notes: str | None
    created_at: datetime


class BudgetIn(BaseModel):
    scope_type: str
    scope_id: str | None = None
    period_start: datetime
    period_end: datetime
    amount_limit: Decimal
    currency: str = "USD"
    policy: str = "Solo informar"
    alert_threshold_pct: int = Field(default=90, ge=50, le=100)
    name: str | None = None
    active: bool = True


class BudgetPatch(BaseModel):
    period_start: datetime | None = None
    period_end: datetime | None = None
    amount_limit: Decimal | None = None
    currency: str | None = None
    policy: str | None = None
    alert_threshold_pct: int | None = Field(default=None, ge=50, le=100)
    name: str | None = None
    active: bool | None = None


class BudgetOut(BaseModel):
    id: str
    organization_id: str
    scope_type: str
    scope_id: str | None
    period_start: datetime
    period_end: datetime
    amount_limit: Decimal
    currency: str
    policy: str
    alert_threshold_pct: int
    name: str | None
    active: bool
    spent: Decimal
    balance: Decimal
    state: str
    projection: Decimal | None = None
    blocks_execution: bool = False


class OpportunityEconomicsOut(BaseModel):
    opportunity_id: str
    opportunity_codigo: str
    total_cost: Decimal | None
    total_cost_label: str
    valor_potencial: Decimal | None
    valor_materializado: Decimal | None
    finops_value_sum: Decimal | None
    consumption_count: int
    consumptions: list[ConsumptionOut]
    finops_reference: str | None
    atribucion_nivel: str | None


class DashboardSummary(BaseModel):
    period_start: datetime | None
    period_end: datetime | None
    total_cost: Decimal | None
    total_cost_label: str
    total_value: Decimal | None
    total_value_label: str
    estimated_savings: Decimal | None
    net_benefit: Decimal | None
    roi_percent: Decimal | None
    roi_label: str
    execution_count: int
    avg_cost_per_work: Decimal | None
    currency: str | None


class DrillDownNode(BaseModel):
    id: str
    label: str
    node_type: str
    cost: Decimal | None
    cost_label: str
    children: list["DrillDownNode"] = Field(default_factory=list)
