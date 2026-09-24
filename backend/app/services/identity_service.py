"""Servicio de identidad — CRUD proveedores, políticas y mapeos (1370)."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gateway.secrets import build_env_secret_ref, secret_configured
from app.identity_enums import AuthMode, FORBIDDEN_AUTO_ROLES, IdPStatus, IdPType, MfaSsoMode
from app.identity_models import (
  IdentityGroupRoleMapping,
  IdentityLoginAudit,
  IdentityProvider,
  OrganizationIdentitySettings,
)
from app.models import Organization, User
from app.tenant_scope import ORG_STATUS_ACTIVE


class IdentityValidationError(ValueError):
  pass


def _utcnow() -> datetime:
  return datetime.now(timezone.utc)


def _json(obj: Any) -> str:
  return json.dumps(obj, ensure_ascii=False, default=str)


def _parse_json(raw: str | None) -> Any:
  if not raw:
    return None
  try:
    return json.loads(raw)
  except json.JSONDecodeError:
    return None


def get_or_create_identity_settings(db: Session, organization_id: str) -> OrganizationIdentitySettings:
  row = db.query(OrganizationIdentitySettings).filter(
    OrganizationIdentitySettings.organization_id == organization_id
  ).first()
  if row:
    return row
  row = OrganizationIdentitySettings(organization_id=organization_id)
  db.add(row)
  db.flush()
  return row


def identity_settings_to_dict(row: OrganizationIdentitySettings) -> dict[str, Any]:
  return {
    "auth_mode": row.auth_mode,
    "mfa_sso_mode": row.mfa_sso_mode,
    "auto_provision_enabled": row.auto_provision_enabled,
    "default_role_on_provision": row.default_role_on_provision,
    "allowed_domains": _parse_json(row.allowed_domains_json) or [],
    "org_discovery_code": row.org_discovery_code,
    "attribute_mapping": _parse_json(row.attribute_mapping_json) or {},
    "break_glass_enabled": row.break_glass_enabled,
    "break_glass_configured": secret_configured(row.break_glass_secret_ref),
    "scim_prepared": row.scim_prepared,
    "scim_enabled": row.scim_enabled,
  }


def update_identity_settings(db: Session, organization_id: str, data: dict, user_id: str | None) -> OrganizationIdentitySettings:
  row = get_or_create_identity_settings(db, organization_id)
  if "auth_mode" in data and data["auth_mode"]:
    mode = str(data["auth_mode"]).upper()
    if mode not in AuthMode.ALL:
      raise IdentityValidationError("Modo de autenticación no válido")
    row.auth_mode = mode
  if "mfa_sso_mode" in data and data["mfa_sso_mode"]:
    row.mfa_sso_mode = str(data["mfa_sso_mode"]).upper()
  if "auto_provision_enabled" in data:
    row.auto_provision_enabled = bool(data["auto_provision_enabled"])
  if "default_role_on_provision" in data and data["default_role_on_provision"]:
    role = str(data["default_role_on_provision"]).lower()
    if role in FORBIDDEN_AUTO_ROLES:
      raise IdentityValidationError("Rol no permitido para auto-provisión")
    row.default_role_on_provision = role
  if "allowed_domains" in data:
    row.allowed_domains_json = _json(data["allowed_domains"])
  if "org_discovery_code" in data:
    row.org_discovery_code = data["org_discovery_code"]
  if "attribute_mapping" in data:
    row.attribute_mapping_json = _json(data["attribute_mapping"])
  if data.get("break_glass_env_var"):
    row.break_glass_secret_ref = build_env_secret_ref(data["break_glass_env_var"])
  db.flush()
  write_audit(db, action="identidad.politica.actualizada", organization_id=organization_id, user_id=user_id,
              detail=_json({"auth_mode": row.auth_mode}), commit=False)
  return row


def provider_to_dict(row: IdentityProvider) -> dict[str, Any]:
  config = _parse_json(row.config_json) or {}
  safe_config = {k: v for k, v in config.items() if "secret" not in k.lower() and "mock_hmac" not in k}
  return {
    "id": row.id,
    "code": row.code,
    "name": row.name,
    "provider_type": row.provider_type,
    "vendor_hint": row.vendor_hint,
    "status": row.status,
    "is_default": row.is_default,
    "secret_configured": secret_configured(row.secret_ref),
    "config": safe_config,
    "saml_cert_fingerprint": row.saml_cert_fingerprint,
    "saml_cert_not_after": row.saml_cert_not_after.isoformat() if row.saml_cert_not_after else None,
    "health": {
      "last_test_at": row.last_test_at.isoformat() if row.last_test_at else None,
      "last_test_result": row.last_test_result,
      "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None,
      "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
      "last_error_message": row.last_error_message,
    },
  }


def _get_provider(db: Session, organization_id: str, provider_id: str) -> IdentityProvider:
  row = db.query(IdentityProvider).filter(
    IdentityProvider.id == provider_id,
    IdentityProvider.organization_id == organization_id,
    IdentityProvider.is_active.is_(True),
  ).first()
  if not row:
    raise HTTPException(status_code=404, detail="Proveedor no encontrado")
  return row


def list_providers(db: Session, organization_id: str) -> list[IdentityProvider]:
  return (
    db.query(IdentityProvider)
    .filter(IdentityProvider.organization_id == organization_id, IdentityProvider.is_active.is_(True))
    .order_by(IdentityProvider.name)
    .all()
  )


def create_provider(db: Session, organization_id: str, data: dict, user_id: str | None) -> IdentityProvider:
  org = db.query(Organization).filter(Organization.id == organization_id).first()
  if not org or org.status != ORG_STATUS_ACTIVE:
    raise IdentityValidationError("Organización no disponible")
  ptype = str(data.get("provider_type", "")).upper()
  if ptype not in IdPType.ALL:
    raise IdentityValidationError("Tipo de proveedor no válido")
  code = str(data["code"]).strip().lower()
  exists = db.query(IdentityProvider).filter(
    IdentityProvider.organization_id == organization_id, IdentityProvider.code == code
  ).first()
  if exists:
    raise IdentityValidationError("Ya existe un proveedor con ese código")
  secret_ref = build_env_secret_ref(data["secret_env_var"]) if data.get("secret_env_var") else None
  config = data.get("config") or {}
  if secret_ref:
    config["secret_ref"] = secret_ref
  row = IdentityProvider(
    organization_id=organization_id,
    code=code,
    name=data["name"],
    provider_type=ptype,
    vendor_hint=data.get("vendor_hint"),
    status=IdPStatus.BORRADOR,
    is_default=bool(data.get("is_default")),
    secret_ref=secret_ref,
    config_json=_json(config),
    saml_cert_fingerprint=data.get("saml_cert_fingerprint"),
  )
  if data.get("is_default"):
    db.query(IdentityProvider).filter(IdentityProvider.organization_id == organization_id).update({"is_default": False})
  db.add(row)
  db.flush()
  write_audit(db, action="identidad.proveedor.creado", organization_id=organization_id, user_id=user_id,
              detail=_json({"provider_id": row.id, "code": code}), commit=False)
  return row


def update_provider(db: Session, organization_id: str, provider_id: str, data: dict, user_id: str | None) -> IdentityProvider:
  row = _get_provider(db, organization_id, provider_id)
  for field in ("name", "vendor_hint", "status", "saml_cert_fingerprint"):
    if field in data and data[field] is not None:
      setattr(row, field, data[field])
  if "config" in data:
    config = data["config"] or {}
    if row.secret_ref:
      config["secret_ref"] = row.secret_ref
    row.config_json = _json(config)
  if data.get("secret_env_var"):
    row.secret_ref = build_env_secret_ref(data["secret_env_var"])
  if data.get("is_default"):
    db.query(IdentityProvider).filter(IdentityProvider.organization_id == organization_id).update({"is_default": False})
    row.is_default = True
  db.flush()
  write_audit(db, action="identidad.proveedor.editado", organization_id=organization_id, user_id=user_id,
              detail=_json({"provider_id": provider_id}), commit=False)
  return row


def test_provider(db: Session, organization_id: str, provider_id: str, user_id: str | None) -> dict:
  row = _get_provider(db, organization_id, provider_id)
  config = _parse_json(row.config_json) or {}
  try:
    if row.provider_type == IdPType.OIDC:
      from app.services.oidc_service import discover_oidc
      discover_oidc(config)
    else:
      if not config.get("sso_url"):
        raise IdentityValidationError("SSO URL SAML requerida")
    row.status = IdPStatus.VERIFICADO
    row.last_test_at = _utcnow()
    row.last_test_result = "EXITOSA"
    row.last_error_message = None
    write_audit(db, action="identidad.proveedor.probado", organization_id=organization_id, user_id=user_id,
                detail=_json({"provider_id": provider_id, "result": "EXITOSA"}), commit=False)
    return {"resultado": "EXITOSA", "mensaje": "Configuración verificada correctamente"}
  except Exception as exc:
    row.status = IdPStatus.ERROR
    row.last_test_at = _utcnow()
    row.last_test_result = "FALLIDA"
    row.last_error_at = _utcnow()
    row.last_error_message = str(exc)[:500]
    return {"resultado": "FALLIDA", "mensaje": str(exc)}


def activate_provider(db: Session, organization_id: str, provider_id: str, user_id: str | None) -> IdentityProvider:
  row = _get_provider(db, organization_id, provider_id)
  settings = get_or_create_identity_settings(db, organization_id)
  if settings.auth_mode == AuthMode.SOLO_SSO and row.status not in (IdPStatus.VERIFICADO, IdPStatus.ACTIVO):
    if row.last_test_result != "EXITOSA":
      raise IdentityValidationError("Debe probar el proveedor antes de activar en modo Solo SSO")
  row.status = IdPStatus.ACTIVO
  write_audit(db, action="identidad.proveedor.activado", organization_id=organization_id, user_id=user_id,
              detail=_json({"provider_id": provider_id}), commit=False)
  return row


def deactivate_provider(db: Session, organization_id: str, provider_id: str, user_id: str | None) -> IdentityProvider:
  row = _get_provider(db, organization_id, provider_id)
  row.status = IdPStatus.DESHABILITADO
  write_audit(db, action="identidad.proveedor.desactivado", organization_id=organization_id, user_id=user_id,
              detail=_json({"provider_id": provider_id}), commit=False)
  return row


def list_group_mappings(db: Session, organization_id: str, provider_id: str) -> list[dict]:
  _get_provider(db, organization_id, provider_id)
  rows = db.query(IdentityGroupRoleMapping).filter(
    IdentityGroupRoleMapping.organization_id == organization_id,
    IdentityGroupRoleMapping.provider_id == provider_id,
    IdentityGroupRoleMapping.is_active.is_(True),
  ).all()
  return [{"id": r.id, "external_group": r.external_group, "role_code": r.role_code} for r in rows]


def upsert_group_mapping(db: Session, organization_id: str, provider_id: str, data: dict, user_id: str | None) -> dict:
  _get_provider(db, organization_id, provider_id)
  role = str(data["role_code"]).lower()
  if role in FORBIDDEN_AUTO_ROLES:
    raise IdentityValidationError("Rol no permitido en mapeo de grupos")
  group = str(data["external_group"]).strip()
  row = db.query(IdentityGroupRoleMapping).filter(
    IdentityGroupRoleMapping.organization_id == organization_id,
    IdentityGroupRoleMapping.provider_id == provider_id,
    IdentityGroupRoleMapping.external_group == group,
  ).first()
  if not row:
    row = IdentityGroupRoleMapping(
      organization_id=organization_id,
      provider_id=provider_id,
      external_group=group,
      role_code=role,
    )
    db.add(row)
  else:
    row.role_code = role
    row.is_active = True
  db.flush()
  write_audit(db, action="identidad.mapeo.actualizado", organization_id=organization_id, user_id=user_id,
              detail=_json({"group": group, "role": role}), commit=False)
  return {"id": row.id, "external_group": group, "role_code": role}


def discover_login_options(db: Session, *, org_code: str | None = None, domain: str | None = None) -> dict:
  if not org_code and not domain:
    return {"providers": [], "auth_mode": None}
  q = db.query(OrganizationIdentitySettings)
  if org_code:
    settings = q.filter(OrganizationIdentitySettings.org_discovery_code == org_code).first()
  else:
    settings = None
    for row in q.all():
      domains = _parse_json(row.allowed_domains_json) or []
      if domain and domain.lower() in [d.lower() for d in domains]:
        settings = row
        break
  if not settings or settings.auth_mode == AuthMode.SOLO_LOCAL:
    return {"providers": [], "auth_mode": settings.auth_mode if settings else None}
  providers = db.query(IdentityProvider).filter(
    IdentityProvider.organization_id == settings.organization_id,
    IdentityProvider.status == IdPStatus.ACTIVO,
    IdentityProvider.is_active.is_(True),
  ).all()
  return {
    "auth_mode": settings.auth_mode,
    "providers": [{"id": p.id, "name": p.name, "provider_type": p.provider_type, "is_default": p.is_default} for p in providers],
  }


def log_login_audit(
  db: Session, *, organization_id: str, user_id: str | None, provider_id: str | None,
  login_method: str, result: str, detail: str | None = None, ip_address: str | None = None,
) -> None:
  db.add(IdentityLoginAudit(
    organization_id=organization_id,
    user_id=user_id,
    provider_id=provider_id,
    login_method=login_method,
    result=result,
    detail=detail[:500] if detail else None,
    ip_address=ip_address,
  ))


def list_login_audits(db: Session, organization_id: str, limit: int = 50) -> list[IdentityLoginAudit]:
  return (
    db.query(IdentityLoginAudit)
    .filter(IdentityLoginAudit.organization_id == organization_id)
    .order_by(IdentityLoginAudit.created_at.desc())
    .limit(limit)
    .all()
  )


def generate_discovery_code() -> str:
  return secrets.token_hex(4)
