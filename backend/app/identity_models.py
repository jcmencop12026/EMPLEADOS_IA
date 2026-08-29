"""Modelos — Identidad empresarial, SSO, OIDC y SAML (1370)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationIdentitySettings(Base):
    """Política de autenticación e identidad por organización."""

    __tablename__ = "organization_identity_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), unique=True, nullable=False)
    auth_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="SOLO_LOCAL")
    mfa_sso_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="EAIOS")
    auto_provision_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    default_role_on_provision: Mapped[str] = mapped_column(String(40), nullable=False, default="viewer")
    allowed_domains_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_discovery_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    attribute_mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    break_glass_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    break_glass_secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scim_prepared: Mapped[bool] = mapped_column(Boolean, default=False)
    scim_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class IdentityProvider(Base):
    """Proveedor de identidad configurable (OIDC / SAML)."""

    __tablename__ = "identity_providers"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_idp_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(10), nullable=False)
    vendor_hint: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR", index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    saml_cert_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    saml_cert_not_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class UserExternalIdentity(Base):
    """Vinculación usuario local ↔ identidad externa."""

    __tablename__ = "user_external_identities"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_subject", name="uq_external_identity_subject"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("identity_providers.id"), nullable=False, index=True)
    external_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    external_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IdentityGroupRoleMapping(Base):
    """Mapeo explícito grupo externo → rol (allowlist)."""

    __tablename__ = "identity_group_role_mappings"
    __table_args__ = (
        UniqueConstraint("organization_id", "provider_id", "external_group", name="uq_group_role_map"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("identity_providers.id"), nullable=False)
    external_group: Mapped[str] = mapped_column(String(200), nullable=False)
    role_code: Mapped[str] = mapped_column(String(40), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SsoAuthState(Base):
    """Estado temporal OIDC/SAML (state, nonce, PKCE)."""

    __tablename__ = "sso_auth_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(36), ForeignKey("identity_providers.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    nonce: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pkce_verifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    redirect_after: Mapped[str | None] = mapped_column(String(300), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IdentityLoginAudit(Base):
    """Auditoría de intentos de login SSO/local."""

    __tablename__ = "identity_login_audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("identity_providers.id"), nullable=True)
    login_method: Mapped[str] = mapped_column(String(20), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
