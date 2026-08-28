"""API — Centro de oportunidades y inteligencia proactiva (1030)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.opportunity_models import Opportunity, ProactiveSignal
from app.permissions import check_permission, require_permission
from app.services import proactive_service as svc

router = APIRouter(prefix="/api/oportunidades", tags=["Oportunidades"])


class SignalCreate(BaseModel):
    tipo: str
    dominio: str
    origen: str = "api"
    evento: str
    source_reference: str | None = None
    payload: dict[str, Any] | None = None
    severidad: str = "MEDIA"
    confianza: float = 0.7


class OpportunityEvaluate(BaseModel):
    motivo: str | None = None


class OpportunityApprove(BaseModel):
    aprobado: bool = True
    motivo: str | None = None


class OpportunityActivate(BaseModel):
    auto_execute: bool = False


class OpportunityResult(BaseModel):
    valor_real: float | None = None
    valor_esperado: float | None = None
    evidencia: dict[str, Any] | None = None
    estado_resultado: str = "EXITO"


class TrackingCreate(BaseModel):
    accion: str
    kpi_inicial: dict | None = None
    kpi_objetivo: dict | None = None
    bloqueo: str | None = None


def _opp_dict(o: Opportunity) -> dict[str, Any]:
    return {
        "id": o.id,
        "codigo": o.codigo,
        "tipo": o.tipo,
        "dominio": o.dominio,
        "signal_id": o.signal_id,
        "titulo": o.titulo,
        "descripcion": o.descripcion,
        "estado": o.estado,
        "urgencia": o.urgencia,
        "riesgo": o.riesgo,
        "impacto_estimado": float(o.impacto_estimado) if o.impacto_estimado else None,
        "valor_potencial": float(o.valor_potencial) if o.valor_potencial else None,
        "valor_potencial_certidumbre": o.valor_potencial_certidumbre,
        "valor_materializado": float(o.valor_materializado) if o.valor_materializado else None,
        "confianza": float(o.confianza),
        "pertinencia": o.pertinencia,
        "pertinencia_razon": o.pertinencia_razon,
        "momento": o.momento,
        "prioridad_score": float(o.prioridad_score) if o.prioridad_score else None,
        "prioridad_componentes": json.loads(o.prioridad_componentes_json) if o.prioridad_componentes_json else None,
        "equipo": json.loads(o.equipo_json) if o.equipo_json else None,
        "siguiente_accion": json.loads(o.siguiente_accion_json) if o.siguiente_accion_json else None,
        "work_plan_id": o.work_plan_id,
        "finops_reference": o.finops_reference,
        "atribucion_nivel": o.atribucion_nivel,
        "correlation_id": o.correlation_id,
        "fecha_deteccion": o.fecha_deteccion.isoformat() if o.fecha_deteccion else None,
        "contexto": json.loads(o.contexto_json) if o.contexto_json else None,
        "evidencia": json.loads(o.evidencia_json) if o.evidencia_json else None,
        "resultado": json.loads(o.resultado_json) if o.resultado_json else None,
    }


def _get_opp(db: Session, opp_id: str, user: User) -> Opportunity:
    opp = db.query(Opportunity).filter(
        Opportunity.id == opp_id,
        Opportunity.organization_id == user.organization_id,
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return opp


@router.get("")
def list_opportunities(
    estado: str | None = None,
    dominio: str | None = None,
    tipo: str | None = None,
    q: str | None = None,
    sort: str = "prioridad",
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    query = db.query(Opportunity).filter(Opportunity.organization_id == user.organization_id)
    if estado:
        query = query.filter(Opportunity.estado == estado)
    if dominio:
        query = query.filter(Opportunity.dominio == dominio)
    if tipo:
        query = query.filter(Opportunity.tipo == tipo)
    if q:
        query = query.filter(Opportunity.titulo.ilike(f"%{q}%"))
    if sort == "fecha":
        query = query.order_by(Opportunity.fecha_deteccion.desc())
    else:
        query = query.order_by(Opportunity.prioridad_score.desc().nullslast(), Opportunity.fecha_deteccion.desc())
    items = query.limit(200).all()
    return {"items": [_opp_dict(o) for o in items], "total": len(items)}


@router.get("/resumen")
def business_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    return svc.business_summary(db, user.organization_id)


@router.get("/{opportunity_id}")
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    return _opp_dict(_get_opp(db, opportunity_id, user))


@router.post("/senales")
def create_signal(
    body: SignalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.manage")),
):
    signal, is_new = svc.create_signal(
        db,
        organization_id=user.organization_id,
        tipo=body.tipo,
        dominio=body.dominio,
        origen=body.origen,
        evento=body.evento,
        source_reference=body.source_reference,
        payload=body.payload,
        severidad=body.severidad,
        confianza=body.confianza,
    )
    db.commit()
    return {"signal_id": signal.id, "is_new": is_new, "procesada": signal.procesada}


@router.post("/senales/{signal_id}/procesar")
def process_signal(
    signal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.evaluate")),
):
    signal = db.query(ProactiveSignal).filter(
        ProactiveSignal.id == signal_id,
        ProactiveSignal.organization_id == user.organization_id,
    ).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    opp = svc.process_signal(db, signal, user_id=user.id)
    db.commit()
    return _opp_dict(opp) if opp else {"message": "Señal ya procesada"}


@router.post("/pipeline-proactivo")
def run_proactive_pipeline(
    body: SignalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.evaluate")),
):
    result = svc.run_proactive_pipeline(
        db,
        organization_id=user.organization_id,
        tipo=body.tipo,
        dominio=body.dominio,
        evento=body.evento,
        payload=body.payload,
        origen=body.origen,
        user_id=user.id,
    )
    db.commit()
    return result


@router.post("/{opportunity_id}/evaluar")
def evaluate_opportunity(
    opportunity_id: str,
    body: OpportunityEvaluate = OpportunityEvaluate(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.evaluate")),
):
    opp = _get_opp(db, opportunity_id, user)
    ctx = json.loads(opp.contexto_json) if opp.contexto_json else {}
    capacidad = svc.assess_capability_360(db, organization_id=user.organization_id, dominio=opp.dominio)
    pert = svc.evaluate_pertinence(ctx, impacto=float(opp.impacto_estimado or 0), capacidad=capacidad)
    opp.pertinencia = pert["resultado"]
    opp.pertinencia_razon = pert["razon"]
    momento = svc.evaluate_momento(urgencia=opp.urgencia, capacidad=capacidad)
    opp.momento = momento["resultado"]
    svc.prioritize_opportunities_global(db, user.organization_id)
    equipo = svc.select_team_for_opportunity(db, opp)
    accion = svc.compute_next_best_action(db, opp, capacidad=capacidad, equipo=equipo)
    db.commit()
    return {"oportunidad": _opp_dict(opp), "siguiente_accion": accion}


@router.post("/priorizar")
def prioritize_all(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.evaluate")),
):
    result = svc.prioritize_opportunities_global(db, user.organization_id)
    db.commit()
    return result


@router.get("/{opportunity_id}/siguiente-accion")
def get_next_action(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    opp = _get_opp(db, opportunity_id, user)
    accion = json.loads(opp.siguiente_accion_json) if opp.siguiente_accion_json else None
    if not accion:
        capacidad = svc.assess_capability_360(db, organization_id=user.organization_id, dominio=opp.dominio)
        equipo = json.loads(opp.equipo_json) if opp.equipo_json else None
        accion = svc.compute_next_best_action(db, opp, capacidad=capacidad, equipo=equipo)
        db.commit()
    return accion


@router.post("/{opportunity_id}/aprobar")
def approve_opportunity(
    opportunity_id: str,
    body: OpportunityApprove,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.approve")),
):
    opp = _get_opp(db, opportunity_id, user)
    svc.approve_opportunity(db, opp, user_id=user.id, aprobado=body.aprobado, motivo=body.motivo)
    db.commit()
    return _opp_dict(opp)


@router.post("/{opportunity_id}/activar")
def activate_opportunity(
    opportunity_id: str,
    body: OpportunityActivate = OpportunityActivate(),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.activate")),
):
    opp = _get_opp(db, opportunity_id, user)
    result = svc.activate_opportunity(db, opp, user_id=user.id, auto_execute=body.auto_execute)
    db.commit()
    return result


@router.post("/{opportunity_id}/seguimiento")
def add_tracking(
    opportunity_id: str,
    body: TrackingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.manage")),
):
    from app.opportunity_models import OpportunityTracking

    opp = _get_opp(db, opportunity_id, user)
    track = OpportunityTracking(
        opportunity_id=opp.id,
        organization_id=user.organization_id,
        accion=body.accion,
        responsable_id=user.id,
        bloqueo=body.bloqueo,
        kpi_inicial_json=json.dumps(body.kpi_inicial) if body.kpi_inicial else None,
        kpi_objetivo_json=json.dumps(body.kpi_objetivo) if body.kpi_objetivo else None,
    )
    db.add(track)
    db.commit()
    return {"tracking_id": track.id}


@router.post("/{opportunity_id}/resultado")
def register_result(
    opportunity_id: str,
    body: OpportunityResult,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.manage")),
):
    opp = _get_opp(db, opportunity_id, user)
    result = svc.register_result(
        db, opp, user_id=user.id,
        valor_real=body.valor_real,
        valor_esperado=body.valor_esperado,
        evidencia=body.evidencia,
        estado_resultado=body.estado_resultado,
    )
    db.commit()
    return {"resultado": result, "oportunidad": _opp_dict(opp)}


@router.get("/{opportunity_id}/trazabilidad")
def get_trace(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    _get_opp(db, opportunity_id, user)
    return svc.get_full_trace(db, opportunity_id, user.organization_id)
