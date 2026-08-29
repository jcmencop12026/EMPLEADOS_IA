"""API — Optimización y recomendaciones (Bloque 1290)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import optimization_service as svc

router = APIRouter(prefix="/api/optimizacion", tags=["Optimización"])


class ConfigUpdate(BaseModel):
    objetivo_default: str | None = None
    pesos: dict[str, float] | None = None


class RestriccionesInput(BaseModel):
    presupuesto_maximo: float | None = None
    tiempo_maximo_dias: float | None = None
    capacidad_operativa: int | None = None
    max_iniciativas: int | None = None
    riesgo_maximo: float | None = None
    obligatorias: list[str] = Field(default_factory=list)
    excluidas: list[str] = Field(default_factory=list)
    requiere: list[dict[str, str]] = Field(default_factory=list)
    incompatibles: list[list[str]] = Field(default_factory=list)
    orden_previo: list[dict[str, str]] = Field(default_factory=list)


class RecomendacionCreate(BaseModel):
    objetivo: str = "RESULTADO_EQUILIBRADO"
    restricciones: RestriccionesInput | None = None
    opportunity_ids: list[str] | None = None
    pesos: dict[str, float] | None = None


class SimulacionInput(RecomendacionCreate):
    pass


class CompararEscenariosInput(BaseModel):
    restricciones_base: RestriccionesInput | None = None
    escenarios: list[dict[str, Any]]


class AprobarInput(BaseModel):
    justificacion: str = Field(..., min_length=3)


class RechazarInput(BaseModel):
    motivo: str = Field(..., min_length=3)


class RecalcularInput(BaseModel):
    objetivo: str | None = None
    restricciones: RestriccionesInput | None = None


def _restricciones_dict(r: RestriccionesInput | None) -> dict | None:
    if not r:
        return None
    return r.model_dump(exclude_none=True)


@router.get("/configuracion")
def get_configuracion(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.view")),
):
    cfg = svc.obtener_configuracion(db, user.organization_id)
    return {
        "objetivo_default": cfg.objetivo_default,
        "pesos": svc._json_load(cfg.pesos_json),
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


@router.put("/configuracion")
def put_configuracion(
    body: ConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.configure")),
):
    cfg = svc.actualizar_configuracion(
        db, user, objetivo_default=body.objetivo_default, pesos=body.pesos
    )
    db.commit()
    return {"objetivo_default": cfg.objetivo_default, "pesos": svc._json_load(cfg.pesos_json)}


@router.post("/simular")
def simular(
    body: SimulacionInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.simulate")),
):
    resultado = svc.ejecutar_optimizacion(
        db,
        user.organization_id,
        objetivo=body.objetivo,
        restricciones_data=_restricciones_dict(body.restricciones),
        pesos_custom=body.pesos,
        opportunity_ids=body.opportunity_ids,
    )
    return {
        "factible": resultado["factible"],
        "conflictos": resultado["conflictos"],
        "seleccion": resultado["seleccion"],
        "totales": resultado["totales"],
        "roi": resultado["roi"],
        "explicacion": resultado["explicacion"],
        "oportunidades": [
            {
                "opportunity_id": e.opportunity_id,
                "codigo": e.codigo,
                "titulo": e.titulo,
                "puntuacion": e.puntuacion,
                "seleccionado": e.opportunity_id in resultado["seleccion"],
                "factores": e.factores,
                "aprendizaje": e.aprendizaje,
            }
            for e in resultado["evaluadas"]
        ],
    }


@router.post("/recomendaciones", status_code=201)
def crear_recomendacion(
    body: RecomendacionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.create")),
):
    rec = svc.crear_recomendacion(
        db,
        user,
        objetivo=body.objetivo,
        restricciones=_restricciones_dict(body.restricciones),
        opportunity_ids=body.opportunity_ids,
        pesos=body.pesos,
    )
    db.commit()
    items = svc.listar_items(db, user.organization_id, rec.id)
    return svc.serializar_recomendacion(rec, items)


@router.get("/recomendaciones")
def listar_recomendaciones(
    incluir_simulaciones: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.view")),
):
    recs = svc.listar_recomendaciones(db, user.organization_id, incluir_simulaciones=incluir_simulaciones)
    return [svc.serializar_recomendacion(r) for r in recs]


@router.get("/recomendaciones/{rec_id}")
def detalle_recomendacion(
    rec_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.view")),
):
    rec = svc.obtener_recomendacion(db, user.organization_id, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    items = svc.listar_items(db, user.organization_id, rec_id)
    return svc.serializar_recomendacion(rec, items)


@router.post("/recomendaciones/{rec_id}/recalcular", status_code=201)
def recalcular(
    rec_id: str,
    body: RecalcularInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.create")),
):
    try:
        nueva = svc.recalcular_recomendacion(
            db,
            user,
            rec_id,
            restricciones=_restricciones_dict(body.restricciones),
            objetivo=body.objetivo,
        )
        db.commit()
        items = svc.listar_items(db, user.organization_id, nueva.id)
        return svc.serializar_recomendacion(nueva, items)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recomendaciones/{rec_id}/aprobar")
def aprobar(
    rec_id: str,
    body: AprobarInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.approve")),
):
    try:
        rec = svc.aprobar_recomendacion(db, user, rec_id, body.justificacion)
        db.commit()
        return svc.serializar_recomendacion(rec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recomendaciones/{rec_id}/rechazar")
def rechazar(
    rec_id: str,
    body: RechazarInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.approve")),
):
    try:
        rec = svc.rechazar_recomendacion(db, user, rec_id, body.motivo)
        db.commit()
        return svc.serializar_recomendacion(rec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recomendaciones/{rec_id}/revisar")
def revisar(
    rec_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.create")),
):
    try:
        rec = svc.marcar_revisada(db, user, rec_id)
        db.commit()
        return svc.serializar_recomendacion(rec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/comparar", status_code=201)
def comparar_escenarios(
    body: CompararEscenariosInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.simulate")),
):
    recs = svc.comparar_escenarios(
        db,
        user,
        escenarios=body.escenarios,
        restricciones_base=_restricciones_dict(body.restricciones_base),
    )
    db.commit()
    grupo = recs[0].grupo_comparacion_id if recs else None
    return {
        "grupo_comparacion_id": grupo,
        "escenarios": [
            {
                **svc.serializar_recomendacion(r),
                "items": [svc.serializar_item(i) for i in svc.listar_items(db, user.organization_id, r.id)],
            }
            for r in recs
        ],
    }


@router.get("/historial")
def historial(
    recomendacion_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("optimizacion.view")),
):
    eventos = svc.listar_auditoria(db, user.organization_id, recomendacion_id)
    return [
        {
            "id": e.id,
            "accion": e.accion,
            "recomendacion_id": e.recomendacion_id,
            "actor_id": e.actor_id,
            "detalle": svc._json_load(e.detalle_json),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in eventos
    ]
