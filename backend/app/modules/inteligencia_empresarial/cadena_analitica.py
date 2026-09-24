"""Cadena analítica EVIDENCIA → … → ACCIÓN con trazabilidad."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionHallazgo, EvaluacionOportunidadLink
from app.opportunity_models import Opportunity, OpportunityTrace
from app.services import diagnostic_service as diag_svc
from app.services import evaluacion_service as eval_svc
from app.services import transformacion_service as trans_svc
from app.modules.inteligencia_empresarial.contracts import CADENA_PASOS


def _nodo(paso: str, *, ref_id: str | None, titulo: str, detalle: str | None = None, enlace: str | None = None) -> dict[str, Any]:
    return {
        "paso": paso,
        "id": ref_id,
        "titulo": titulo,
        "detalle": detalle,
        "enlace": enlace,
    }


def construir_cadena_expediente(db: Session, organization_id: str, expediente_id: str) -> dict[str, Any]:
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    nodos: list[dict[str, Any]] = []

    detail = eval_svc.expediente_to_detail(db, exp)
    for item in detail.get("informacion", [])[:20]:
        if item.get("respuesta"):
            nodos.append(_nodo(
                "EVIDENCIA",
                ref_id=item.get("id"),
                titulo=item.get("etiqueta", item.get("campo")),
                detalle=item.get("respuesta")[:200] if item.get("respuesta") else None,
            ))

    hallazgos = (
        db.query(EvaluacionHallazgo)
        .filter(EvaluacionHallazgo.expediente_id == exp.id)
        .order_by(EvaluacionHallazgo.created_at)
        .all()
    )
    for h in hallazgos:
        nodos.append(_nodo(
            "HALLAZGO",
            ref_id=h.id,
            titulo=h.titulo,
            detalle=h.descripcion[:200] if h.descripcion else None,
            enlace=f"/evaluaciones/{exp.id}",
        ))
        if h.impacto_resumen:
            nodos.append(_nodo("IMPACTO", ref_id=h.id, titulo=h.titulo, detalle=h.impacto_resumen[:200]))
        if h.tipo_contenido == "RECOMENDACION":
            nodos.append(_nodo("RECOMENDACION", ref_id=h.id, titulo=h.titulo, detalle=h.descripcion[:200]))

    links = (
        db.query(EvaluacionOportunidadLink)
        .filter(EvaluacionOportunidadLink.expediente_id == exp.id)
        .all()
    )
    for link in links:
        opp = db.query(Opportunity).filter(Opportunity.id == link.opportunity_id).first()
        if opp:
            nodos.append(_nodo(
                "OPORTUNIDAD",
                ref_id=opp.id,
                titulo=opp.titulo,
                detalle=opp.descripcion[:200] if opp.descripcion else None,
                enlace=f"/oportunidades/{opp.id}",
            ))
            traces = (
                db.query(OpportunityTrace)
                .filter(OpportunityTrace.opportunity_id == opp.id)
                .order_by(OpportunityTrace.created_at.desc())
                .limit(3)
                .all()
            )
            for t in traces:
                nodos.append(_nodo(
                    "ACCION",
                    ref_id=t.id,
                    titulo=t.etapa,
                    detalle=str(t.detalle_json)[:200] if t.detalle_json else None,
                ))

    dossier = trans_svc.get_dossier_completo(db, organization_id)
    if dossier:
        for causa in dossier.get("causas", [])[:10]:
            nodos.append(_nodo(
                "CAUSA",
                ref_id=causa.get("id"),
                titulo=causa.get("tipo", "CAUSA"),
                detalle=causa.get("descripcion"),
            ))

    if exp.diagnostic_id:
        try:
            trace = diag_svc.get_diagnostic_trace(db, organization_id, exp.diagnostic_id)
            for ext in (trace.get("cadenas_externas") or [])[:5]:
                nodos.append(_nodo("ANALISIS", ref_id=ext.get("id"), titulo=ext.get("etapa", "DIAGNÓSTICO"), detalle=ext.get("resumen")))
        except Exception:
            pass

    return {
        "expediente_id": expediente_id,
        "correlation_id": exp.correlation_id,
        "pasos_canonicos": list(CADENA_PASOS),
        "nodos": nodos,
        "total": len(nodos),
    }


def construir_cadena_oportunidad(db: Session, organization_id: str, opportunity_id: str) -> dict[str, Any]:
    from app.services import proactive_service as opp_svc

    trace = opp_svc.get_full_trace(db, opportunity_id, organization_id)
    nodos: list[dict[str, Any]] = []
    if trace.get("senal"):
        s = trace["senal"]
        nodos.append(_nodo("EVIDENCIA", ref_id=s.get("id"), titulo=s.get("titulo", "Señal"), detalle=s.get("descripcion")))
    for h in trace.get("hallazgos_vinculados") or []:
        nodos.append(_nodo("HALLAZGO", ref_id=h.get("id"), titulo=h.get("titulo")))
    if trace.get("oportunidad"):
        o = trace["oportunidad"]
        nodos.append(_nodo("OPORTUNIDAD", ref_id=o.get("id"), titulo=o.get("titulo")))
    for t in trace.get("transiciones") or []:
        nodos.append(_nodo("ACCION", ref_id=t.get("id"), titulo=t.get("estado_nuevo", "Transición"), detalle=t.get("motivo")))
    return {
        "oportunidad_id": opportunity_id,
        "pasos_canonicos": list(CADENA_PASOS),
        "nodos": nodos,
        "trazabilidad_completa": trace,
    }
