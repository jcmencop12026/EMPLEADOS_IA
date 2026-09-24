"""API — Arquitecto de Transformación Empresarial."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import evaluacion_service as eval_svc
from app.services import transformacion_service as svc
from app.services import factory_bridge_service as bridge_svc

router = APIRouter(prefix="/api/transformacion", tags=["Transformación"])


class RegistrarNecesidadBody(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=300)
    necesidad: str = Field(..., min_length=5)
    objetivo: str | None = None
    area_proceso: str | None = Field(None, max_length=120)
    entidad_nombre: str | None = Field(None, max_length=200)
    nivel: str = "PRELIMINAR"


@router.get("/dossier")
def get_dossier(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.view")),
):
    return svc.get_dossier_completo(db, user.organization_id)


@router.post("/necesidad", status_code=201)
def registrar_necesidad(
    body: RegistrarNecesidadBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.manage")),
):
    result = svc.registrar_necesidad(
        db,
        user.organization_id,
        user.id,
        titulo=body.titulo,
        necesidad=body.necesidad,
        objetivo=body.objetivo,
        area_proceso=body.area_proceso,
        entidad_nombre=body.entidad_nombre,
        nivel=body.nivel,
    )
    db.commit()
    return result


@router.get("/expedientes/{expediente_id}/suficiencia")
def suficiencia(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.view")),
):
    return svc.evaluar_suficiencia(db, user.organization_id, expediente_id)


@router.post("/expedientes/{expediente_id}/diagnosticar")
def diagnosticar(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.execute")),
):
    result = svc.ejecutar_diagnostico_transformacion(
        db, user.organization_id, expediente_id, user_id=user.id,
    )
    db.commit()
    return result


@router.get("/recorrido")
def recorrido(
    expediente_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.view")),
):
    return svc.get_recorrido_estado(db, user.organization_id, expediente_id)


@router.post("/expedientes/{expediente_id}/prefill")
def prefill_dossier(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.manage")),
):
    dossier = svc.get_or_create_dossier(db, user.organization_id)
    exp = eval_svc._get_expediente(db, expediente_id, user.organization_id)  # noqa: SLF001
    filled = svc.prefill_from_dossier(db, dossier, exp)
    db.commit()
    return {"items_rellenados": filled, "dossier": svc.get_dossier_completo(db, user.organization_id)}


@router.get("/requerimientos-empleado-ia")
def list_requerimientos_empleado_ia(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("transformacion.view")),
):
    return {"items": bridge_svc.list_requerimientos_pendientes(db, user.organization_id)}
