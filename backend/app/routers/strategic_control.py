"""API — Centro de Control Estratégico/Empresa (V1)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import strategic_control_service as svc
from app.services import strategic_write_service as write_svc

router = APIRouter(prefix="/api/centro-estrategico", tags=["Centro Estratégico"])


class RegistrarNecesidadBody(BaseModel):
    titulo: str = Field(..., min_length=1)
    necesidad: str = Field(..., min_length=1)
    objetivo: str | None = None
    entidad_nombre: str | None = None


class PrepararPublicacionBody(BaseModel):
    hallazgo_id: str
    visible_entidad: bool
    motivo: str | None = None


class ActualizarSupuestoBody(BaseModel):
    item_id: str
    respuesta: str
    motivo: str | None = None


class RegistrarDecisionBody(BaseModel):
    opportunity_id: str
    aprobado: bool = True
    motivo: str | None = None


@router.get("/cockpit")
def get_cockpit(
    lectura: str = Query("resumen", description="resumen | gerencia | operacion | sistemas | financiero"),
    modo_comite: bool = Query(False, description="Modo comité — navegación entre lecturas"),
    organization_id: str | None = Query(None, description="Solo plataforma/SuperAdmin"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
):
    try:
        org_id = svc.resolve_organization_id(db, user, organization_id)
        return svc.get_cockpit(db, user, org_id, lectura=lectura, modo_comite=modo_comite)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/lecturas")
def get_lecturas_config(
    user: User = Depends(require_permission("strategic_control.view")),
):
    return {"lecturas": svc.LECTURAS, "semantica": svc.SEMANTICA_VALOR}


@router.post("/acciones/registrar-necesidad")
def accion_registrar_necesidad(
    body: RegistrarNecesidadBody,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
) -> dict[str, Any]:
    org_id = svc.resolve_organization_id(db, user, organization_id)
    result = write_svc.registrar_necesidad(
        db, user, org_id,
        titulo=body.titulo,
        necesidad=body.necesidad,
        objetivo=body.objetivo,
        entidad_nombre=body.entidad_nombre,
    )
    db.commit()
    return result


@router.post("/acciones/preparar-publicacion")
def accion_preparar_publicacion(
    body: PrepararPublicacionBody,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
) -> dict[str, Any]:
    org_id = svc.resolve_organization_id(db, user, organization_id)
    result = write_svc.preparar_publicacion(
        db, user, org_id,
        hallazgo_id=body.hallazgo_id,
        visible_entidad=body.visible_entidad,
        motivo=body.motivo,
    )
    db.commit()
    return result


@router.post("/acciones/actualizar-supuesto")
def accion_actualizar_supuesto(
    body: ActualizarSupuestoBody,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
) -> dict[str, Any]:
    org_id = svc.resolve_organization_id(db, user, organization_id)
    result = write_svc.actualizar_supuesto(
        db, user, org_id,
        item_id=body.item_id,
        respuesta=body.respuesta,
        motivo=body.motivo,
    )
    db.commit()
    return result


@router.post("/acciones/priorizar-oportunidades")
def accion_priorizar_oportunidades(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
) -> dict[str, Any]:
    org_id = svc.resolve_organization_id(db, user, organization_id)
    result = write_svc.priorizar_oportunidades(db, user, org_id)
    db.commit()
    return result


@router.post("/acciones/registrar-decision")
def accion_registrar_decision(
    body: RegistrarDecisionBody,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
) -> dict[str, Any]:
    org_id = svc.resolve_organization_id(db, user, organization_id)
    result = write_svc.registrar_decision_oportunidad(
        db, user, org_id,
        opportunity_id=body.opportunity_id,
        aprobado=body.aprobado,
        motivo=body.motivo,
    )
    db.commit()
    return result
