"""API — Aprendizaje, retroalimentación y repriorización (Bloque 1260)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.learning_models import CicloAprendizaje, PatronAprendizaje, Recalibracion, Retroalimentacion
from app.models import User
from app.permissions import require_permission
from app.services import learning_service as svc

router = APIRouter(prefix="/api/aprendizaje", tags=["Aprendizaje"])


class CicloCreate(BaseModel):
    opportunity_id: str
    impacto_real: float | None = None
    valor_real: float | None = None
    costo_real: float | None = None
    tiempo_real_dias: float | None = None


class CicloEvaluar(BaseModel):
    impacto_real: float | None = None
    valor_real: float | None = None
    costo_real: float | None = None
    tiempo_real_dias: float | None = None
    tipo_explicacion: str = Field(default="PROBABLE", pattern="^(CONFIRMADA|PROBABLE|HIPOTESIS)$")
    notas: str | None = None


class RechazoRecalibracion(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=2000)


def _handle_value_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/ciclos")
def listar_ciclos(
    opportunity_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    ciclos = svc.listar_ciclos(db, user.organization_id, opportunity_id=opportunity_id)
    return [svc.serializar_ciclo(c) for c in ciclos]


@router.get("/ciclos/{ciclo_id}")
def obtener_ciclo(
    ciclo_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    ciclo = svc.obtener_ciclo(db, user.organization_id, ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="Ciclo de aprendizaje no encontrado")
    retro = (
        db.query(Retroalimentacion)
        .filter(Retroalimentacion.ciclo_id == ciclo_id, Retroalimentacion.organization_id == user.organization_id)
        .order_by(Retroalimentacion.created_at.desc())
        .all()
    )
    recs = svc.listar_recalibraciones(db, user.organization_id, ciclo_id=ciclo_id)
    return {
        **svc.serializar_ciclo(ciclo),
        "retroalimentaciones": [_serializar_retro(r) for r in retro],
        "recalibraciones": [_serializar_recal(r) for r in recs],
    }


@router.post("/ciclos", status_code=201)
def crear_ciclo(
    body: CicloCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.evaluate")),
):
    try:
        ciclo = svc.crear_ciclo_aprendizaje(
            db,
            user,
            opportunity_id=body.opportunity_id,
            impacto_real=body.impacto_real,
            valor_real=body.valor_real,
            costo_real=body.costo_real,
            tiempo_real_dias=body.tiempo_real_dias,
        )
        db.commit()
        return svc.serializar_ciclo(ciclo)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.post("/ciclos/{ciclo_id}/evaluar")
def evaluar_ciclo(
    ciclo_id: str,
    body: CicloEvaluar,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.evaluate")),
):
    try:
        result = svc.evaluar_ciclo(
            db,
            user,
            ciclo_id,
            impacto_real=body.impacto_real,
            valor_real=body.valor_real,
            costo_real=body.costo_real,
            tiempo_real_dias=body.tiempo_real_dias,
            tipo_explicacion=body.tipo_explicacion,
            notas=body.notas,
        )
        db.commit()
        return {
            "ciclo": svc.serializar_ciclo(result["ciclo"]),
            "retroalimentacion": _serializar_retro(result["retroalimentacion"]),
            "patrones": [_serializar_patron(p) for p in result["patrones"]],
            "recalibraciones": [_serializar_recal(r) for r in result["recalibraciones"]],
            "desviaciones": result["desviaciones"],
            "explicacion_prioridad": result["explicacion_prioridad"],
        }
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.get("/desviaciones")
def consultar_desviaciones(
    opportunity_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    ciclos = svc.listar_ciclos(db, user.organization_id, opportunity_id=opportunity_id)
    return [
        {
            "ciclo_id": c.id,
            "opportunity_id": c.opportunity_id,
            "estado": c.estado,
            "desviaciones": svc._json_load(c.desviaciones_json),
            "calidad_recomendacion": c.calidad_recomendacion,
        }
        for c in ciclos
        if c.desviaciones_json
    ]


@router.get("/recalibraciones")
def listar_recalibraciones(
    ciclo_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    recs = svc.listar_recalibraciones(db, user.organization_id, ciclo_id=ciclo_id)
    return [_serializar_recal(r) for r in recs]


@router.post("/recalibraciones/{recalibracion_id}/aprobar")
def aprobar_recalibracion(
    recalibracion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.approve")),
):
    try:
        rec = svc.aprobar_recalibracion(db, user, recalibracion_id)
        db.commit()
        return _serializar_recal(rec)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.post("/recalibraciones/{recalibracion_id}/rechazar")
def rechazar_recalibracion(
    recalibracion_id: str,
    body: RechazoRecalibracion,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.approve")),
):
    try:
        rec = svc.rechazar_recalibracion(db, user, recalibracion_id, body.motivo)
        db.commit()
        return _serializar_recal(rec)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.post("/recalibraciones/{recalibracion_id}/aplicar")
def aplicar_recalibracion(
    recalibracion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.recalibrate")),
):
    try:
        rec = svc.aplicar_recalibracion(db, user, recalibracion_id)
        db.commit()
        return _serializar_recal(rec)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc


@router.get("/patrones")
def listar_patrones(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    return [_serializar_patron(p) for p in svc.listar_patrones(db, user.organization_id)]


@router.get("/historial")
def historial_aprendizaje(
    ciclo_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("aprendizaje.view")),
):
    eventos = svc.listar_auditoria(db, user.organization_id, ciclo_id=ciclo_id)
    return [
        {
            "id": e.id,
            "accion": e.accion,
            "ciclo_id": e.ciclo_id,
            "recalibracion_id": e.recalibracion_id,
            "opportunity_id": e.opportunity_id,
            "actor_id": e.actor_id,
            "detalle": svc._json_load(e.detalle_json),
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in eventos
    ]


def _serializar_retro(r: Retroalimentacion) -> dict[str, Any]:
    return {
        "id": r.id,
        "ciclo_id": r.ciclo_id,
        "opportunity_id": r.opportunity_id,
        "tipo_explicacion": r.tipo_explicacion,
        "calidad_recomendacion": r.calidad_recomendacion,
        "resumen": r.resumen,
        "detalle": r.detalle,
        "lecciones": svc._json_load(r.lecciones_json),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _serializar_recal(r: Recalibracion) -> dict[str, Any]:
    return {
        "id": r.id,
        "ciclo_id": r.ciclo_id,
        "opportunity_id": r.opportunity_id,
        "estado": r.estado,
        "campo": r.campo,
        "valor_anterior": r.valor_anterior,
        "valor_nuevo": r.valor_nuevo,
        "justificacion": r.justificacion,
        "factores": svc._json_load(r.factores_json),
        "sugerida_at": r.sugerida_at.isoformat() if r.sugerida_at else None,
        "decidida_at": r.decidida_at.isoformat() if r.decidida_at else None,
        "aplicada_at": r.aplicada_at.isoformat() if r.aplicada_at else None,
        "motivo_rechazo": r.motivo_rechazo,
    }


def _serializar_patron(p: PatronAprendizaje) -> dict[str, Any]:
    return {
        "id": p.id,
        "tipo_patron": p.tipo_patron,
        "clave_patron": p.clave_patron,
        "dominio": p.dominio,
        "tipo_oportunidad": p.tipo_oportunidad,
        "ocurrencias": p.ocurrencias,
        "resumen": p.resumen,
        "detalle": svc._json_load(p.detalle_json),
        "ultima_deteccion_at": p.ultima_deteccion_at.isoformat() if p.ultima_deteccion_at else None,
    }
