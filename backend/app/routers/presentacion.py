"""API — Presentación ejecutiva real EIAAX (V1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.presentacion_models import ESTADOS_PUBLICACION
from app.services import informes_comerciales_adapter as inf_adapter
from app.services import presentacion_publicacion_adapter as pub_adapter
from app.services import presentacion_service as pres_svc
from app.services.presentacion_publicacion_adapter import PublicacionDenegadaError

router = APIRouter(prefix="/api/presentacion", tags=["presentacion"])


class PublicacionUpdate(BaseModel):
    estado: str = Field(..., min_length=5, max_length=40)
    notas: str | None = None


class InformeComercialCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=160)
    audiencia: str = "GERENCIA"
    periodicidad: str = "MENSUAL"
    destinatarios: list[str] = Field(default_factory=list)
    resumen: str | None = None
    expediente_id: str | None = None
    enlace_seguro: bool = True
    activo: bool = True


class InformeComercialUpdate(BaseModel):
    activo: bool | None = None
    destinatarios: list[str] | None = None
    resumen: str | None = None


@router.get("/informes-comerciales/plantillas")
def informes_plantillas(user: User = Depends(get_current_user)):
    return {"plantillas": inf_adapter.plantillas_periodicas()}


@router.get("/informes-comerciales/config")
def list_informes_config(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("communications.view")),
):
    return {"items": inf_adapter.list_configs(db, user.organization_id)}


@router.post("/informes-comerciales/config")
def create_informe_config(
    body: InformeComercialCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("communications.rule.manage")),
):
    try:
        result = inf_adapter.create_config(
            db,
            user.organization_id,
            user.id,
            nombre=body.nombre,
            audiencia=body.audiencia,
            periodicidad=body.periodicidad,
            destinatarios=body.destinatarios,
            resumen=body.resumen,
            expediente_id=body.expediente_id,
            enlace_seguro=body.enlace_seguro,
            activo=body.activo,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/informes-comerciales/config/{config_id}")
def patch_informe_config(
    config_id: str,
    body: InformeComercialUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("communications.rule.manage")),
):
    try:
        result = inf_adapter.update_config(
            db,
            user.organization_id,
            config_id,
            activo=body.activo,
            destinatarios=body.destinatarios,
            resumen=body.resumen,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{expediente_id}")
def get_presentacion_real(
    expediente_id: str,
    audiencia: str = Query("GERENCIA"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return pres_svc.build_presentacion_real(
            db, user.organization_id, expediente_id, user, audiencia=audiencia
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PublicacionDenegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{expediente_id}/pdf")
def get_presentacion_pdf(
    expediente_id: str,
    audiencia: str = Query("GERENCIA"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        pdf_bytes, filename = pres_svc.build_presentacion_pdf(
            db,
            user.organization_id,
            expediente_id,
            user,
            audiencia=audiencia,
            es_demo=False,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PublicacionDenegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{expediente_id}/publicacion")
def get_publicacion_estado(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    row = pub_adapter.get_publicacion(db, user.organization_id, expediente_id)
    if not row:
        return {
            "expediente_id": expediente_id,
            "estado": "PRIVADO",
            "estados_permitidos": list(ESTADOS_PUBLICACION),
            "adapter": "presentacion_publicacion_v1",
        }
    return pub_adapter.publicacion_to_dict(row)


@router.put("/{expediente_id}/publicacion")
def update_publicacion_estado(
    expediente_id: str,
    body: PublicacionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.visibility")),
):
    try:
        result = pub_adapter.set_estado_publicacion(
            db,
            user.organization_id,
            expediente_id,
            user.id,
            estado=body.estado,
            notas=body.notas,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
