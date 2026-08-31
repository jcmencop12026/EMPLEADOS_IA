"""Esquemas API — Identidad empresarial y SSO (1370)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IdentitySettingsOut(BaseModel):
  auth_mode: str
  mfa_sso_mode: str
  auto_provision_enabled: bool
  default_role_on_provision: str
  allowed_domains: list[str] = Field(default_factory=list)
  org_discovery_code: str | None = None
  attribute_mapping: dict[str, Any] = Field(default_factory=dict)
  break_glass_enabled: bool
  break_glass_configured: bool
  scim_prepared: bool


class IdentitySettingsUpdate(BaseModel):
  auth_mode: str | None = None
  mfa_sso_mode: str | None = None
  auto_provision_enabled: bool | None = None
  default_role_on_provision: str | None = None
  allowed_domains: list[str] | None = None
  org_discovery_code: str | None = None
  attribute_mapping: dict[str, Any] | None = None
  break_glass_env_var: str | None = None


class IdentityProviderCreate(BaseModel):
  code: str
  name: str
  provider_type: str
  vendor_hint: str | None = None
  secret_env_var: str | None = None
  config: dict[str, Any] | None = None
  is_default: bool = False
  saml_cert_fingerprint: str | None = None


class IdentityProviderUpdate(BaseModel):
  name: str | None = None
  vendor_hint: str | None = None
  config: dict[str, Any] | None = None
  status: str | None = None
  secret_env_var: str | None = None
  is_default: bool | None = None
  saml_cert_fingerprint: str | None = None


class GroupRoleMappingCreate(BaseModel):
  external_group: str
  role_code: str


class OidcCallbackRequest(BaseModel):
  state: str
  code: str


class SamlAcsRequest(BaseModel):
  relay_state: str
  saml_response: str


class LoginDiscoverRequest(BaseModel):
  org_code: str | None = None
  domain: str | None = None


class BreakGlassRequest(BaseModel):
  username: str
  password: str
  break_glass_token: str


class IdentityLoginAuditOut(BaseModel):
  id: str
  login_method: str
  result: str
  user_id: str | None = None
  provider_id: str | None = None
  detail: str | None = None
  ip_address: str | None = None
  created_at: datetime

  model_config = {"from_attributes": True}
