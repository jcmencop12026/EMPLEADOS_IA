from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlatformOrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    timezone: str
    created_at: datetime
    updated_at: datetime | None
    users_count: int = 0

    model_config = {"from_attributes": True}


class PlatformOrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9-]+$")
    timezone: str = Field(default="America/Bogota", max_length=64)
    admin_username: str = Field(min_length=2, max_length=80)
    admin_password: str | None = Field(default=None, min_length=8, max_length=200)
    admin_email: str | None = Field(default=None, max_length=200)
    admin_full_name: str | None = Field(default=None, max_length=200)


class PlatformOrganizationCreateResponse(BaseModel):
    organization: PlatformOrganizationOut
    admin_user_id: str
    admin_username: str
    temporary_password: str | None = None


class PlatformOrganizationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACTIVE|INACTIVE)$")
