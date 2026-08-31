"""Router — Continuidad comercial y operacional EIAAX (1720)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission, user_permissions
from app.schemas_continuidad_comercial import (
    CambioAlcanceAvanzar,
    CambioAlcanceCreate,
    CierreContratoConfirmar,
    CierreContratoCreate,
)
from app.services import continuidad_comercial_service as svc
from app.services import control_center_service as cc_svc

router = APIRouter(prefix="/api/continuidad-comercial", tags=["continuidad-comercial"])


def _org(db: Session, user: User, organization_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, organization_id)


@router.get("/propuestas/{proposal_id}/vista")
def vista_por_propuesta(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.view", db)
    org_id = _org(db, user, organization_id)
    perms = user_permissions(user, db)
    include_private = "negocio.economy.private" in perms or "finops.economy.private" in perms
    return svc.vista_continuidad(db, org_id, proposal_id=proposal_id, include_private=include_private)


@router.get("/contratos/{contract_id}/vista")
def vista_por_contrato(
    contract_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.view", db)
    org_id = _org(db, user, organization_id)
    perms = user_permissions(user, db)
    include_private = "negocio.economy.private" in perms or "finops.economy.private" in perms
    return svc.vista_continuidad(db, org_id, contract_id=contract_id, include_private=include_private)


@router.get("/proyectos/{proyecto_id}/vista")
def vista_por_proyecto(
    proyecto_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.view", db)
    org_id = _org(db, user, organization_id)
    perms = user_permissions(user, db)
    include_private = "negocio.economy.private" in perms or "finops.economy.private" in perms
    return svc.vista_continuidad(db, org_id, proyecto_id=proyecto_id, include_private=include_private)


@router.post("/cambios-alcance")
def crear_cambio(
    body: CambioAlcanceCreate,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.manage", db)
    org_id = _org(db, user, organization_id)
    row = svc.create_cambio_alcance(db, user, org_id, body.model_dump())
    db.commit()
    return svc.cambio_to_dict(row)


@router.post("/cambios-alcance/{cambio_id}/avanzar")
def avanzar_cambio(
    cambio_id: str,
    body: CambioAlcanceAvanzar,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.manage", db)
    org_id = _org(db, user, organization_id)
    row = svc.avanzar_cambio_alcance(db, user, org_id, cambio_id, accion=body.accion, payload=body.model_dump())
    db.commit()
    return svc.cambio_to_dict(row)


@router.get("/propuestas/{proposal_id}/cambios-alcance")
def listar_cambios(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.view", db)
    org_id = _org(db, user, organization_id)
    from app.continuidad_comercial_models import ContinuidadCambioAlcance

    rows = (
        db.query(ContinuidadCambioAlcance)
        .filter(ContinuidadCambioAlcance.proposal_id == proposal_id, ContinuidadCambioAlcance.organization_id == org_id)
        .order_by(ContinuidadCambioAlcance.created_at.desc())
        .all()
    )
    return [svc.cambio_to_dict(r) for r in rows]


@router.post("/contratos/{contract_id}/cierre")
def iniciar_cierre(
    contract_id: str,
    body: CierreContratoCreate,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.close", db)
    org_id = _org(db, user, organization_id)
    row = svc.iniciar_cierre_contrato(db, user, org_id, contract_id, body.model_dump())
    db.commit()
    return svc.closure_to_dict(row)


@router.post("/cierres/{closure_id}/confirmar")
def confirmar_cierre(
    closure_id: str,
    body: CierreContratoConfirmar,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "continuidad_comercial.close", db)
    org_id = _org(db, user, organization_id)
    row = svc.confirmar_cierre_contrato(db, user, org_id, closure_id, confirmacion=body.confirmacion)
    db.commit()
    return svc.closure_to_dict(row)
