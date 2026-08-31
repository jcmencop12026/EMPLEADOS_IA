"""Servicio — MB-03 Partners / Aliados."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Organization, User
from app.partner_models import (
    GRANT_ESTADOS,
    PARTNER_ESTADOS,
    PARTNER_SCOPE_CODES,
    PARTNER_USER_ROLES,
    Partner,
    PartnerAuditEvent,
    PartnerOrganizationGrant,
    PartnerUserMembership,
)
from app.permissions import user_permissions

_DEFAULT_ALCANCE = ["organizacion.read"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _audit(
    db: Session,
    *,
    partner_id: str,
    action: str,
    actor_id: str | None,
    organization_id: str | None = None,
    user_id: str | None = None,
    detail: dict | None = None,
) -> None:
    db.add(
        PartnerAuditEvent(
            partner_id=partner_id,
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            detail_json=json.dumps(detail or {}, ensure_ascii=False),
            actor_id=actor_id,
        )
    )


def _next_codigo(db: Session) -> str:
    count = db.query(Partner).count()
    return f"PTR-{count + 1:04d}"


def _get_partner(db: Session, partner_id: str) -> Partner:
    p = db.query(Partner).filter(Partner.id == partner_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Partner no encontrado")
    return p


def _partner_active(p: Partner) -> bool:
    if p.estado != "ACTIVO":
        return False
    now = _utcnow()
    if p.valid_from and p.valid_from > now:
        return False
    if p.valid_until and p.valid_until < now:
        return False
    return True


def _grant_active(g: PartnerOrganizationGrant) -> bool:
    if g.estado != "ACTIVO":
        return False
    now = _utcnow()
    if g.valid_from and g.valid_from > now:
        return False
    if g.valid_until and g.valid_until < now:
        return False
    return True


def can_manage_partners(user: User, db: Session) -> bool:
    return "partners.manage" in user_permissions(user, db)


def can_view_partners(user: User, db: Session) -> bool:
    return "partners.view" in user_permissions(user, db) or can_manage_partners(user, db)


def get_membership(db: Session, user_id: str, partner_id: str) -> PartnerUserMembership | None:
    return (
        db.query(PartnerUserMembership)
        .filter(
            PartnerUserMembership.partner_id == partner_id,
            PartnerUserMembership.user_id == user_id,
            PartnerUserMembership.is_active.is_(True),
        )
        .first()
    )


def assert_partner_access(
    db: Session,
    user: User,
    partner_id: str,
    *,
    require_manage: bool = False,
    require_membership: bool = False,
) -> Partner:
    partner = _get_partner(db, partner_id)
    if can_manage_partners(user, db):
        return partner
    membership = get_membership(db, user.id, partner_id)
    if require_manage:
        if not membership or membership.rol != "ADMIN":
            raise HTTPException(status_code=403, detail="Sin permiso para administrar este partner")
        return partner
    if require_membership and not membership:
        raise HTTPException(status_code=403, detail="No es miembro de este partner")
    if not membership and not can_view_partners(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para ver partners")
    return partner


def assert_org_grant(
    db: Session,
    user: User,
    partner_id: str,
    organization_id: str,
    scope: str,
) -> PartnerOrganizationGrant:
    membership = get_membership(db, user.id, partner_id)
    if membership:
        partner = assert_partner_access(db, user, partner_id, require_membership=True)
    elif can_manage_partners(user, db):
        partner = _get_partner(db, partner_id)
    else:
        raise HTTPException(status_code=403, detail="No es miembro de este partner")
    if not _partner_active(partner):
        raise HTTPException(status_code=403, detail="Partner inactivo o fuera de vigencia")
    grant = (
        db.query(PartnerOrganizationGrant)
        .filter(
            PartnerOrganizationGrant.partner_id == partner_id,
            PartnerOrganizationGrant.organization_id == organization_id,
        )
        .first()
    )
    if not grant or not _grant_active(grant):
        raise HTTPException(status_code=403, detail="Sin acceso autorizado a esta organización")
    scopes = _json_loads(grant.alcance_json, [])
    if scope not in scopes:
        raise HTTPException(status_code=403, detail=f"Alcance '{scope}' no concedido")
    return grant


def partner_to_dict(p: Partner) -> dict[str, Any]:
    return {
        "id": p.id,
        "codigo": p.codigo,
        "nombre": p.nombre,
        "razon_social": p.razon_social,
        "estado": p.estado,
        "tipo_relacion": p.tipo_relacion,
        "contacto_nombre": p.contacto_nombre,
        "contacto_email": p.contacto_email,
        "contacto_telefono": p.contacto_telefono,
        "alcance_descripcion": p.alcance_descripcion,
        "valid_from": p.valid_from.isoformat() if p.valid_from else None,
        "valid_until": p.valid_until.isoformat() if p.valid_until else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def grant_to_dict(g: PartnerOrganizationGrant, org: Organization | None = None) -> dict[str, Any]:
    return {
        "id": g.id,
        "partner_id": g.partner_id,
        "organization_id": g.organization_id,
        "organization_name": org.name if org else None,
        "estado": g.estado,
        "alcance": _json_loads(g.alcance_json, []),
        "valid_from": g.valid_from.isoformat() if g.valid_from else None,
        "valid_until": g.valid_until.isoformat() if g.valid_until else None,
        "notas": g.notas,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def membership_to_dict(m: PartnerUserMembership, user: User | None = None) -> dict[str, Any]:
    return {
        "id": m.id,
        "partner_id": m.partner_id,
        "user_id": m.user_id,
        "username": user.username if user else None,
        "full_name": user.full_name if user else None,
        "rol": m.rol,
        "is_active": m.is_active,
        "assigned_at": m.assigned_at.isoformat() if m.assigned_at else None,
    }


def list_partners(
    db: Session,
    user: User,
    *,
    estado: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    if can_manage_partners(user, db) or can_view_partners(user, db):
        query = db.query(Partner)
    else:
        partner_ids = [
            m.partner_id
            for m in db.query(PartnerUserMembership)
            .filter(PartnerUserMembership.user_id == user.id, PartnerUserMembership.is_active.is_(True))
            .all()
        ]
        if not partner_ids:
            return {"items": [], "total": 0}
        query = db.query(Partner).filter(Partner.id.in_(partner_ids))
    if estado:
        query = query.filter(Partner.estado == estado)
    if q:
        like = f"%{q}%"
        query = query.filter((Partner.nombre.ilike(like)) | (Partner.codigo.ilike(like)))
    rows = query.order_by(Partner.updated_at.desc()).all()
    return {"items": [partner_to_dict(p) for p in rows], "total": len(rows)}


def create_partner(db: Session, user: User, **fields: Any) -> Partner:
    if not can_manage_partners(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para crear partners")
    estado = fields.get("estado", "BORRADOR")
    if estado not in PARTNER_ESTADOS:
        raise HTTPException(status_code=422, detail=f"Estado inválido: {estado}")
    codigo = fields.get("codigo") or _next_codigo(db)
    if db.query(Partner).filter(Partner.codigo == codigo).first():
        raise HTTPException(status_code=409, detail="Código de partner duplicado")
    p = Partner(
        codigo=codigo,
        nombre=fields["nombre"],
        razon_social=fields.get("razon_social"),
        estado=estado,
        tipo_relacion=fields.get("tipo_relacion", "CONSULTOR"),
        contacto_nombre=fields.get("contacto_nombre"),
        contacto_email=fields.get("contacto_email"),
        contacto_telefono=fields.get("contacto_telefono"),
        alcance_descripcion=fields.get("alcance_descripcion"),
        notas_internas=fields.get("notas_internas"),
        created_by=user.id,
    )
    db.add(p)
    db.flush()
    _audit(db, partner_id=p.id, action="partner.create", actor_id=user.id, detail={"codigo": codigo})
    return p


def update_partner(db: Session, user: User, partner_id: str, **fields: Any) -> Partner:
    if can_manage_partners(user, db):
        p = _get_partner(db, partner_id)
    else:
        p = assert_partner_access(db, user, partner_id, require_manage=True)
    allowed = {
        "nombre", "razon_social", "tipo_relacion", "contacto_nombre", "contacto_email",
        "contacto_telefono", "alcance_descripcion", "notas_internas", "valid_from", "valid_until",
    }
    for k, v in fields.items():
        if k in allowed and v is not None:
            setattr(p, k, v)
    p.updated_at = _utcnow()
    _audit(db, partner_id=p.id, action="partner.update", actor_id=user.id)
    return p


def set_partner_estado(db: Session, user: User, partner_id: str, estado: str) -> Partner:
    if estado not in PARTNER_ESTADOS:
        raise HTTPException(status_code=422, detail=f"Estado inválido: {estado}")
    if not can_manage_partners(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para cambiar estado del partner")
    p = _get_partner(db, partner_id)
    p.estado = estado
    p.updated_at = _utcnow()
    _audit(db, partner_id=p.id, action="partner.set_estado", actor_id=user.id, detail={"estado": estado})
    return p


def get_partner_detail(db: Session, user: User, partner_id: str) -> dict[str, Any]:
    p = assert_partner_access(db, user, partner_id)
    grants = (
        db.query(PartnerOrganizationGrant, Organization)
        .join(Organization, Organization.id == PartnerOrganizationGrant.organization_id)
        .filter(PartnerOrganizationGrant.partner_id == partner_id)
        .all()
    )
    members = (
        db.query(PartnerUserMembership, User)
        .join(User, User.id == PartnerUserMembership.user_id)
        .filter(PartnerUserMembership.partner_id == partner_id)
        .all()
    )
    return {
        **partner_to_dict(p),
        "organizaciones": [grant_to_dict(g, org) for g, org in grants],
        "usuarios": [membership_to_dict(m, u) for m, u in members],
    }


def grant_organization(
    db: Session,
    user: User,
    partner_id: str,
    organization_id: str,
    *,
    alcance: list[str] | None = None,
    notas: str | None = None,
) -> PartnerOrganizationGrant:
    if not can_manage_partners(user, db):
        assert_partner_access(db, user, partner_id, require_manage=True)
    _get_partner(db, partner_id)
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    scopes = alcance or list(_DEFAULT_ALCANCE)
    invalid = [s for s in scopes if s not in PARTNER_SCOPE_CODES]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Alcances inválidos: {invalid}")
    existing = (
        db.query(PartnerOrganizationGrant)
        .filter(
            PartnerOrganizationGrant.partner_id == partner_id,
            PartnerOrganizationGrant.organization_id == organization_id,
        )
        .first()
    )
    if existing:
        existing.estado = "ACTIVO"
        existing.alcance_json = json.dumps(scopes)
        existing.notas = notas
        existing.revoked_by = None
        existing.revoked_at = None
        existing.granted_by = user.id
        existing.updated_at = _utcnow()
        grant = existing
    else:
        grant = PartnerOrganizationGrant(
            partner_id=partner_id,
            organization_id=organization_id,
            estado="ACTIVO",
            alcance_json=json.dumps(scopes),
            notas=notas,
            granted_by=user.id,
        )
        db.add(grant)
    db.flush()
    _audit(
        db,
        partner_id=partner_id,
        organization_id=organization_id,
        action="partner.org.grant",
        actor_id=user.id,
        detail={"alcance": scopes},
    )
    return grant


def revoke_organization_grant(db: Session, user: User, partner_id: str, grant_id: str) -> PartnerOrganizationGrant:
    if not can_manage_partners(user, db):
        assert_partner_access(db, user, partner_id, require_manage=True)
    grant = (
        db.query(PartnerOrganizationGrant)
        .filter(PartnerOrganizationGrant.id == grant_id, PartnerOrganizationGrant.partner_id == partner_id)
        .first()
    )
    if not grant:
        raise HTTPException(status_code=404, detail="Concesión no encontrada")
    grant.estado = "REVOCADO"
    grant.revoked_by = user.id
    grant.revoked_at = _utcnow()
    grant.updated_at = _utcnow()
    _audit(
        db,
        partner_id=partner_id,
        organization_id=grant.organization_id,
        action="partner.org.revoke",
        actor_id=user.id,
    )
    return grant


def assign_user(
    db: Session,
    user: User,
    partner_id: str,
    target_user_id: str,
    *,
    rol: str = "OPERADOR",
) -> PartnerUserMembership:
    if rol not in PARTNER_USER_ROLES:
        raise HTTPException(status_code=422, detail=f"Rol inválido: {rol}")
    if not can_manage_partners(user, db):
        assert_partner_access(db, user, partner_id, require_manage=True)
    _get_partner(db, partner_id)
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    existing = (
        db.query(PartnerUserMembership)
        .filter(
            PartnerUserMembership.partner_id == partner_id,
            PartnerUserMembership.user_id == target_user_id,
        )
        .first()
    )
    if existing:
        existing.is_active = True
        existing.rol = rol
        existing.revoked_at = None
        existing.assigned_by = user.id
        m = existing
    else:
        m = PartnerUserMembership(
            partner_id=partner_id,
            user_id=target_user_id,
            rol=rol,
            assigned_by=user.id,
        )
        db.add(m)
    db.flush()
    _audit(
        db,
        partner_id=partner_id,
        user_id=target_user_id,
        action="partner.user.assign",
        actor_id=user.id,
        detail={"rol": rol},
    )
    return m


def revoke_user_membership(db: Session, user: User, partner_id: str, membership_id: str) -> PartnerUserMembership:
    if not can_manage_partners(user, db):
        assert_partner_access(db, user, partner_id, require_manage=True)
    m = (
        db.query(PartnerUserMembership)
        .filter(PartnerUserMembership.id == membership_id, PartnerUserMembership.partner_id == partner_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    m.is_active = False
    m.revoked_at = _utcnow()
    _audit(
        db,
        partner_id=partner_id,
        user_id=m.user_id,
        action="partner.user.revoke",
        actor_id=user.id,
    )
    return m


def update_grant_alcance(
    db: Session,
    user: User,
    partner_id: str,
    grant_id: str,
    alcance: list[str],
) -> PartnerOrganizationGrant:
    if not can_manage_partners(user, db):
        assert_partner_access(db, user, partner_id, require_manage=True)
    invalid = [s for s in alcance if s not in PARTNER_SCOPE_CODES]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Alcances inválidos: {invalid}")
    grant = (
        db.query(PartnerOrganizationGrant)
        .filter(PartnerOrganizationGrant.id == grant_id, PartnerOrganizationGrant.partner_id == partner_id)
        .first()
    )
    if not grant:
        raise HTTPException(status_code=404, detail="Concesión no encontrada")
    grant.alcance_json = json.dumps(alcance)
    grant.updated_at = _utcnow()
    _audit(
        db,
        partner_id=partner_id,
        organization_id=grant.organization_id,
        action="partner.org.update_alcance",
        actor_id=user.id,
        detail={"alcance": alcance},
    )
    return grant


def list_audit_events(db: Session, user: User, partner_id: str, limit: int = 100) -> list[dict[str, Any]]:
    assert_partner_access(db, user, partner_id)
    rows = (
        db.query(PartnerAuditEvent)
        .filter(PartnerAuditEvent.partner_id == partner_id)
        .order_by(PartnerAuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "action": e.action,
            "organization_id": e.organization_id,
            "user_id": e.user_id,
            "detail": _json_loads(e.detail_json, {}),
            "actor_id": e.actor_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ]


def get_org_context_for_partner(
    db: Session,
    user: User,
    partner_id: str,
    organization_id: str,
) -> dict[str, Any]:
    grant = assert_org_grant(db, user, partner_id, organization_id, "organizacion.read")
    org = db.query(Organization).filter(Organization.id == organization_id).one()
    scopes = _json_loads(grant.alcance_json, [])
    result: dict[str, Any] = {
        "partner_id": partner_id,
        "organization_id": organization_id,
        "organization_name": org.name,
        "organization_status": org.status,
        "alcance": scopes,
    }
    if "cc.view" in scopes:
        from app.services import control_center_service as cc_svc

        try:
            summary = cc_svc.get_executive_summary(db, user, organization_id=organization_id)
            result["centro_control"] = {
                "organization_id": summary.get("organization_id"),
                "resumen_ejecutivo": summary.get("resumen_ejecutivo"),
            }
        except Exception:
            result["centro_control"] = None
    if "trabajo.view" in scopes:
        from app.services import trabajo_service as trabajo_svc

        try:
            result["mi_trabajo"] = trabajo_svc.resumen(db, user, organization_id=organization_id)
        except Exception:
            result["mi_trabajo"] = None
    return result


def list_my_partner_organizations(db: Session, user: User, partner_id: str) -> list[dict[str, Any]]:
    if not get_membership(db, user.id, partner_id) and not can_manage_partners(user, db):
        raise HTTPException(status_code=403, detail="No es miembro de este partner")
    if get_membership(db, user.id, partner_id):
        assert_partner_access(db, user, partner_id, require_membership=True)
    else:
        _get_partner(db, partner_id)
    grants = (
        db.query(PartnerOrganizationGrant, Organization)
        .join(Organization, Organization.id == PartnerOrganizationGrant.organization_id)
        .filter(
            PartnerOrganizationGrant.partner_id == partner_id,
            PartnerOrganizationGrant.estado == "ACTIVO",
        )
        .all()
    )
    return [grant_to_dict(g, org) for g, org in grants if _grant_active(g)]
