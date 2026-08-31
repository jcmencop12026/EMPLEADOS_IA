"""API — Centro de Negocios EIAAX."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_negocio import (
    IaConsumoIn,
    NegociacionIn,
    PerspectivaUpdateIn,
    PrecioDecisionIn,
    PropuestaDesdeExpedienteIn,
    PropuestaTransicionIn,
)
from app.services import negocio_service as svc

router = APIRouter(prefix="/api/centro-negocios", tags=["Centro de Negocios"])


def _org(db: Session, user: User, organization_id: str | None) -> str:
    try:
        return svc.resolve_organization_id(db, user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/dashboard")
def dashboard(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.view", db)
    org_id = _org(db, user, organization_id)
    return svc.dashboard(db, org_id)


@router.get("/pipeline")
def pipeline(
    organization_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.view", db)
    org_id = _org(db, user, organization_id)
    return svc.list_pipeline(db, org_id, limit=limit)


@router.post("/propuestas/desde-expediente", status_code=201)
def crear_propuesta_desde_expediente(
    body: PropuestaDesdeExpedienteIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.create_proposal_from_expediente(
            db,
            user,
            org_id,
            evaluacion_id=body.evaluacion_id,
            opportunity_id=body.opportunity_id,
            titulo=body.titulo,
            modelo_comercial=body.modelo_comercial,
        )
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/propuestas/{proposal_id}")
def obtener_propuesta(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.view", db)
    org_id = _org(db, user, organization_id)
    include_internal = False
    from app.permissions import user_permissions

    perms = user_permissions(user, db)
    if "negocio.economy.private" in perms or "finops.economy.private" in perms:
        include_internal = True
    return svc.get_proposal_negocio(db, org_id, proposal_id, include_internal=include_internal)


@router.post("/propuestas/{proposal_id}/enriquecer")
def enriquecer_propuesta(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.enrich_proposal_from_sources(db, user, org_id, proposal_id)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/propuestas/{proposal_id}/transicion")
def transicion_propuesta(
    proposal_id: str,
    body: PropuestaTransicionIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    perm = "negocio.proposal.present" if body.nuevo_estado == "ENVIADA" else "negocio.manage"
    if body.nuevo_estado == "APROBADA":
        perm = "negocio.proposal.approve"
    if body.nuevo_estado == "ACEPTADA":
        perm = "negocio.contract"
    check_permission(user, perm, db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.transition_proposal(db, user, org_id, proposal_id, body.nuevo_estado, body.motivo)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/propuestas/{proposal_id}/precio")
def decidir_precio(
    proposal_id: str,
    body: PrecioDecisionIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.proposal.approve", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.apply_price_recommendation(
            db,
            user,
            org_id,
            proposal_id,
            action=body.action,
            precio_decidido=body.precio_decidido,
            justificacion=body.justificacion,
        )
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/propuestas/{proposal_id}/negociacion", status_code=201)
def registrar_negociacion(
    proposal_id: str,
    body: NegociacionIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.register_negotiation(db, user, org_id, proposal_id, body.model_dump(exclude_none=True))
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/propuestas/{proposal_id}/versiones")
def listar_versiones(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.view", db)
    org_id = _org(db, user, organization_id)
    return svc.list_versions(db, org_id, proposal_id)


@router.get("/propuestas/{proposal_id}/negociaciones")
def listar_negociaciones(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.view", db)
    org_id = _org(db, user, organization_id)
    return svc.list_negotiations(db, org_id, proposal_id)


@router.put("/propuestas/{proposal_id}/ia-consumo")
def actualizar_ia_consumo(
    proposal_id: str,
    body: IaConsumoIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.update_ia_consumo(db, org_id, proposal_id, body.model_dump(exclude_none=True))
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/propuestas/{proposal_id}/perspectivas")
def actualizar_perspectiva(
    proposal_id: str,
    body: PerspectivaUpdateIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.update_perspectives(db, org_id, proposal_id, body.perspectiva, body.contenido)
        db.commit()
        return {"perspectivas": result}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/propuestas/{proposal_id}/convertir-implementacion")
def convertir_implementacion(
    proposal_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "negocio.contract", db)
    org_id = _org(db, user, organization_id)
    try:
        result = svc.convert_to_implementacion(db, user, org_id, proposal_id)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
