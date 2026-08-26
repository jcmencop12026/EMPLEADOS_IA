from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocumentOut(BaseModel):
    id: str
    organization_id: str
    name: str
    source_type: str
    file_type: str | None = None
    mime_type: str | None = None
    status: str
    original_filename: str | None = None
    size_bytes: int | None = None
    version: int
    is_active: bool
    error_message: str | None = None
    association_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by_id: str | None = None
    updated_by_id: str | None = None
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    has_content: bool = False


class KnowledgeDocumentDetail(KnowledgeDocumentOut):
    processed_content: str | None = None
    chunks_count: int = 0


class KnowledgeTextCreate(BaseModel):
    name: str
    content: str
    metadata: dict[str, Any] | None = None


class KnowledgeDocumentUpdate(BaseModel):
    name: str | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class KnowledgeSearchResult(BaseModel):
    id: str
    name: str
    source_type: str
    file_type: str | None = None
    status: str
    snippet: str | None = None
    relevance: float | None = None


class KnowledgeRetrieveRequest(BaseModel):
    query: str
    filters: dict[str, Any] | None = None
    limit: int = Field(default=10, ge=1, le=50)
    context: dict[str, Any] | None = None
    employee_id: str | None = None


class KnowledgeRetrieveFragment(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    position: int
    page_number: int | None = None
    section: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    relevance: float | None = None


class KnowledgeActivityOut(BaseModel):
    id: str
    action: str
    detail: str | None = None
    user_id: str | None = None
    created_at: datetime


class EmployeeKnowledgeGrantOut(BaseModel):
    id: str
    employee_id: str
    document_id: str
    document_name: str
    is_active: bool
    created_at: datetime
