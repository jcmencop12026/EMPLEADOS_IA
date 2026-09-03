"""Evaluación adaptativa por nivel — plan de información y evaluadores."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionInformacionItem
from app.services import evaluacion_service as eval_svc


def plan_informacion_adaptativa(db: Session, expediente_id: str, organization_id: str) -> dict[str, Any]:
    """Qué necesita conocer, qué ya tiene, qué falta, documentos e indicadores."""
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    eval_svc.sync_informacion_adaptativa(db, exp)
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )
    from app.modules.inteligencia_empresarial.suficiencia import evaluar_suficiencia_unificada

    suf = evaluar_suficiencia_unificada(db, organization_id, expediente_id)
    preguntas = [
        {
            "campo": i.campo,
            "etiqueta": i.etiqueta,
            "estado": i.estado,
            "obligatorio": i.obligatorio,
            "por_que": i.por_que,
            "profundidad": exp.nivel,
        }
        for i in items
        if i.estado in ("PENDIENTE", "INCOMPLETO")
    ]
    documentos_requeridos = [
        i.etiqueta for i in items
        if i.campo == "evidencias_documentales" and i.estado != "RECIBIDO"
    ]
    indicadores = [
        i.etiqueta for i in items
        if i.campo == "metricas_actuales"
    ]
    return {
        "expediente_id": expediente_id,
        "nivel": exp.nivel,
        "profundidad_requerida": exp.nivel,
        "que_necesita_conocer": [i.etiqueta for i in items if i.obligatorio],
        "que_ya_posee": [i.etiqueta for i in items if i.estado == "RECIBIDO"],
        "que_falta": [f["etiqueta"] for f in suf.get("faltantes", [])],
        "cubierto_dossier": suf.get("cubierto_por_dossier", []),
        "documentos_requeridos": documentos_requeridos,
        "indicadores_necesarios": indicadores,
        "preguntas_pendientes": preguntas,
        "suficiencia": suf,
    }


def ejecutar_evaluacion_adaptativa(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
) -> dict[str, Any]:
    """Evaluador según nivel PRELIMINAR / DIAGNOSTICA / PROFUNDA."""
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    nivel = exp.nivel or "PRELIMINAR"

    if nivel == "PRELIMINAR":
        result = eval_svc.ejecutar_evaluacion_preliminar(db, expediente_id, organization_id, user_id=user_id)
        profundidad = "superficial"
    elif nivel == "DIAGNOSTICA":
        result = eval_svc.ejecutar_evaluacion_preliminar(db, expediente_id, organization_id, user_id=user_id)
        items = db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.expediente_id == exp.id).all()
        metricas = next((i for i in items if i.campo == "metricas_actuales" and i.respuesta), None)
        if metricas:
            eval_svc.create_hallazgo(
                db,
                expediente_id,
                organization_id,
                user_id=user_id,
                titulo="Métricas actuales registradas",
                descripcion=metricas.respuesta[:500],
                tipo_contenido="HECHO",
                confianza="MEDIA",
                explicacion_confianza="Información diagnóstica declarada por el evaluador.",
                origen="evaluacion.diagnostica",
            )
        profundidad = "diagnostica"
    else:
        result = eval_svc.ejecutar_evaluacion_preliminar(db, expediente_id, organization_id, user_id=user_id)
        items = db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.expediente_id == exp.id).all()
        evidencias = [i for i in items if i.campo == "evidencias_documentales" and i.respuesta]
        if evidencias:
            eval_svc.create_hallazgo(
                db,
                expediente_id,
                organization_id,
                user_id=user_id,
                titulo="Evidencia documental profunda",
                descripcion=evidencias[0].respuesta[:500],
                tipo_contenido="HECHO",
                confianza="ALTA",
                explicacion_confianza="Evaluación profunda con evidencia documental.",
                origen="evaluacion.profunda",
                evidencia=evidencias[0].evidencia_ref,
            )
        profundidad = "profunda"

    exp.estado = "PRELIMINAR" if nivel == "PRELIMINAR" else nivel
    return {
        **result,
        "nivel_aplicado": nivel,
        "profundidad": profundidad,
        "plan": plan_informacion_adaptativa(db, expediente_id, organization_id),
    }
