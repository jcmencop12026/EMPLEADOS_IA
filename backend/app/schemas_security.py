from datetime import datetime

from pydantic import BaseModel, Field


class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    mfa_token: str
    token_type: str = "mfa_pending"
    message: str = "Se requiere verificación de autenticación multifactor."


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32)
    mfa_token: str | None = None


class MfaEnrollStartResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data_url: str


class MfaConfirmRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32)


class MfaRecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]


class MfaPasswordConfirmRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class MfaStatusOut(BaseModel):
    enabled: bool
    confirmed_at: datetime | None = None
    recovery_codes_remaining: int = 0
    enrollment_pending: bool = False
    mfa_required_by_policy: bool = False


class SessionOut(BaseModel):
    id: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    mfa_verified: bool
    current: bool = False

    model_config = {"from_attributes": True}


class SecurityPolicyOut(BaseModel):
    mfa_mode: str
    mfa_required_roles: list[str] = Field(default_factory=list)
    session_duration_minutes: int
    max_active_sessions: int
    login_max_attempts: int
    lockout_minutes: int
    revoke_sessions_on_password_change: bool
    excess_session_policy: str


class SecurityPolicyUpdate(BaseModel):
    mfa_mode: str | None = None
    mfa_required_roles: list[str] | None = None
    session_duration_minutes: int | None = Field(default=None, ge=15, le=10080)
    max_active_sessions: int | None = Field(default=None, ge=1, le=50)
    login_max_attempts: int | None = Field(default=None, ge=3, le=20)
    lockout_minutes: int | None = Field(default=None, ge=5, le=120)
    revoke_sessions_on_password_change: bool | None = None
    excess_session_policy: str | None = None


class SecurityEventOut(BaseModel):
    id: str
    event_type: str
    user_id: str | None = None
    detail: str | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)
    revoke_other_sessions: bool | None = None


class ForgotPasswordRequest(BaseModel):
    email_or_username: str = Field(min_length=3, max_length=120)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class ForgotPasswordResponse(BaseModel):
    message: str
