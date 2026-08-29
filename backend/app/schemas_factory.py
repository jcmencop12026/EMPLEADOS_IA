from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmployeeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    specialty: str = Field(min_length=1, max_length=120)
    role: str | None = None
    objective: str | None = None
    template_code: str | None = None


class EmployeeUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    role: str | None = None
    objective: str | None = None
    specialty: str | None = None
    risk_level: str | None = None
    maturity: str | None = None
    shadow_mode: bool | None = None
    capability_ids: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    knowledge: list[dict[str, Any]] | None = None
    model_policy: dict[str, Any] | None = None
    limits: dict[str, Any] | None = None
    instructions: dict[str, Any] | None = None
    force_new_version: bool = False


class EmployeeOut(BaseModel):
    id: str
    code: str
    name: str
    specialty: str
    lifecycle_status: str
    maturity: str
    risk_level: str
    status: str
    version: int
    capabilities: list[str] = []
    model_provider: str | None = None
    model_name: str | None = None
    last_certification: str | None = None
    shadow_mode: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class TemplateOut(BaseModel):
    code: str
    name: str
    description: str | None = None
    specialty: str


class EmployeeVersionCreateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    changed_fields: list[str] | None = None


class EmployeeTestCaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    test_type: str = "SMOKE"
    test_category: str | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] | None = None
    criterion: str | None = None
    validation_rules: dict[str, Any] | None = None
    severity: str = "medium"
    is_active: bool = True


class EmployeeApprovalRequest(BaseModel):
    kind: str = Field(description="PUBLISH, ROLLBACK, PROVIDER_CHANGE, etc.")
    reason: str = Field(min_length=3, max_length=500)
    target_version: int | None = None


class EmployeeRollbackRequest(BaseModel):
    target_version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)
    force: bool = False


class EmployeeTrainingRequest(BaseModel):
    training_type: str = Field(description="NEW_KNOWLEDGE, INSTRUCTIONS, REGULATION, etc.")
    reason: str = Field(min_length=3, max_length=500)
    source: str | None = None
    config_delta: dict[str, Any] | None = None
    approved_by_id: str | None = None


class EmployeeRetireRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
