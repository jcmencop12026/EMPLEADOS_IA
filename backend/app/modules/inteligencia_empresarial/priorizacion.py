"""Priorización HACER / ESTUDIAR / ESPERAR / DESCARTAR — mapeo sobre motor 1030."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.opportunity_models import Opportunity
from app.services import proactive_service as opp_svc


def _clasificar_decision(opp: Opportunity) -> str:
    pert = (opp.pertinencia or "").upper()
    estado = (opp.estado or "").upper()
    if estado in ("DESCARTADA", "CERRADA_RECHAZADA") or pert == "DESCARTAR":
        return "DESCARTAR"
    if pert == "ACTUAR" or estado in ("APROBADA", "EN_EJECUCION", "MATERIALIZADA"):
        return "HACER"
    if pert in ("POSPONER", "SOLICITAR_APROBACION") or estado in ("EN_SEGUIMIENTO",):
        return "ESPERAR"
    return "ESTUDIAR"


def priorizar_oportunidad(db: Session, organization_id: str, opportunity_id: str) -> dict[str, Any]:
    opp = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.organization_id == organization_id,
    ).first()
    if not opp:
        return {"error": "Oportunidad no encontrada"}
    score_data = opp_svc._score_opportunity(opp)  # noqa: SLF001
    decision = _clasificar_decision(opp)
    comp = score_data.get("componentes", {})
    return {
        "oportunidad_id": opportunity_id,
        "titulo": opp.titulo,
        "decision": decision,
        "pertinencia_original": opp.pertinencia,
        "estado": opp.estado,
        "factores": {
            "impacto": comp.get("impacto"),
            "factibilidad": comp.get("esfuerzo_inverso"),
            "urgencia": comp.get("urgencia"),
            "riesgo": comp.get("riesgo_inverso"),
            "confianza": float(opp.confianza or 0),
            "prioridad_score": score_data.get("prioridad_score"),
        },
        "explicacion": score_data.get("explicacion") or opp.pertinencia_razon,
    }


def priorizar_portafolio(db: Session, organization_id: str) -> dict[str, Any]:
    ranking = opp_svc.prioritize_opportunities_global(db, organization_id)
    clasificado: dict[str, list] = {"HACER": [], "ESTUDIAR": [], "ESPERAR": [], "DESCARTAR": []}
    for item in ranking.get("ranking", []):
        opp = db.query(Opportunity).filter(Opportunity.id == item["opportunity_id"]).first()
        if not opp:
            continue
        decision = _clasificar_decision(opp)
        clasificado[decision].append({
            "oportunidad_id": opp.id,
            "titulo": opp.titulo,
            "prioridad_score": item.get("prioridad_score"),
            "ranking": item.get("ranking"),
        })
    return {
        "metodologia": ranking.get("metodologia"),
        "por_decision": clasificado,
        "ranking_completo": ranking.get("ranking"),
        "total": ranking.get("total"),
    }
