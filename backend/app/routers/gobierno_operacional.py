"""API de gobierno operacional EIAAX."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_gobierno_operacional import (
    AccionPolicyIn,
    AccionPolicyOut,
    AccionSolicitudDecideIn,
    AccionSolicitudIn,
    AccionSolicitudOut,
    ConfianzaCentroOut,
    EvaluarAccionIn,
    EvaluarAccionOut,
    GobiernoEventoOut,
    IaPolicyCheckIn,
    IaPolicyCheckOut,
    IaPolicyIn,
    IaPolicyOut,
    VisibilidadIn,
    VisibilidadLogOut,
)
from app.services import gobierno_operacional_service as svc

router = APIRouter(prefix="/api/gobierno-operacional", tags=["gobierno-operacional"])


@router.get("/confianza", response_model=ConfianzaCentroOut)
def centro_confianza(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "gobierno.confianza.view", db)
    return svc.get_centro_confianza(db, user.organization_id)


@router.post("/acciones/evaluar", response_model=EvaluarAccionOut)
def evaluar_accion(
    body: EvaluarAccionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.view", db)
    return svc.evaluar_accion(
        db,
        user.organization_id,
        tipo_accion=body.tipo_accion,
        recurso_tipo=body.recurso_tipo,
        criticidad=body.criticidad,
        capacidad_externa=body.capacidad_externa,
        empleado_ia_id=body.empleado_ia_id,
    )


@router.get("/politicas", response_model=list[AccionPolicyOut])
def list_policies(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "gobierno.view", db)
    return [svc.policy_to_dict(p) for p in svc.list_policies(db, user.organization_id)]


@router.post("/politicas", response_model=AccionPolicyOut, status_code=201)
def create_policy(
    body: AccionPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.manage", db)
    row = svc.create_policy(db, user.organization_id, body.model_dump())
    db.commit()
    return svc.policy_to_dict(row)


@router.get("/solicitudes", response_model=list[AccionSolicitudOut])
def list_solicitudes(
    estado: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.view", db)
    return svc.list_solicitudes(db, user.organization_id, estado=estado, limit=limit)


@router.post("/solicitudes", response_model=AccionSolicitudOut, status_code=201)
def crear_solicitud(
    body: AccionSolicitudIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.execute", db)
    result = svc.crear_solicitud(db, user.organization_id, user.id, body.model_dump())
    db.commit()
    return result


@router.post("/solicitudes/{solicitud_id}/decidir", response_model=AccionSolicitudOut)
def decidir_solicitud(
    solicitud_id: str,
    body: AccionSolicitudDecideIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.approve", db)
    result = svc.decidir_solicitud(
        db,
        user.organization_id,
        solicitud_id,
        user.id,
        decision=body.decision,
        motivo=body.motivo,
    )
    db.commit()
    return result


@router.post("/visibilidad", response_model=VisibilidadLogOut, status_code=201)
def set_visibilidad(
    body: VisibilidadIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.visibility", db)
    log = svc.set_visibilidad_general(
        db,
        user.organization_id,
        user.id,
        dominio=body.dominio,
        contexto_id=body.contexto_id,
        objeto_tipo=body.objeto_tipo,
        objeto_id=body.objeto_id,
        visible=body.visible,
        correlation_id=body.correlation_id,
    )
    db.commit()
    return {
        "id": log.id,
        "dominio": log.dominio,
        "contexto_id": log.contexto_id,
        "objeto_tipo": log.objeto_tipo,
        "objeto_id": log.objeto_id,
        "visible": log.visible,
        "changed_by": log.changed_by,
        "correlation_id": log.correlation_id,
        "created_at": log.created_at,
    }


@router.get("/visibilidad", response_model=list[VisibilidadLogOut])
def list_visibilidad(
    dominio: str | None = None,
    contexto_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.view", db)
    return svc.list_visibilidad(db, user.organization_id, dominio=dominio, contexto_id=contexto_id, limit=limit)


@router.get("/ia/politicas", response_model=list[IaPolicyOut])
def list_ia_policies(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "gobierno.ia_policy", db)
    return svc.list_ia_policies(db, user.organization_id)


@router.post("/ia/politicas", response_model=IaPolicyOut, status_code=201)
def create_ia_policy(
    body: IaPolicyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.ia_policy", db)
    result = svc.create_ia_policy(db, user.organization_id, body.model_dump())
    db.commit()
    return result


@router.post("/ia/verificar", response_model=IaPolicyCheckOut)
def check_ia_policy(
    body: IaPolicyCheckIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.view", db)
    return svc.check_ia_policy(
        db,
        user.organization_id,
        proveedor=body.proveedor,
        modelo=body.modelo,
        tipo_accion=body.tipo_accion,
        herramienta=body.herramienta,
    )


@router.get("/eventos", response_model=list[GobiernoEventoOut])
def list_eventos(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "gobierno.audit", db)
    return svc.list_eventos(db, user.organization_id, limit=limit)
