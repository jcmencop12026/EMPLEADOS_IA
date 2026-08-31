"""Router — Identidad empresarial, SSO, OIDC y SAML (1370)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission, require_permission
from app.schemas_identity import (
  BreakGlassRequest,
  GroupRoleMappingCreate,
  IdentityProviderCreate,
  IdentityProviderUpdate,
  IdentitySettingsUpdate,
  LoginDiscoverRequest,
  OidcCallbackRequest,
  SamlAcsRequest,
)
from app.schemas import TokenResponse
from app.schemas_security import MfaChallengeResponse
from app.services import identity_service as svc
from app.services import sso_login_service as sso_svc
from app.services.request_context import client_ip, client_user_agent
from app.services.security_event_service import log_security_event
from app.security import verify_password
from app.models import Organization
from app.routers.auth import _issue_session_token
from typing import Union

router = APIRouter(prefix="/api/identidad", tags=["identidad"])


def _validation_error(exc: svc.IdentityValidationError) -> HTTPException:
  return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/politica")
def get_policy(user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
  row = svc.get_or_create_identity_settings(db, user.organization_id)
  return svc.identity_settings_to_dict(row)


@router.put("/politica")
def update_policy(
  body: IdentitySettingsUpdate,
  user: User = Depends(require_permission("identidad.manage")),
  db: Session = Depends(get_db),
):
  try:
    row = svc.update_identity_settings(db, user.organization_id, body.model_dump(exclude_none=True), user.id)
    db.commit()
    return svc.identity_settings_to_dict(row)
  except svc.IdentityValidationError as exc:
    db.rollback()
    raise _validation_error(exc) from exc


@router.get("/proveedores")
def list_providers(user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
  return [svc.provider_to_dict(p) for p in svc.list_providers(db, user.organization_id)]


@router.post("/proveedores", status_code=status.HTTP_201_CREATED)
def create_provider(
  body: IdentityProviderCreate,
  user: User = Depends(require_permission("identidad.manage")),
  db: Session = Depends(get_db),
):
  try:
    row = svc.create_provider(db, user.organization_id, body.model_dump(), user.id)
    db.commit()
    return svc.provider_to_dict(row)
  except svc.IdentityValidationError as exc:
    db.rollback()
    raise _validation_error(exc) from exc


@router.get("/proveedores/{provider_id}")
def get_provider(provider_id: str, user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
  from app.identity_models import IdentityProvider
  row = db.query(IdentityProvider).filter(
    IdentityProvider.id == provider_id, IdentityProvider.organization_id == user.organization_id
  ).first()
  if not row:
    raise HTTPException(status_code=404, detail="Proveedor no encontrado")
  return svc.provider_to_dict(row)


@router.put("/proveedores/{provider_id}")
def update_provider(
  provider_id: str,
  body: IdentityProviderUpdate,
  user: User = Depends(require_permission("identidad.manage")),
  db: Session = Depends(get_db),
):
  row = svc.update_provider(db, user.organization_id, provider_id, body.model_dump(exclude_none=True), user.id)
  db.commit()
  return svc.provider_to_dict(row)


@router.post("/proveedores/{provider_id}/probar")
def test_provider(provider_id: str, user: User = Depends(require_permission("identidad.test")), db: Session = Depends(get_db)):
  result = svc.test_provider(db, user.organization_id, provider_id, user.id)
  db.commit()
  return result


@router.post("/proveedores/{provider_id}/activar")
def activate_provider(provider_id: str, user: User = Depends(require_permission("identidad.activate")), db: Session = Depends(get_db)):
  try:
    row = svc.activate_provider(db, user.organization_id, provider_id, user.id)
    db.commit()
    return svc.provider_to_dict(row)
  except svc.IdentityValidationError as exc:
    db.rollback()
    raise _validation_error(exc) from exc


@router.post("/proveedores/{provider_id}/desactivar")
def deactivate_provider(provider_id: str, user: User = Depends(require_permission("identidad.activate")), db: Session = Depends(get_db)):
  row = svc.deactivate_provider(db, user.organization_id, provider_id, user.id)
  db.commit()
  return svc.provider_to_dict(row)


@router.get("/proveedores/{provider_id}/mapeos-roles")
def list_mappings(provider_id: str, user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
  return svc.list_group_mappings(db, user.organization_id, provider_id)


@router.post("/proveedores/{provider_id}/mapeos-roles")
def create_mapping(
  provider_id: str,
  body: GroupRoleMappingCreate,
  user: User = Depends(require_permission("identidad.manage")),
  db: Session = Depends(get_db),
):
  try:
    result = svc.upsert_group_mapping(db, user.organization_id, provider_id, body.model_dump(), user.id)
    db.commit()
    return result
  except svc.IdentityValidationError as exc:
    db.rollback()
    raise _validation_error(exc) from exc


@router.post("/descubrir")
def discover_login(body: LoginDiscoverRequest, db: Session = Depends(get_db)):
  return svc.discover_login_options(db, org_code=body.org_code, domain=body.domain)


@router.post("/public/oidc/{provider_id}/iniciar")
def begin_oidc_public(provider_id: str, body: LoginDiscoverRequest, db: Session = Depends(get_db)):
  if not body.org_code:
    raise HTTPException(status_code=400, detail="Código de organización requerido")
  from app.identity_models import OrganizationIdentitySettings
  settings = db.query(OrganizationIdentitySettings).filter(
    OrganizationIdentitySettings.org_discovery_code == body.org_code
  ).first()
  if not settings:
    raise HTTPException(status_code=404, detail="Configuración no encontrada")
  try:
    result = sso_svc.begin_oidc(db, settings.organization_id, provider_id)
    db.commit()
    return result
  except sso_svc.SsoLoginError as exc:
    db.rollback()
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/oidc/{provider_id}/iniciar")
def begin_oidc(provider_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  check_permission(user, "identidad.view", db)
  try:
    result = sso_svc.begin_oidc(db, user.organization_id, provider_id)
    db.commit()
    return result
  except sso_svc.SsoLoginError as exc:
    db.rollback()
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/oidc/callback", response_model=Union[TokenResponse, MfaChallengeResponse])
def oidc_callback(body: OidcCallbackRequest, request: Request, db: Session = Depends(get_db)):
  try:
    result = sso_svc.complete_oidc(db, state=body.state, code=body.code, ip=client_ip(request), user_agent=client_user_agent(request))
    db.commit()
    if result.get("mfa_required"):
      return MfaChallengeResponse(mfa_token=result["mfa_token"])
    return TokenResponse(access_token=result["access_token"])
  except sso_svc.SsoLoginError as exc:
    db.commit()
    raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/saml/{provider_id}/iniciar")
def begin_saml(provider_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  check_permission(user, "identidad.view", db)
  try:
    result = sso_svc.begin_saml(db, user.organization_id, provider_id)
    db.commit()
    return result
  except sso_svc.SsoLoginError as exc:
    db.rollback()
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/saml/acs", response_model=Union[TokenResponse, MfaChallengeResponse])
def saml_acs(body: SamlAcsRequest, request: Request, db: Session = Depends(get_db)):
  try:
    result = sso_svc.complete_saml(
      db, relay_state=body.relay_state, saml_response=body.saml_response,
      ip=client_ip(request), user_agent=client_user_agent(request),
    )
    db.commit()
    if result.get("mfa_required"):
      return MfaChallengeResponse(mfa_token=result["mfa_token"])
    return TokenResponse(access_token=result["access_token"])
  except sso_svc.SsoLoginError as exc:
    db.commit()
    raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/eventos")
def login_events(user: User = Depends(require_permission("identidad.audit")), db: Session = Depends(get_db)):
  rows = svc.list_login_audits(db, user.organization_id)
  return [
    {
      "id": r.id, "login_method": r.login_method, "result": r.result,
      "user_id": r.user_id, "provider_id": r.provider_id,
      "detail": r.detail, "ip_address": r.ip_address, "created_at": r.created_at,
    }
    for r in rows
  ]


@router.post("/break-glass", response_model=TokenResponse)
def break_glass_login(body: BreakGlassRequest, request: Request, db: Session = Depends(get_db)):
  user = db.query(User).filter(User.username == body.username).first()
  if not user or not verify_password(body.password, user.password_hash):
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")
  if user.role not in ("superadmin", "platform_admin"):
    raise HTTPException(status_code=403, detail="Acceso de emergencia no autorizado para este usuario")
  if not sso_svc.verify_break_glass(db, token=body.break_glass_token, organization_id=user.organization_id):
    log_security_event(db, organization_id=user.organization_id, user_id=user.id, event_type="BREAK_GLASS_FALLIDO",
                       ip_address=client_ip(request))
    db.commit()
    raise HTTPException(status_code=403, detail="Token de emergencia inválido")
  org = db.query(Organization).filter(Organization.id == user.organization_id).first()
  if not org or org.status != "ACTIVE":
    raise HTTPException(status_code=403, detail="Organización no disponible")
  token = _issue_session_token(db, user, ip=client_ip(request), user_agent=client_user_agent(request), mfa_verified=True)
  log_security_event(db, organization_id=user.organization_id, user_id=user.id, event_type="BREAK_GLASS_USADO",
                     ip_address=client_ip(request))
  svc.log_login_audit(db, organization_id=user.organization_id, user_id=user.id, provider_id=None,
                      login_method="BREAK_GLASS", result="EXITOSO", ip_address=client_ip(request))
  db.commit()
  return TokenResponse(access_token=token)


# --- SCIM administración (1380) ---

@router.get("/scim/estado")
def scim_status(user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
    from app.services.scim_auth_service import is_scim_enabled, list_tokens
    from app.services.scim_audit import get_metrics, list_audit
    from app.scim_models import ScimConflict
    settings = svc.get_or_create_identity_settings(db, user.organization_id)
    conflicts = db.query(ScimConflict).filter(
        ScimConflict.organization_id == user.organization_id, ScimConflict.resolved.is_(False)
    ).count()
    return {
        "scim_enabled": is_scim_enabled(db, user.organization_id),
        "scim_base_url": "/scim/v2",
        "metrics": get_metrics(db, user.organization_id),
        "tokens": list_tokens(db, user.organization_id),
        "conflicts_pending": conflicts,
        "recent_events": [
            {"action": e.action, "result": e.result, "detail": e.detail, "created_at": e.created_at.isoformat()}
            for e in list_audit(db, user.organization_id, limit=10)
        ],
    }


@router.put("/scim/configuracion")
def scim_configure(
    body: dict,
    user: User = Depends(require_permission("identidad.manage")),
    db: Session = Depends(get_db),
):
    from app.services.scim_auth_service import set_scim_enabled
    enabled = bool(body.get("scim_enabled", False))
    set_scim_enabled(db, user.organization_id, enabled)
    db.commit()
    return {"scim_enabled": enabled, "message": "Configuración SCIM actualizada"}


@router.post("/scim/tokens")
def scim_create_token(
    body: dict,
    user: User = Depends(require_permission("identidad.manage")),
    db: Session = Depends(get_db),
):
    from app.services.scim_auth_service import create_token, set_scim_enabled
    set_scim_enabled(db, user.organization_id, True)
    row, plain = create_token(db, user.organization_id, name=body.get("name", "Token SCIM"), expires_days=body.get("expires_days"))
    db.commit()
    return {
        "id": row.id,
        "token": plain,
        "token_prefix": row.token_prefix,
        "message": "Guarde este token ahora. No se volverá a mostrar.",
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


@router.post("/scim/tokens/{token_id}/rotar")
def scim_rotate_token(token_id: str, user: User = Depends(require_permission("identidad.manage")), db: Session = Depends(get_db)):
    from app.services.scim_auth_service import rotate_token
    row, plain = rotate_token(db, user.organization_id, token_id)
    db.commit()
    return {"id": row.id, "token": plain, "message": "Token rotado. Guarde el nuevo token ahora."}


@router.post("/scim/tokens/{token_id}/revocar")
def scim_revoke_token(token_id: str, user: User = Depends(require_permission("identidad.manage")), db: Session = Depends(get_db)):
    from app.services.scim_auth_service import revoke_token
    revoke_token(db, user.organization_id, token_id)
    db.commit()
    return {"message": "Token revocado"}


@router.get("/scim/mapeos-roles")
def scim_list_mappings(user: User = Depends(require_permission("identidad.view")), db: Session = Depends(get_db)):
    from app.services.scim_group_service import list_group_role_mappings
    return list_group_role_mappings(db, user.organization_id)


@router.post("/scim/mapeos-roles")
def scim_upsert_mapping(
    body: dict,
    user: User = Depends(require_permission("identidad.manage")),
    db: Session = Depends(get_db),
):
    from app.services.scim_group_service import upsert_group_role_mapping
    try:
        result = upsert_group_role_mapping(db, user.organization_id, body["external_group"], body["role_code"])
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/scim/conflictos")
def scim_conflicts(user: User = Depends(require_permission("identidad.audit")), db: Session = Depends(get_db)):
    from app.scim_models import ScimConflict
    rows = db.query(ScimConflict).filter(
        ScimConflict.organization_id == user.organization_id, ScimConflict.resolved.is_(False)
    ).order_by(ScimConflict.created_at.desc()).limit(50).all()
    return [
        {"id": r.id, "conflict_type": r.conflict_type, "external_id": r.external_id, "detail": r.detail, "created_at": r.created_at.isoformat()}
        for r in rows
    ]
