from typing import Any

from pydantic import BaseModel, Field


class CapabilityCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str | None = None
    description: str | None = None
    category: str | None = None
    risk_level: str = "LOW"
    requires_approval: bool = False


class CapabilityUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    category: str | None = None
    risk_level: str | None = None
    requires_approval: bool | None = None


class ToolCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    capability_id: str
    code: str | None = None
    description: str | None = None
    tool_type: str = "PYTHON"
    risk_level: str = "LOW"
    requires_approval: bool = False
    configuration: dict[str, Any] | None = None
    timeout_seconds: int | None = None


class ToolUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    capability_id: str | None = None
    tool_type: str | None = None
    risk_level: str | None = None
    requires_approval: bool | None = None
    configuration: dict[str, Any] | None = None
    timeout_seconds: int | None = None


class ToolAssignRequest(BaseModel):
    tool_id: str
    permission: str = "ALLOW"


class KnowledgeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: str
    code: str | None = None
    description: str | None = None
    configuration: dict[str, Any] | None = None
    secret_ref: str | None = None


class KnowledgeUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    source_type: str | None = None
    configuration: dict[str, Any] | None = None
    secret_ref: str | None = None


class KnowledgeIngestRequest(BaseModel):
    content: str | None = None
    content_type: str | None = None


class TestLabRunRequest(BaseModel):
    employee_id: str
    task_description: str = Field(min_length=1)
    context: dict[str, Any] | None = None
    capability_id: str | None = None
    tool_id: str | None = None
    knowledge_source_ids: list[str] | None = None
    auto_execute: bool = True
