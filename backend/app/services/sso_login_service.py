"""Orquestación de login SSO — OIDC, SAML, provisión y sesiones 1300 (1370)."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.gateway.secrets import resolve_secret
from app.identity_enums import AuthMode, FORBIDDEN_AUTO_ROLES, IdPStatus, IdPType, MfaSsoMode
from app.identity_models import IdentityProvider, IdentityGroupRoleMapping, SsoAuthState, UserExternalIdentity
from app.models import Organization, User
from app.security import hash_password
from app.services import identity_service as id_svc
from app.services import oidc_service
from app.services import saml_service
from app.services.security_event_service import log_security_event
from app.services.security_policy_service import get_or_create_policy, is_mfa_required_for_user, user_has_mfa_enabled
from app.services.session_service import create_session
from app.security import create_access_token, create_mfa_pending_token
from app.tenant_scope import ORG_STATUS_ACTIVE


class SsoLoginError(ValueError):
  def __init__(self, message: str, *, category: str = "SSO"):
    super().__init__(message)
    self.category = category


def _utcnow() -> datetime:
  return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime | None) -> datetime | None:
  if dt is None:
    return None
  if dt.tzinfo is None:
    return dt.replace(tzinfo=timezone.utc)
  return dt


def _parse_config(row: IdentityProvider) -> dict:
  return json.loads(row.config_json) if row.config_json else {}


def _create_auth_state(db: Session, *, org_id: str, provider_id: str, nonce: str | None, pkce_verifier: str | None) -> SsoAuthState:
  state = secrets.token_urlsafe(32)
  row = SsoAuthState(
    organization_id=org_id,
    provider_id=provider_id,
    state=state,
    nonce=nonce,
    pkce_verifier=pkce_verifier,
    expires_at=_utcnow() + timedelta(minutes=10),
  )
  db.add(row)
  db.flush()
  return row


def begin_oidc(db: Session, organization_id: str, provider_id: str) -> dict:
  provider = db.query(IdentityProvider).filter(
    IdentityProvider.id == provider_id,
    IdentityProvider.organization_id == organization_id,
    IdentityProvider.provider_type == IdPType.OIDC,
    IdentityProvider.status == IdPStatus.ACTIVO,
  ).first()
  if not provider:
    raise SsoLoginError("Proveedor OIDC no disponible")
  config = _parse_config(provider)
  verifier, challenge = oidc_service.generate_pkce()
  nonce = secrets.token_urlsafe(16)
  auth_state = _create_auth_state(db, org_id=organization_id, provider_id=provider_id, nonce=nonce, pkce_verifier=verifier)
  redirect_uri = config.get("redirect_uri") or "/api/identidad/oidc/callback"
  url = oidc_service.build_authorization_url(
    config, state=auth_state.state, nonce=nonce, redirect_uri=redirect_uri, pkce_challenge=challenge,
  )
  return {"authorization_url": url, "state": auth_state.state}


def complete_oidc(
  db: Session, *, state: str, code: str, ip: str | None, user_agent: str | None,
) -> dict[str, Any]:
  auth_state = db.query(SsoAuthState).filter(SsoAuthState.state == state, SsoAuthState.consumed_at.is_(None)).first()
  if not auth_state or _ensure_aware(auth_state.expires_at) < _utcnow():
    raise SsoLoginError("Estado OIDC inválido o expirado", category="VALIDACION")
  provider = db.query(IdentityProvider).filter(IdentityProvider.id == auth_state.provider_id).first()
  if not provider or provider.organization_id != auth_state.organization_id:
    raise SsoLoginError("Proveedor no encontrado", category="VALIDACION")
  config = _parse_config(provider)
  tokens = oidc_service.exchange_code_mock(config, code=code)
  id_token = tokens.get("id_token")
  if not id_token:
    raise SsoLoginError("Token ID no recibido", category="AUTENTICACION")
  try:
    claims = oidc_service.validate_id_token(id_token, config, nonce=auth_state.nonce)
  except oidc_service.OidcError as exc:
    id_svc.log_login_audit(db, organization_id=auth_state.organization_id, user_id=None, provider_id=provider.id,
                           login_method="OIDC", result="FALLIDO", detail=str(exc), ip_address=ip)
    log_security_event(db, organization_id=auth_state.organization_id, event_type="SSO_TOKEN_INVALIDO",
                       detail=str(exc)[:200], ip_address=ip)
    raise SsoLoginError(str(exc), category=exc.category) from exc

  auth_state.consumed_at = _utcnow()
  profile = _map_profile(claims, auth_state.organization_id, db)
  return _finalize_sso_login(
    db, organization_id=auth_state.organization_id, provider=provider,
    subject=claims.get("sub") or profile.get("subject", ""),
    profile=profile, ip=ip, user_agent=user_agent,
  )


def begin_saml(db: Session, organization_id: str, provider_id: str) -> dict:
  provider = db.query(IdentityProvider).filter(
    IdentityProvider.id == provider_id,
    IdentityProvider.organization_id == organization_id,
    IdentityProvider.provider_type == IdPType.SAML,
    IdentityProvider.status == IdPStatus.ACTIVO,
  ).first()
  if not provider:
    raise SsoLoginError("Proveedor SAML no disponible")
  config = _parse_config(provider)
  relay = secrets.token_urlsafe(24)
  auth_state = _create_auth_state(db, org_id=organization_id, provider_id=provider_id, nonce=None, pkce_verifier=None)
  auth_state.redirect_after = relay
  url = saml_service.build_authn_request_url(config, relay_state=auth_state.state)
  return {"sso_url": url, "relay_state": auth_state.state}


def complete_saml(
  db: Session, *, relay_state: str, saml_response: str, ip: str | None, user_agent: str | None,
) -> dict[str, Any]:
  auth_state = db.query(SsoAuthState).filter(SsoAuthState.state == relay_state, SsoAuthState.consumed_at.is_(None)).first()
  if not auth_state or _ensure_aware(auth_state.expires_at) < _utcnow():
    raise SsoLoginError("Estado SAML inválido o expirado", category="VALIDACION")
  provider = db.query(IdentityProvider).filter(IdentityProvider.id == auth_state.provider_id).first()
  if not provider:
    raise SsoLoginError("Proveedor no encontrado")
  config = _parse_config(provider)
  try:
    assertion = saml_service.parse_saml_response(saml_response, config)
  except saml_service.SamlError as exc:
    id_svc.log_login_audit(db, organization_id=auth_state.organization_id, user_id=None, provider_id=provider.id,
                           login_method="SAML", result="FALLIDO", detail=str(exc), ip_address=ip)
    log_security_event(db, organization_id=auth_state.organization_id, event_type="SSO_SAML_INVALIDO",
                       detail=str(exc)[:200], ip_address=ip)
    raise SsoLoginError(str(exc), category=exc.category) from exc

  auth_state.consumed_at = _utcnow()
  profile = {
    "subject": assertion["subject"],
    "email": assertion.get("email"),
    "given_name": assertion.get("given_name"),
    "family_name": assertion.get("family_name"),
    "groups": assertion.get("groups") or [],
  }
  return _finalize_sso_login(
    db, organization_id=auth_state.organization_id, provider=provider,
    subject=assertion["subject"], profile=profile, ip=ip, user_agent=user_agent,
  )


def _map_profile(claims: dict, organization_id: str, db: Session) -> dict:
  settings = id_svc.get_or_create_identity_settings(db, organization_id)
  mapping = json.loads(settings.attribute_mapping_json) if settings.attribute_mapping_json else {}
  profile = {
    "subject": claims.get("sub"),
    "email": claims.get(mapping.get("email", "email")),
    "given_name": claims.get(mapping.get("given_name", "given_name")),
    "family_name": claims.get(mapping.get("family_name", "family_name")),
    "groups": claims.get(mapping.get("groups", "groups")) or claims.get("groups") or [],
  }
  return profile


def _resolve_role_from_groups(db: Session, organization_id: str, provider_id: str, groups: list) -> str | None:
  if not groups:
    return None
  mappings = db.query(IdentityGroupRoleMapping).filter(
    IdentityGroupRoleMapping.organization_id == organization_id,
    IdentityGroupRoleMapping.provider_id == provider_id,
    IdentityGroupRoleMapping.is_active.is_(True),
  ).all()
  group_set = {str(g).lower() for g in groups}
  for m in mappings:
    if m.external_group.lower() in group_set and m.role_code not in FORBIDDEN_AUTO_ROLES:
      return m.role_code
  return None


def _find_or_provision_user(
  db: Session, *, organization_id: str, provider: IdentityProvider, subject: str, profile: dict,
) -> User:
  settings = id_svc.get_or_create_identity_settings(db, organization_id)
  link = db.query(UserExternalIdentity).filter(
    UserExternalIdentity.provider_id == provider.id,
    UserExternalIdentity.external_subject == subject,
  ).first()
  if link:
    user = db.query(User).filter(User.id == link.user_id, User.organization_id == organization_id).first()
    if not user:
      raise SsoLoginError("Usuario vinculado no encontrado")
    if not user.is_active or user.status != "ACTIVE":
      raise SsoLoginError("Usuario deshabilitado localmente")
    link.last_login_at = _utcnow()
    return user

  if not settings.auto_provision_enabled:
    raise SsoLoginError("Auto-provisión deshabilitada")

  role = _resolve_role_from_groups(db, organization_id, provider.id, profile.get("groups") or [])
  if not role:
    role = settings.default_role_on_provision
  if role in FORBIDDEN_AUTO_ROLES:
    raise SsoLoginError("Rol prohibido para auto-provisión")

  username = f"sso-{provider.code}-{subject[:20]}".lower().replace(" ", "-")
  if db.query(User).filter(User.username == username).first():
    username = f"{username}-{uuid.uuid4().hex[:6]}"
  user = User(
    organization_id=organization_id,
    username=username,
    password_hash=hash_password(secrets.token_urlsafe(32)),
    email=profile.get("email"),
    full_name=" ".join(filter(None, [profile.get("given_name"), profile.get("family_name")])).strip() or None,
    role=role,
    status="ACTIVE",
    is_active=True,
  )
  db.add(user)
  db.flush()
  db.add(UserExternalIdentity(
    user_id=user.id,
    organization_id=organization_id,
    provider_id=provider.id,
    external_subject=subject,
    external_email=profile.get("email"),
    last_login_at=_utcnow(),
  ))
  log_security_event(db, organization_id=organization_id, user_id=user.id, event_type="SSO_AUTO_PROVISION",
                     detail=f"provider={provider.code}")
  return user


def _finalize_sso_login(
  db: Session, *, organization_id: str, provider: IdentityProvider, subject: str,
  profile: dict, ip: str | None, user_agent: str | None,
) -> dict[str, Any]:
  org = db.query(Organization).filter(Organization.id == organization_id).first()
  if not org or org.status != ORG_STATUS_ACTIVE:
    raise SsoLoginError("Organización no disponible")

  user = _find_or_provision_user(db, organization_id=organization_id, provider=provider, subject=subject, profile=profile)
  settings = id_svc.get_or_create_identity_settings(db, organization_id)

  provider.last_login_at = _utcnow()
  id_svc.log_login_audit(db, organization_id=organization_id, user_id=user.id, provider_id=provider.id,
                         login_method=provider.provider_type, result="EXITOSO", ip_address=ip)
  log_security_event(db, organization_id=organization_id, user_id=user.id, event_type="LOGIN_SSO_EXITOSO",
                     detail=provider.code, ip_address=ip)

  mfa_mode = settings.mfa_sso_mode
  if mfa_mode == MfaSsoMode.IDP:
    mfa_verified = True
    mfa_required = False
  elif mfa_mode == MfaSsoMode.ADICIONAL or is_mfa_required_for_user(db, user):
    mfa_required = user_has_mfa_enabled(db, user.id)
    if mfa_required:
      mfa_token = create_mfa_pending_token(user.id, organization_id=organization_id, role=user.role)
      return {"mfa_required": True, "mfa_token": mfa_token, "login_method": "SSO"}
    mfa_verified = False
  else:
    mfa_verified = False
    mfa_required = False

  session = create_session(
    db, user=user, ip_address=ip, user_agent=user_agent, mfa_verified=mfa_verified,
    auth_method="SSO", identity_provider_id=provider.id,
  )
  policy = get_or_create_policy(db, organization_id)
  token = create_access_token(
    user.id,
    {"role": user.role, "org": organization_id, "sid": session.id, "sso": True, "idp": provider.code},
    expires_minutes=policy.session_duration_minutes,
  )
  user.last_login_at = _utcnow()
  return {"access_token": token, "login_method": "SSO", "provider": provider.name}


def verify_break_glass(db: Session, *, token: str, organization_id: str) -> bool:
  settings = id_svc.get_or_create_identity_settings(db, organization_id)
  if not settings.break_glass_enabled:
    return False
  secret = resolve_secret(settings.break_glass_secret_ref)
  return bool(secret and secrets.compare_digest(secret, token))

def is_local_login_allowed(db: Session, user: User) -> tuple[bool, str | None]:
  if user.role in ("superadmin", "platform_admin"):
    return True, None
  settings = id_svc.get_or_create_identity_settings(db, user.organization_id)
  if settings.auth_mode == AuthMode.SOLO_SSO:
    return False, "El inicio de sesión local está deshabilitado. Use inicio de sesión empresarial."
  return True, None
