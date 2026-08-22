import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Capability(Base):
    __tablename__ = "capabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(36), ForeignKey("capabilities.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    executor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    capability: Mapped["Capability"] = relationship()


class AIEmployee(Base):
    __tablename__ = "ai_employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="DISPONIBLE")
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeCapability(Base):
    __tablename__ = "employee_capabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(36), ForeignKey("capabilities.id"), nullable=False)


class WorkPlan(Base):
    __tablename__ = "work_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    request: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="CREATED", index=True)
    capability_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("capabilities.id"), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    tool_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tools.id"), nullable=True)
    steps_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencies_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(30), default="NOT_REQUIRED")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    tasks: Mapped[list["EmployeeTask"]] = relationship(back_populates="work_plan", order_by="EmployeeTask.sequence")


class EmployeeTask(Base):
    __tablename__ = "employee_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    work_plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=False, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    capability_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("capabilities.id"), nullable=True)
    tool_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tools.id"), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    executor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="CREATED", index=True)
    inputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    outputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(30), default="NOT_REQUIRED")
    cost_reference_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    work_plan: Mapped["WorkPlan"] = relationship(back_populates="tasks")


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    work_plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkEvent(Base):
    __tablename__ = "work_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class FinOpsRecord(Base):
    __tablename__ = "finops_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
