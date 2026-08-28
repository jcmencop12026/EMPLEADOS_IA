from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    username: str
    email: str | None
    full_name: str | None
    role: str
    status: str
    is_active: bool
    organization_id: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    created_by_id: str | None
    updated_by_id: str | None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)
    role: str = Field(min_length=2, max_length=40)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=200)
    full_name: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=40)


class UserStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACTIVE|INACTIVE|BLOCKED)$")


class PasswordResetRequest(BaseModel):
    new_password: str | None = Field(default=None, min_length=8, max_length=200)


class PasswordResetResponse(BaseModel):
    temporary_password: str


class RoleOut(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    is_system: bool
    is_active: bool
    organization_id: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str]


class OrganizationAdminOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    timezone: str
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = Field(default=None, max_length=64)


class OrgConfigOut(BaseModel):
    language: str
    timezone: str
    date_format: str
    time_format: str


class OrgConfigUpdate(BaseModel):
    language: str | None = None
    timezone: str | None = None
    date_format: str | None = None
    time_format: str | None = None


class SecuritySummaryOut(BaseModel):
    users_active: int
    users_inactive: int
    users_blocked: int
    roles_total: int
    recent_events: list[dict]
