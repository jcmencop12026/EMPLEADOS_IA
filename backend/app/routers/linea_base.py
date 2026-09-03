"""API — Línea base, medición posterior e impacto (Bloque 1200)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.baseline_models import LineaBase, LineaBaseImpacto, LineaBaseMedicion
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import baseline_service as svc

router = APIRouter(prefix="/api/lineas-base", tags=["Línea base"])


class LineaBaseCreate(BaseModel):
    indicador: str = Field(..., max_length=120)
    valor_base: float
    fecha_inicio_base: datetime
    fecha_fin_base: datetime
    unidad: str = "unidad"
    descripcion: str | None = None
    fuente: str = "MANUAL"
    metodo_calculo: str | None = None
    evidencia: dict[str, Any] | None = None
    direccion_indicador: str = "MAYOR_ES_MEJOR"
    impacto_esperado: float | None = None
    estado: str = "BORRADOR"
    proceso: str | None = None
    opportunity_id: str | None = None
    work_plan_id: str | None = None
    employee_id: str | None = None
    accion_referencia: str | None = None
    valor_economico_tipo: str | None = None


class LineaBaseUpdate(BaseModel):
    indicador: str | None = None
    valor_base: float | None = None
    fecha_inicio_base: datetime | None = None
    fecha_fin_base: datetime | None = None
    unidad: str | None = None
    descripcion: str | None = None
    fuente: str | None = None
    metodo_calculo: str | None = None
    evidencia: dict[str, Any] | None = None
    direccion_indicador: str | None = None
    impacto_esperado: float | None = None
    estado: str | None = None
    proceso: str | None = None
    opportunity_id: str | None = None
    work_plan_id: str | None = None
    employee_id: str | None = None
    accion_referencia: str | None = None
    valor_economico_tipo: str | None = None


class MedicionCreate(BaseModel):
    valor_posterior: float
    periodo_inicio: datetime
    periodo_fin: datetime
    fuente: str = "MANUAL"
    evidencia: dict[str, Any] | None = None


class AtribucionUpdate(BaseModel):
    atribucion_nivel: str
    atribucion_porcentaje: float | None = None
    justificacion: str | None = None
    evidencia: dict[str, Any] | None = None


def _get_linea_base(db: Session, linea_base_id: str, user: User) -> LineaBase:
    lb = (
        db.query(LineaBase)
        .filter(LineaBase.id == linea_base_id, LineaBase.organization_id == user.organization_id)
        .first()
    )
    if not lb:
        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    return lb


def _get_medicion(db: Session, linea_base_id: str, medicion_id: str, user: User) -> LineaBaseMedicion:
    med = (
        db.query(LineaBaseMedicion)
        .filter(
            LineaBaseMedicion.id == medicion_id,
            LineaBaseMedicion.linea_base_id == linea_base_id,
            LineaBaseMedicion.organization_id == user.organization_id,
        )
        .first()
    )
    if not med:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return med


@router.get("")
def list_lineas_base(
    estado: str | None = None,
    opportunity_id: str | None = None,
    indicador: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.view")),
):
    query = db.query(LineaBase).filter(LineaBase.organization_id == user.organization_id)
    if estado:
        query = query.filter(LineaBase.estado == estado)
    if opportunity_id:
        query = query.filter(LineaBase.opportunity_id == opportunity_id)
    if indicador:
        query = query.filter(LineaBase.indicador.ilike(f"%{indicador}%"))
    items = query.order_by(LineaBase.created_at.desc()).limit(200).all()
    return {"items": [svc.linea_base_to_dict(i) for i in items], "total": len(items)}


@router.post("")
def create_linea_base(
    body: LineaBaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.manage")),
):
    try:
        lb = svc.create_linea_base(
            db,
            organization_id=user.organization_id,
            user_id=user.id,
            **body.model_dump(),
        )
        db.commit()
        return svc.linea_base_to_dict(lb)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{linea_base_id}")
def get_linea_base(
    linea_base_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.view")),
):
    lb = _get_linea_base(db, linea_base_id, user)
    mediciones = (
        db.query(LineaBaseMedicion)
        .filter(LineaBaseMedicion.linea_base_id == lb.id)
        .order_by(LineaBaseMedicion.created_at)
        .all()
    )
    meds_out = []
    for med in mediciones:
        impacto = db.query(LineaBaseImpacto).filter(LineaBaseImpacto.medicion_id == med.id).first()
        meds_out.append(svc.medicion_to_dict(med, impacto))
    return {
        "linea_base": svc.linea_base_to_dict(lb),
        "mediciones": meds_out,
        "evolucion": svc.get_evolucion(db, lb.id, user.organization_id),
        "historial": svc.get_historial(db, lb.id, user.organization_id),
    }


@router.patch("/{linea_base_id}")
def update_linea_base(
    linea_base_id: str,
    body: LineaBaseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.manage")),
):
    lb = _get_linea_base(db, linea_base_id, user)
    try:
        svc.update_linea_base(db, lb, user_id=user.id, **body.model_dump(exclude_unset=True))
        db.commit()
        return svc.linea_base_to_dict(lb)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{linea_base_id}/mediciones")
def add_medicion(
    linea_base_id: str,
    body: MedicionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.manage")),
):
    lb = _get_linea_base(db, linea_base_id, user)
    try:
        med, impacto = svc.register_medicion(db, lb, user_id=user.id, **body.model_dump())
        db.commit()
        return {
            "medicion": svc.medicion_to_dict(med, impacto),
            "comparacion": svc.impacto_to_dict(impacto),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{linea_base_id}/mediciones/{medicion_id}/validar")
def validate_medicion(
    linea_base_id: str,
    medicion_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.validate")),
):
    lb = _get_linea_base(db, linea_base_id, user)
    med = _get_medicion(db, linea_base_id, medicion_id, user)
    impacto = db.query(LineaBaseImpacto).filter(LineaBaseImpacto.medicion_id == med.id).first()
    if not impacto:
        raise HTTPException(status_code=404, detail="Impacto no encontrado")
    try:
        impacto = svc.validate_medicion(db, lb, med, impacto, user_id=user.id)
        db.commit()
        return {
            "medicion": svc.medicion_to_dict(med, impacto),
            "impacto": svc.impacto_to_dict(impacto),
            "linea_base": svc.linea_base_to_dict(lb),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{linea_base_id}/mediciones/{medicion_id}/atribucion")
def update_atribucion(
    linea_base_id: str,
    medicion_id: str,
    body: AtribucionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.validate")),
):
    lb = _get_linea_base(db, linea_base_id, user)
    med = _get_medicion(db, linea_base_id, medicion_id, user)
    impacto = db.query(LineaBaseImpacto).filter(LineaBaseImpacto.medicion_id == med.id).first()
    if not impacto:
        raise HTTPException(status_code=404, detail="Impacto no encontrado")
    try:
        impacto = svc.update_atribucion(
            db,
            lb,
            impacto,
            med,
            user_id=user.id,
            atribucion_nivel=body.atribucion_nivel,
            atribucion_porcentaje=body.atribucion_porcentaje,
            justificacion=body.justificacion,
            evidencia=body.evidencia,
        )
        db.commit()
        return svc.impacto_to_dict(impacto)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/oportunidad/{opportunity_id}")
def list_by_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("linea_base.view")),
):
    items = (
        db.query(LineaBase)
        .filter(
            LineaBase.organization_id == user.organization_id,
            LineaBase.opportunity_id == opportunity_id,
        )
        .order_by(LineaBase.created_at.desc())
        .all()
    )
    return {"items": [svc.linea_base_to_dict(i) for i in items], "total": len(items)}
