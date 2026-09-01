"""API — Inteligencia de resultados EIAAX."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import resultados_service as svc

router = APIRouter(prefix="/api/resultados", tags=["Resultados"])


class IndicadorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    unidad: str = "unidad"
    definicion: str | None = None
    fuente: str = "MANUAL"
    valor_antes: float | None = None
    valor_proyectado: float | None = None
    valor_real: float | None = None
    meta: float | None = None
    expediente_id: str | None = None
    hallazgo_id: str | None = None
    opportunity_id: str | None = None
    linea_base_id: str | None = None
    proceso: str | None = None
    periodo: str | None = None
    tipo_analitica: str = "DESCRIPTIVA"
    evidencia_ref: str | None = None
    confianza: str = "MEDIA"
    visible_entidad: bool = False


class MedicionRealCreate(BaseModel):
    valor_real: float
    evidencia_ref: str | None = None
    calidad: str = "VALIDADA"


class DimensionNodoCreate(BaseModel):
    codigo: str
    etiqueta: str
    valor: float | None = None
    unidad: str | None = None
    parent_id: str | None = None
    nivel: int = 0
    metadata: dict | None = None


class InformeGenerar(BaseModel):
    expediente_id: str
    tipo: str = "IMPACTO"
    visibilidad: str = "INTERNO"


class PlanAccionCreate(BaseModel):
    expediente_id: str
    accion: str
    hallazgo_id: str | None = None
    causa: str | None = None
    indicador_id: str | None = None
    responsable_id: str | None = None
    fecha_meta: datetime | None = None


class PlanAccionUpdate(BaseModel):
    estado: str | None = None
    resultado: str | None = None
    evidencia_ref: str | None = None
    seguimiento_notas: str | None = None


class EvidenciaCreate(BaseModel):
    titulo: str
    indicador_id: str | None = None
    informe_id: str | None = None
    descripcion: str | None = None
    fuente: str = "MANUAL"
    referencia: str | None = None


@router.get("/indicadores")
def list_indicadores(
    expediente_id: str | None = None,
    periodo: str | None = None,
    proceso: str | None = None,
    tipo_analitica: str | None = None,
    q: str | None = None,
    solo_con_real: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    items = svc.list_indicadores(
        db,
        user.organization_id,
        expediente_id=expediente_id,
        periodo=periodo,
        proceso=proceso,
        tipo_analitica=tipo_analitica,
        q=q,
        solo_con_real=solo_con_real,
    )
    return {"items": items, "total": len(items)}


@router.post("/indicadores")
def create_indicador(
    body: IndicadorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    return svc.create_indicador(db, user.organization_id, **body.model_dump())


@router.post("/indicadores/sync-linea-base/{linea_base_id}")
def sync_linea_base(
    linea_base_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    try:
        return svc.sync_indicador_from_linea_base(db, linea_base_id, user.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/indicadores/{indicador_id}/medicion-real")
def register_medicion_real(
    indicador_id: str,
    body: MedicionRealCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.validate")),
) -> dict[str, Any]:
    try:
        return svc.register_medicion_real(
            db, indicador_id, user.organization_id, **body.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/indicadores/{indicador_id}/drill-down")
def drill_down(
    indicador_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    try:
        return svc.get_drill_down(db, indicador_id, user.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/indicadores/{indicador_id}/dimensiones")
def add_dimension(
    indicador_id: str,
    body: DimensionNodoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    return svc.add_dimension_nodo(db, user.organization_id, indicador_id, **body.model_dump())


@router.get("/antes-proyectado-real")
def antes_proyectado_real(
    expediente_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    return svc.build_antes_proyectado_real(db, user.organization_id, expediente_id=expediente_id)


@router.get("/informes")
def list_informes(
    expediente_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    items = svc.list_informes(db, user.organization_id, expediente_id=expediente_id)
    return {"items": items, "total": len(items)}


@router.get("/informes/{informe_id}")
def get_informe(
    informe_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    try:
        return svc.get_informe(db, informe_id, user.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/informes/generar")
def generar_informe(
    body: InformeGenerar,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.informe.generate")),
) -> dict[str, Any]:
    try:
        return svc.generate_informe_impacto(
            db,
            user.organization_id,
            user.id,
            expediente_id=body.expediente_id,
            tipo=body.tipo,
            visibilidad=body.visibilidad,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/plan-acciones")
def list_planes(
    expediente_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    items = svc.list_planes(db, user.organization_id, expediente_id=expediente_id)
    return {"items": items, "total": len(items)}


@router.post("/plan-acciones")
def create_plan(
    body: PlanAccionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    return svc.create_plan_accion(db, user.organization_id, **body.model_dump())


@router.patch("/plan-acciones/{plan_id}")
def update_plan(
    plan_id: str,
    body: PlanAccionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    try:
        return svc.update_plan_accion(db, plan_id, user.organization_id, **body.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/evidencias")
def add_evidencia(
    body: EvidenciaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.manage")),
) -> dict[str, Any]:
    return svc.add_evidencia(db, user.organization_id, user.id, **body.model_dump())


@router.get("/expediente/{expediente_id}/trazabilidad")
def trazabilidad(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("resultados.view")),
) -> dict[str, Any]:
    try:
        return svc.get_trazabilidad_resultados(db, user.organization_id, expediente_id=expediente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/informes/{informe_id}/entregar")
def entregar_informe_resultados(
    informe_id: str,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("communications.send")),
) -> dict[str, Any]:
    from app.services import communications_service as comm_svc

    try:
        return comm_svc.deliver_informe_impacto(
            db,
            user.organization_id,
            user,
            informe_id=informe_id,
            channel_id=body["channel_id"],
            destinatario_tipo=body.get("destinatario_tipo", "USUARIO"),
            destinatario_id=body.get("destinatario_id"),
            destinatario_externo=body.get("destinatario_externo"),
            visibilidad_entrega=body.get("visibilidad_entrega", "VISIBLE_ENTIDAD"),
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
