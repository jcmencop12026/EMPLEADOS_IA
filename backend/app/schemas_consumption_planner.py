"""Esquemas — Planificador consumo y capacidad IA (MB-07)."""

from typing import Any

from pydantic import BaseModel, Field


class ModelDistributionSlice(BaseModel):
    provider: str | None = None
    model: str | None = None
    pct: float = Field(ge=0, le=100)


class PlannerConfigPatch(BaseModel):
    credential_mode: str | None = None
    currency: str | None = None
    included_consumption_usd: float | None = None
    client_price_monthly: float | None = None
    capacity_total_units: float | None = None
    max_concurrency: int | None = None
    executions_per_employee_per_day: float | None = None
    tokens_in_avg: int | None = None
    tokens_out_avg: int | None = None
    model_distribution: list[dict[str, Any]] | None = None
    alert_thresholds: list[int] | None = None
    plan_label: str | None = None


class PlannerSimulateIn(BaseModel):
    active_employees: int | None = None
    employee_count: int | None = None
    executions_per_day: float | None = None
    executions_per_employee_per_day: float | None = None
    days: int | None = 30
    model_distribution: list[dict[str, Any]] | None = None
    platform_cost_monthly: float | None = None
    save_as: str | None = None


class CompareScenarioIn(BaseModel):
    provider: str | None = None
    model: str | None = None
    latency_hint: str | None = None


class PlannerCompareIn(BaseModel):
    tokens_in: int = Field(ge=0, default=1500)
    tokens_out: int = Field(ge=0, default=800)
    scenarios: list[CompareScenarioIn]


class TransversalPatch(BaseModel):
    activation_type: str | None = None
    is_deterministic: bool | None = None
    executions_per_period: float | None = None
    period_days: int | None = None
    tokens_in_avg: int | None = None
    tokens_out_avg: int | None = None
    provider: str | None = None
    model_name: str | None = None
    tools_cost_estimated: float | None = None
    infra_cost_estimated: float | None = None
    enabled: bool | None = None
