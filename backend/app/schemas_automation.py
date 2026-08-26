from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RecurrenceConfig(BaseModel):
    hour: int | None = 9
    minute: int | None = 0
    weekdays: list[int] | None = None  # 0=Mon .. 6=Sun
    day_of_month: int | None = None
    interval_minutes: int | None = None
    event_type: str | None = None  # INTERNAL_EVENT V1


class AutomationBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    trigger_type: str = "SCHEDULE"
    schedule_type: str | None = "DAILY"
    timezone: str = "UTC"
    start_at: datetime | None = None
    end_at: datetime | None = None
    recurrence: RecurrenceConfig | None = None
    objective: str = Field(min_length=1)
    employee_id: str | None = None
    workflow: dict[str, Any] | None = None
    priority: int = 5
    max_retries: int = Field(default=0, ge=0, le=10, description="Reintentos después del intento inicial")
    retry_delay_seconds: int = 60
    timeout_seconds: int | None = None
    requires_approval: bool = False
    max_cost_per_run: float | None = None
    max_runs_per_day: int | None = None
    missed_run_policy: str = "SKIP"


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    schedule_type: str | None = None
    timezone: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    recurrence: RecurrenceConfig | None = None
    objective: str | None = None
    employee_id: str | None = None
    workflow: dict[str, Any] | None = None
    priority: int | None = None
    max_retries: int | None = None
    retry_delay_seconds: int | None = None
    timeout_seconds: int | None = None
    requires_approval: bool | None = None
    max_cost_per_run: float | None = None
    max_runs_per_day: int | None = None
    missed_run_policy: str | None = None


class AutomationOut(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None
    status: str
    trigger_type: str
    schedule_type: str | None
    timezone: str
    start_at: datetime | None
    end_at: datetime | None
    next_run_at: datetime | None
    last_run_at: datetime | None
    recurrence: RecurrenceConfig | None
    objective: str
    employee_id: str | None
    workflow: dict[str, Any] | None
    priority: int
    max_retries: int
    retry_delay_seconds: int
    timeout_seconds: int | None
    requires_approval: bool
    max_cost_per_run: float | None
    max_runs_per_day: int | None
    missed_run_policy: str
    created_by_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AutomationRunOut(BaseModel):
    id: str
    automation_id: str
    organization_id: str
    occurrence_key: str
    scheduled_for: datetime
    started_at: datetime | None
    finished_at: datetime | None
    status: str
    work_plan_id: str | None
    result_reference: dict[str, Any] | None
    attempt: int
    error: str | None
    cost_reference: float | None
    trigger_source: str
    created_at: datetime

    model_config = {"from_attributes": True}
