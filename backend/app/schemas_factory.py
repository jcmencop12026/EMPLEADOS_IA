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
