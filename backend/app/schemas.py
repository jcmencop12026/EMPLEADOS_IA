from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class UserMe(BaseModel):
    id: str
    username: str
    role: str
    organization_id: str
    organization_name: str

    model_config = {"from_attributes": True}


class OrganizationOut(BaseModel):
    id: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: str
    action: str
    detail: str | None
    user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
