from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    mfa_required: bool = False


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserMe(BaseModel):
    id: str
    username: str
    role: str
    organization_id: str
    organization_name: str
    email: str | None = None
    full_name: str | None = None
    status: str = "ACTIVE"
    permissions: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class OrganizationOut(BaseModel):
    id: str
    name: str
    status: str = "ACTIVE"
    timezone: str = "America/Bogota"
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: str
    action: str
    detail: str | None
    user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
