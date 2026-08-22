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
    inputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    outputs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    executor_types_json: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    lifecycle_status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    maturity: Mapped[str] = mapped_column(String(40), default="DRAFT")
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default="DISPONIBLE")
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    shadow_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    certified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmployeeCapability(Base):
    __tablename__ = "employee_capabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(36), ForeignKey("capabilities.id"), nullable=False)


class EmployeeToolGrant(Base):
    __tablename__ = "employee_tool_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(36), ForeignKey("tools.id"), nullable=False)
    permission: Mapped[str] = mapped_column(String(30), default="ALLOW")


class EmployeeKnowledgeSource(Base):
    __tablename__ = "employee_knowledge_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeModelPolicy(Base):
    __tablename__ = "employee_model_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, unique=True)
    preferred_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    allowed_models_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fallback_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_daily: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_ceiling: Mapped[float | None] = mapped_column(Float, nullable=True)
    policy_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmployeeLimits(Base):
    __tablename__ = "employee_limits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, unique=True)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=120)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    daily_cost_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    task_cost_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    allowed_hours_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String(40), nullable=True)
    approval_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    limits_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmployeeInstructions(Base):
    __tablename__ = "employee_instructions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, unique=True)
    system_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    operating_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_contract: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmployeeVersion(Base):
    __tablename__ = "employee_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    configuration_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeTestCase(Base):
    __tablename__ = "employee_test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_type: Mapped[str] = mapped_column(String(30), default="SMOKE")
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    expected_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_rules_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeTestRun(Base):
    __tablename__ = "employee_test_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    test_case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_test_cases.id"), nullable=True)
    test_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    input_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    tools_used_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    certified_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeTemplate(Base):
    __tablename__ = "employee_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    template_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


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
