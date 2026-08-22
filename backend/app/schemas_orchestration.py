from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssistantAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    context: dict[str, Any] | None = None
    auto_execute: bool = True


class RouteTaskRequest(BaseModel):
    request: str = Field(min_length=1, max_length=8000)
    context: dict[str, Any] | None = None
    auto_execute: bool = True


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    comment: str | None = None


class TaskSummary(BaseModel):
    id: str
    title: str
    status: str
    executor_type: str
    confidence: float | None = None
    approval_status: str


class PlanResponse(BaseModel):
    plan_id: str
    correlation_id: str | None = None
    status: str
    objective: str | None = None
    summary: str | None = None
    confidence: float | None = None
    approval_status: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None
    tasks: list[TaskSummary] = []
    started_at: str | None = None
    completed_at: str | None = None


class EmployeeOut(BaseModel):
    id: str
    name: str
    specialty: str
    status: str
    model_provider: str | None = None
    model_name: str | None = None

    model_config = {"from_attributes": True}


class ExecutionOut(BaseModel):
    id: str
    request: str
    objective: str
    status: str
    summary: str | None = None
    confidence: float | None = None
    approval_status: str
    employee_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalOut(BaseModel):
    id: str
    work_plan_id: str
    action: str
    employee_name: str | None = None
    reason: str
    impact: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkEventOut(BaseModel):
    id: str
    event_type: str
    work_plan_id: str | None = None
    task_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
