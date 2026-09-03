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
    enterprise_display_name: str | None = None
    enterprise_logo_url: str | None = None
    enterprise_logo_compact_url: str | None = None
    enterprise_accent_color: str | None = None


class OrgConfigUpdate(BaseModel):
    language: str | None = None
    timezone: str | None = None
    date_format: str | None = None
    time_format: str | None = None
    enterprise_display_name: str | None = Field(default=None, max_length=200)
    enterprise_logo_url: str | None = Field(default=None, max_length=700_000)
    enterprise_logo_compact_url: str | None = Field(default=None, max_length=700_000)
    enterprise_accent_color: str | None = Field(default=None, max_length=20)


class SecuritySummaryOut(BaseModel):
    users_active: int
    users_inactive: int
    users_blocked: int
    roles_total: int
    recent_events: list[dict]
    mfa_enabled_count: int = 0
    scim_metrics: dict | None = None
    scim_rate_limit_note: str | None = None


class UserMfaOverviewOut(BaseModel):
    enabled: bool
    enrollment_pending: bool = False
    confirmed_at: datetime | None = None
    updated_at: datetime | None = None
    mfa_required_by_policy: bool = False
    policy_mfa_mode: str | None = None
    allowed_method: str = "TOTP"


class UserIdentityOriginOut(BaseModel):
    source: str
    provider_code: str | None = None
    provider_name: str | None = None
    external_subject_ref: str | None = None


class UserProvisionOverviewOut(BaseModel):
    status: str
    external_id: str | None = None
    scim_resource_id: str | None = None
    updated_at: datetime | None = None


class UserOverviewOut(BaseModel):
    id: str
    username: str
    email: str | None
    full_name: str | None
    role: str
    role_name: str | None = None
    status: str
    is_active: bool
    organization_id: str
    organization_name: str | None = None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime | None
    mfa: UserMfaOverviewOut
    identity_origin: UserIdentityOriginOut
    provisioning: UserProvisionOverviewOut


class UserPermissionEffectiveOut(BaseModel):
    code: str
    source: str
    role_code: str | None = None
    organization_id: str


class UserSessionBriefOut(BaseModel):
    id: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    mfa_verified: bool
    auth_method: str | None = None


class UserAuditEntryOut(BaseModel):
    stream: str
    action: str
    result: str | None = None
    actor_id: str | None = None
    organization_id: str | None = None
    detail: str | None = None
    correlation_id: str | None = None
    created_at: datetime


class UserIdentityDetailOut(BaseModel):
    user: UserOut
    organization_name: str | None = None
    role_name: str | None = None
    mfa: UserMfaOverviewOut
    identity_origin: UserIdentityOriginOut
    provisioning: UserProvisionOverviewOut
    permissions_effective: list[UserPermissionEffectiveOut]
    sessions: list[UserSessionBriefOut]
    audit_entries: list[UserAuditEntryOut]
    scim_user_events: list[dict] = Field(default_factory=list)
