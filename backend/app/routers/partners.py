"""API — MB-03 Partners / Aliados comerciales."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.partner_models import PARTNER_ESTADOS, PARTNER_SCOPE_CODES, PARTNER_USER_ROLES
from app.permissions import require_permission, user_permissions
from app.services import partner_service as svc

router = APIRouter(prefix="/api/partners", tags=["Partners"])


class PartnerCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    codigo: str | None = Field(None, max_length=40)
    razon_social: str | None = Field(None, max_length=300)
    estado: str = "BORRADOR"
    tipo_relacion: str = "CONSULTOR"
    contacto_nombre: str | None = Field(None, max_length=200)
    contacto_email: str | None = Field(None, max_length=200)
    contacto_telefono: str | None = Field(None, max_length=40)
    alcance_descripcion: str | None = None
    notas_internas: str | None = None


class PartnerUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=200)
    razon_social: str | None = None
    tipo_relacion: str | None = None
    contacto_nombre: str | None = None
    contacto_email: str | None = None
    contacto_telefono: str | None = None
    alcance_descripcion: str | None = None
    notas_internas: str | None = None


class PartnerEstadoBody(BaseModel):
    estado: str


class GrantOrganizationBody(BaseModel):
    organization_id: str
    alcance: list[str] | None = None
    notas: str | None = None


class UpdateAlcanceBody(BaseModel):
    alcance: list[str]


class AssignUserBody(BaseModel):
    user_id: str
    rol: str = "OPERADOR"


@router.get("/meta/catalogo")
def partner_catalogo(
    user: User = Depends(require_permission("partners.view")),
):
    return {
        "estados": sorted(PARTNER_ESTADOS),
        "roles_usuario": sorted(PARTNER_USER_ROLES),
        "alcances": sorted(PARTNER_SCOPE_CODES),
        "tipos_relacion": ["CONSULTOR", "INTEGRADOR", "DISTRIBUIDOR", "ALIADO_ESTRATEGICO"],
    }


@router.get("")
def list_partners(
    estado: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.list_partners(db, user, estado=estado, q=q)


@router.post("", status_code=201)
def create_partner(
    body: PartnerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.manage")),
):
    p = svc.create_partner(db, user, **body.model_dump())
    db.commit()
    return svc.partner_to_dict(p)


@router.get("/{partner_id}")
def get_partner(
    partner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    detail = svc.get_partner_detail(db, user, partner_id)
    return detail


@router.patch("/{partner_id}")
def update_partner(
    partner_id: str,
    body: PartnerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = svc.update_partner(db, user, partner_id, **body.model_dump(exclude_unset=True))
    db.commit()
    return svc.partner_to_dict(p)


@router.post("/{partner_id}/estado")
def set_partner_estado(
    partner_id: str,
    body: PartnerEstadoBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("partners.manage")),
):
    p = svc.set_partner_estado(db, user, partner_id, body.estado)
    db.commit()
    return svc.partner_to_dict(p)


@router.get("/{partner_id}/organizaciones")
def list_partner_organizations(
    partner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    detail = svc.get_partner_detail(db, user, partner_id)
    return {"items": detail["organizaciones"], "total": len(detail["organizaciones"])}


@router.post("/{partner_id}/organizaciones", status_code=201)
def grant_organization(
    partner_id: str,
    body: GrantOrganizationBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not svc.can_manage_partners(user, db):
        if "partners.org.grant" not in user_permissions(user, db):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Sin permiso para conceder organizaciones")
    grant = svc.grant_organization(
        db, user, partner_id, body.organization_id, alcance=body.alcance, notas=body.notas,
    )
    db.commit()
    return svc.grant_to_dict(grant)


@router.post("/{partner_id}/organizaciones/{grant_id}/revocar")
def revoke_organization(
    partner_id: str,
    grant_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    grant = svc.revoke_organization_grant(db, user, partner_id, grant_id)
    db.commit()
    return svc.grant_to_dict(grant)


@router.patch("/{partner_id}/organizaciones/{grant_id}/alcance")
def update_grant_alcance(
    partner_id: str,
    grant_id: str,
    body: UpdateAlcanceBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    grant = svc.update_grant_alcance(db, user, partner_id, grant_id, body.alcance)
    db.commit()
    return svc.grant_to_dict(grant)


@router.post("/{partner_id}/usuarios", status_code=201)
def assign_user(
    partner_id: str,
    body: AssignUserBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not svc.can_manage_partners(user, db):
        if "partners.user.assign" not in user_permissions(user, db):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Sin permiso para asignar usuarios")
    m = svc.assign_user(db, user, partner_id, body.user_id, rol=body.rol)
    db.commit()
    return svc.membership_to_dict(m)


@router.post("/{partner_id}/usuarios/{membership_id}/revocar")
def revoke_user(
    partner_id: str,
    membership_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    m = svc.revoke_user_membership(db, user, partner_id, membership_id)
    db.commit()
    return svc.membership_to_dict(m)


@router.get("/{partner_id}/auditoria")
def list_audit(
    partner_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    events = svc.list_audit_events(db, user, partner_id, limit=limit)
    return {"items": events, "total": len(events)}


@router.get("/{partner_id}/organizaciones/{organization_id}/contexto")
def org_context(
    partner_id: str,
    organization_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ctx = svc.get_org_context_for_partner(db, user, partner_id, organization_id)
    return ctx


@router.get("/{partner_id}/mis-organizaciones")
def my_organizations(
    partner_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = svc.list_my_partner_organizations(db, user, partner_id)
    return {"items": items, "total": len(items)}
