"""Servicio expediente de evaluación empresarial EIAAX — Bloque Producto 1."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.evaluacion_models import (
    CONFIANZA_NIVELES,
    EVALUACION_ESTADOS,
    EVALUACION_NIVELES,
    INFO_ESTADOS,
    EvaluacionExpediente,
    EvaluacionHallazgo,
    EvaluacionInformacionItem,
    EvaluacionOportunidadLink,
    EvaluacionVisibilidadLog,
)
from app.llm_models import LlmProviderConfig
from app.opportunity_models import Opportunity
from app.services import proactive_service as opp_svc
from app.services.coordinator import route_task
from app.gateway.providers import is_executable_llm_provider
from app.gateway.secrets import secret_configured

# Catálogo adaptativo — campos por profundidad
_INFO_CATALOGO: list[dict[str, Any]] = [
    {
        "campo": "contexto_negocio",
        "etiqueta": "Contexto del negocio",
        "explicacion": "Sector, tamaño y modelo operativo de la entidad.",
        "por_que": "Permite contextualizar el análisis y calibrar expectativas.",
        "impacto_precision": "Sin contexto, las inferencias pueden ser genéricas.",
        "niveles": {"PRELIMINAR", "DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
    },
    {
        "campo": "problema_detalle",
        "etiqueta": "Descripción del problema",
        "explicacion": "Narrativa del dolor o necesidad principal.",
        "por_que": "Define el foco de la evaluación.",
        "impacto_precision": "Problemas vagos generan hallazgos de baja confianza.",
        "niveles": {"PRELIMINAR", "DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
    },
    {
        "campo": "procesos_afectados",
        "etiqueta": "Procesos o áreas afectadas",
        "explicacion": "Procesos, departamentos o flujos involucrados.",
        "por_que": "Delimita el alcance del análisis.",
        "impacto_precision": "Sin alcance definido, el impacto es estimado.",
        "niveles": {"PRELIMINAR", "DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
    },
    {
        "campo": "metricas_actuales",
        "etiqueta": "Métricas o indicadores actuales",
        "explicacion": "KPIs, volúmenes o mediciones disponibles.",
        "por_que": "Sustenta el análisis cuantitativo.",
        "impacto_precision": "Sin métricas, el impacto queda en proyección.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
    },
    {
        "campo": "sistemas_herramientas",
        "etiqueta": "Sistemas y herramientas",
        "explicacion": "ERP, hojas de cálculo, aplicaciones relevantes.",
        "por_que": "Identifica fuentes de datos y restricciones técnicas.",
        "impacto_precision": "Afecta la viabilidad de soluciones propuestas.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": False,
    },
    {
        "campo": "restricciones",
        "etiqueta": "Restricciones y dependencias",
        "explicacion": "Presupuesto, plazos, regulación o dependencias críticas.",
        "por_que": "Evita recomendaciones no viables.",
        "impacto_precision": "Sin restricciones, las oportunidades pueden ser irreales.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": False,
    },
    {
        "campo": "evidencias_documentales",
        "etiqueta": "Evidencias y documentos",
        "explicacion": "Informes, contratos, datos exportados u otras evidencias.",
        "por_que": "Fundamenta hallazgos con hechos verificables.",
        "impacto_precision": "Aumenta confianza de HECHO vs INFERENCIA.",
        "niveles": {"PROFUNDA"},
        "obligatorio": True,
    },
    {
        "campo": "stakeholders",
        "etiqueta": "Partes interesadas",
        "explicacion": "Responsables, patrocinadores y usuarios clave.",
        "por_que": "Facilita la siguiente acción y gobernanza.",
        "impacto_precision": "Mejora priorización de oportunidades.",
        "niveles": {"PROFUNDA"},
        "obligatorio": False,
    },
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_correlation() -> str:
    return str(uuid.uuid4())


def _next_codigo(db: Session, organization_id: str) -> str:
    year = _utcnow().year
    prefix = f"EVA-{year}-"
    count = (
        db.query(func.count(EvaluacionExpediente.id))
        .filter(
            EvaluacionExpediente.organization_id == organization_id,
            EvaluacionExpediente.codigo.like(f"{prefix}%"),
        )
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def _get_expediente(db: Session, expediente_id: str, organization_id: str) -> EvaluacionExpediente:
    row = (
        db.query(EvaluacionExpediente)
        .filter(
            EvaluacionExpediente.id == expediente_id,
            EvaluacionExpediente.organization_id == organization_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Expediente de evaluación no encontrado")
    return row


def _confianza_from_pct(pct: int) -> str:
    if pct >= 75:
        return "ALTA"
    if pct >= 45:
        return "MEDIA"
    return "BAJA"


def _confianza_from_float(value: float) -> str:
    return _confianza_from_pct(int(round(max(0.0, min(1.0, value)) * 100)))


def _tipo_contenido_desde_diagnostico(tipo: str | None) -> str:
    if tipo == "HECHO":
        return "HECHO"
    if tipo in {"INTERPRETACION", "INFERENCIA"}:
        return "INFERENCIA"
    if tipo in {"HECHO", "INFERENCIA", "PROYECCION", "RECOMENDACION"}:
        return tipo
    return "INFERENCIA"


def _item_estado(item: EvaluacionInformacionItem) -> str:
    if item.respuesta and item.respuesta.strip():
        return "RECIBIDO"
    if not item.obligatorio:
        return "OPCIONAL"
    return "PENDIENTE"


def _recalc_metrics(exp: EvaluacionExpediente, items: list[EvaluacionInformacionItem]) -> None:
    obligatorios = [i for i in items if i.obligatorio]
    if not obligatorios:
        exp.porcentaje_informacion = 100
    else:
        recibidos = sum(1 for i in obligatorios if i.estado == "RECIBIDO")
        exp.porcentaje_informacion = int(round(100 * recibidos / len(obligatorios)))
    exp.confianza_global = _confianza_from_pct(exp.porcentaje_informacion)


def _info_item_dict(item: EvaluacionInformacionItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "campo": item.campo,
        "etiqueta": item.etiqueta,
        "estado": item.estado,
        "obligatorio": item.obligatorio,
        "explicacion": item.explicacion,
        "por_que": item.por_que,
        "impacto_precision": item.impacto_precision,
        "respuesta": item.respuesta,
        "evidencia_ref": item.evidencia_ref,
        "orden": item.orden,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _hallazgo_dict(h: EvaluacionHallazgo, *, include_internal: bool = True) -> dict[str, Any]:
    data = {
        "id": h.id,
        "titulo": h.titulo,
        "descripcion": h.descripcion,
        "tipo_contenido": h.tipo_contenido,
        "confianza": h.confianza,
        "explicacion_confianza": h.explicacion_confianza,
        "evidencia": h.evidencia,
        "origen": h.origen,
        "impacto_resumen": h.impacto_resumen,
        "visible_entidad": h.visible_entidad,
        "es_problema_original": h.es_problema_original,
        "opportunity_id": h.opportunity_id,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }
    if include_internal:
        data["diagnostic_finding_id"] = h.diagnostic_finding_id
        data["correlation_id"] = h.correlation_id
    return data


def expediente_to_summary(exp: EvaluacionExpediente) -> dict[str, Any]:
    return {
        "id": exp.id,
        "codigo": exp.codigo,
        "titulo": exp.titulo,
        "entidad_nombre": exp.entidad_nombre,
        "estado": exp.estado,
        "nivel": exp.nivel,
        "porcentaje_informacion": exp.porcentaje_informacion,
        "confianza_global": exp.confianza_global,
        "valor_potencial": exp.valor_potencial,
        "area_proceso": exp.area_proceso,
        "created_at": exp.created_at.isoformat() if exp.created_at else None,
        "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
    }


def expediente_to_detail(
    db: Session,
    exp: EvaluacionExpediente,
    *,
    include_internal: bool = True,
) -> dict[str, Any]:
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )
    hallazgos = (
        db.query(EvaluacionHallazgo)
        .filter(EvaluacionHallazgo.expediente_id == exp.id)
        .order_by(EvaluacionHallazgo.created_at.desc())
        .all()
    )
    links = (
        db.query(EvaluacionOportunidadLink)
        .filter(EvaluacionOportunidadLink.expediente_id == exp.id)
        .all()
    )
    data: dict[str, Any] = {
        **expediente_to_summary(exp),
        "entidad_ref": exp.entidad_ref,
        "necesidad": exp.necesidad,
        "objetivo": exp.objetivo,
        "diagnostic_id": exp.diagnostic_id,
        "correlation_id": exp.correlation_id,
        "informacion": [_info_item_dict(i) for i in items],
        "hallazgos": [
            _hallazgo_dict(h, include_internal=include_internal)
            for h in hallazgos
            if include_internal or h.visible_entidad
        ],
        "oportunidades_vinculadas": [l.opportunity_id for l in links],
    }
    if include_internal:
        data["notas_internas"] = exp.notas_internas
        data["responsable_id"] = exp.responsable_id
    return data


def list_expedientes(
    db: Session,
    organization_id: str,
    *,
    estado: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    query = db.query(EvaluacionExpediente).filter(EvaluacionExpediente.organization_id == organization_id)
    if estado:
        query = query.filter(EvaluacionExpediente.estado == estado)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (EvaluacionExpediente.titulo.ilike(like))
            | (EvaluacionExpediente.entidad_nombre.ilike(like))
            | (EvaluacionExpediente.codigo.ilike(like))
        )
    total = query.count()
    rows = query.order_by(EvaluacionExpediente.updated_at.desc()).offset(offset).limit(limit).all()
    return {
        "items": [expediente_to_summary(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def create_expediente(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    titulo: str,
    entidad_nombre: str,
    entidad_ref: str | None = None,
    necesidad: str | None = None,
    objetivo: str | None = None,
    area_proceso: str | None = None,
    sector: str | None = None,
    nivel: str = "PRELIMINAR",
) -> EvaluacionExpediente:
    if nivel not in EVALUACION_NIVELES:
        raise HTTPException(status_code=422, detail=f"Nivel inválido: {nivel}")
    exp = EvaluacionExpediente(
        organization_id=organization_id,
        codigo=_next_codigo(db, organization_id),
        titulo=titulo,
        entidad_nombre=entidad_nombre,
        entidad_ref=entidad_ref,
        necesidad=necesidad,
        objetivo=objetivo,
        area_proceso=area_proceso,
        sector=sector,
        nivel=nivel,
        estado="BORRADOR",
        correlation_id=_new_correlation(),
        created_by=user_id,
        responsable_id=user_id,
    )
    db.add(exp)
    db.flush()
    sync_informacion_adaptativa(db, exp, user_id=user_id)
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="evaluacion.create",
        detail=json.dumps({"codigo": exp.codigo, "entidad": entidad_nombre, "resource_id": exp.id}),
        commit=False,
    )
    return exp


def update_expediente(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
    **fields: Any,
) -> EvaluacionExpediente:
    exp = _get_expediente(db, expediente_id, organization_id)
    nivel_changed = False
    allowed = {
        "titulo", "entidad_nombre", "entidad_ref", "necesidad", "objetivo",
        "area_proceso", "nivel", "estado", "notas_internas", "responsable_id", "valor_potencial",
    }
    for key, value in fields.items():
        if key not in allowed or value is None:
            continue
        if key == "estado" and value not in EVALUACION_ESTADOS:
            raise HTTPException(status_code=422, detail=f"Estado inválido: {value}")
        if key == "nivel":
            if value not in EVALUACION_NIVELES:
                raise HTTPException(status_code=422, detail=f"Nivel inválido: {value}")
            nivel_changed = value != exp.nivel
        setattr(exp, key, value)
    if nivel_changed:
        sync_informacion_adaptativa(db, exp, user_id=user_id)
    elif any(k in fields for k in ("necesidad", "objetivo", "area_proceso")):
        sync_informacion_adaptativa(db, exp, user_id=user_id, preserve_responses=True)
    exp.updated_at = _utcnow()
    return exp


def sync_informacion_adaptativa(
    db: Session,
    exp: EvaluacionExpediente,
    *,
    user_id: str | None = None,
    preserve_responses: bool = True,
) -> list[EvaluacionInformacionItem]:
    existing = {
        i.campo: i
        for i in db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .all()
    }
    applicable = [c for c in _INFO_CATALOGO if exp.nivel in c["niveles"]]
    items: list[EvaluacionInformacionItem] = []
    for orden, spec in enumerate(applicable):
        prev = existing.get(spec["campo"])
        if prev:
            prev.etiqueta = spec["etiqueta"]
            prev.explicacion = spec["explicacion"]
            prev.por_que = spec["por_que"]
            prev.impacto_precision = spec["impacto_precision"]
            prev.obligatorio = spec["obligatorio"]
            prev.orden = orden
            if not preserve_responses:
                prev.respuesta = None
            prev.estado = _item_estado(prev)
            items.append(prev)
            continue
        item = EvaluacionInformacionItem(
            organization_id=exp.organization_id,
            expediente_id=exp.id,
            campo=spec["campo"],
            etiqueta=spec["etiqueta"],
            explicacion=spec["explicacion"],
            por_que=spec["por_que"],
            impacto_precision=spec["impacto_precision"],
            obligatorio=spec["obligatorio"],
            orden=orden,
            estado="PENDIENTE",
        )
        db.add(item)
        items.append(item)

    # Marcar obsoletos como opcionales fuera de catálogo vigente
    valid_campos = {s["campo"] for s in applicable}
    for campo, item in existing.items():
        if campo not in valid_campos:
            item.obligatorio = False
            item.estado = "OPCIONAL" if not item.respuesta else "RECIBIDO"
            if item not in items:
                items.append(item)

    db.flush()
    _recalc_metrics(exp, items)
    if exp.estado == "BORRADOR" and exp.necesidad:
        exp.estado = "EN_CURSO"
    return items


def update_informacion_item(
    db: Session,
    expediente_id: str,
    organization_id: str,
    item_id: str,
    *,
    respuesta: str | None = None,
    evidencia_ref: str | None = None,
    estado: str | None = None,
) -> EvaluacionInformacionItem:
    exp = _get_expediente(db, expediente_id, organization_id)
    item = (
        db.query(EvaluacionInformacionItem)
        .filter(
            EvaluacionInformacionItem.id == item_id,
            EvaluacionInformacionItem.expediente_id == exp.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Ítem de información no encontrado")
    if respuesta is not None:
        item.respuesta = respuesta.strip() or None
    if evidencia_ref is not None:
        item.evidencia_ref = evidencia_ref.strip() or None
    if estado and estado in INFO_ESTADOS:
        item.estado = estado
    else:
        item.estado = _item_estado(item)
    item.updated_at = _utcnow()
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .all()
    )
    _recalc_metrics(exp, items)
    exp.updated_at = _utcnow()
    return item


def ejecutar_evaluacion_preliminar(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
) -> dict[str, Any]:
    """Genera hallazgos iniciales a partir de la información disponible."""
    exp = _get_expediente(db, expediente_id, organization_id)
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )
    _recalc_metrics(exp, items)
    created: list[EvaluacionHallazgo] = []

    if exp.necesidad:
        h = EvaluacionHallazgo(
            organization_id=organization_id,
            expediente_id=exp.id,
            titulo="Problema original identificado",
            descripcion=exp.necesidad,
            tipo_contenido="HECHO",
            confianza="ALTA" if exp.porcentaje_informacion >= 50 else "MEDIA",
            explicacion_confianza="Declarado explícitamente por el evaluador como necesidad principal.",
            evidencia=exp.objetivo,
            origen="expediente.necesidad",
            es_problema_original=True,
            visible_entidad=False,
            correlation_id=exp.correlation_id,
            created_by=user_id,
        )
        db.add(h)
        created.append(h)

    pendientes = [i for i in items if i.estado in ("PENDIENTE", "INCOMPLETO") and i.obligatorio]
    if pendientes:
        h = EvaluacionHallazgo(
            organization_id=organization_id,
            expediente_id=exp.id,
            titulo="Información pendiente que limita precisión",
            descripcion="; ".join(f"{i.etiqueta}" for i in pendientes[:5]),
            tipo_contenido="INFERENCIA",
            confianza="BAJA",
            explicacion_confianza=f"Faltan {len(pendientes)} requisitos obligatorios para el nivel {exp.nivel}.",
            evidencia=json.dumps([i.campo for i in pendientes], ensure_ascii=False),
            origen="evaluacion.informacion_adaptativa",
            impacto_resumen="La evaluación puede continuar de forma preliminar con menor certeza.",
            visible_entidad=False,
            correlation_id=exp.correlation_id,
            created_by=user_id,
        )
        db.add(h)
        created.append(h)

    if exp.objetivo:
        h = EvaluacionHallazgo(
            organization_id=organization_id,
            expediente_id=exp.id,
            titulo="Objetivo de evaluación",
            descripcion=exp.objetivo,
            tipo_contenido="HECHO",
            confianza=exp.confianza_global,
            explicacion_confianza="Objetivo declarado en el expediente.",
            origen="expediente.objetivo",
            visible_entidad=False,
            correlation_id=exp.correlation_id,
            created_by=user_id,
        )
        db.add(h)
        created.append(h)

    if exp.porcentaje_informacion < 100:
        h = EvaluacionHallazgo(
            organization_id=organization_id,
            expediente_id=exp.id,
            titulo="Evaluación preliminar con información incompleta",
            descripcion=(
                f"Se completó el {exp.porcentaje_informacion}% de la información obligatoria. "
                "Los hallazgos posteriores deben interpretarse como proyección hasta completar datos."
            ),
            tipo_contenido="PROYECCION",
            confianza=exp.confianza_global,
            explicacion_confianza="Proyección basada en cobertura parcial de información.",
            origen="evaluacion.preliminar",
            impacto_resumen="Completar información pendiente mejorará confianza y precisión.",
            visible_entidad=False,
            correlation_id=exp.correlation_id,
            created_by=user_id,
        )
        db.add(h)
        created.append(h)

    exp.estado = "PRELIMINAR" if exp.nivel == "PRELIMINAR" else exp.nivel
    exp.updated_at = _utcnow()
    db.flush()

    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="evaluacion.evaluate",
        detail=json.dumps({"hallazgos_creados": len(created), "porcentaje": exp.porcentaje_informacion, "resource_id": exp.id}),
        commit=False,
    )
    return {
        "expediente": expediente_to_detail(db, exp),
        "hallazgos_creados": len(created),
    }


def create_hallazgo(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
    titulo: str,
    descripcion: str | None = None,
    tipo_contenido: str = "INFERENCIA",
    confianza: str = "MEDIA",
    explicacion_confianza: str | None = None,
    evidencia: str | None = None,
    origen: str | None = None,
    impacto_resumen: str | None = None,
    visible_entidad: bool = False,
    es_problema_original: bool = False,
    diagnostic_finding_id: str | None = None,
) -> EvaluacionHallazgo:
    exp = _get_expediente(db, expediente_id, organization_id)
    if tipo_contenido not in {"HECHO", "INFERENCIA", "PROYECCION", "RECOMENDACION"}:
        raise HTTPException(status_code=422, detail="tipo_contenido inválido")
    if confianza not in CONFIANZA_NIVELES:
        raise HTTPException(status_code=422, detail="confianza inválida")
    h = EvaluacionHallazgo(
        organization_id=organization_id,
        expediente_id=exp.id,
        titulo=titulo,
        descripcion=descripcion,
        tipo_contenido=tipo_contenido,
        confianza=confianza,
        explicacion_confianza=explicacion_confianza,
        evidencia=evidencia,
        origen=origen or "manual",
        impacto_resumen=impacto_resumen,
        visible_entidad=visible_entidad,
        es_problema_original=es_problema_original,
        diagnostic_finding_id=diagnostic_finding_id,
        correlation_id=exp.correlation_id,
        created_by=user_id,
    )
    db.add(h)
    db.flush()
    return h


def set_visibilidad(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    objeto_tipo: str,
    objeto_id: str,
    visible_entidad: bool,
    user_id: str,
) -> dict[str, Any]:
    exp = _get_expediente(db, expediente_id, organization_id)
    if objeto_tipo != "hallazgo":
        raise HTTPException(status_code=422, detail="Solo se admite visibilidad sobre hallazgos en este bloque")
    h = (
        db.query(EvaluacionHallazgo)
        .filter(
            EvaluacionHallazgo.id == objeto_id,
            EvaluacionHallazgo.expediente_id == exp.id,
            EvaluacionHallazgo.organization_id == organization_id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    prev = h.visible_entidad
    h.visible_entidad = visible_entidad
    h.updated_at = _utcnow()
    log = EvaluacionVisibilidadLog(
        organization_id=organization_id,
        expediente_id=exp.id,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        visible_entidad=visible_entidad,
        changed_by=user_id,
    )
    db.add(log)
    from app.services.gobierno_operacional_service import set_visibilidad_general

    set_visibilidad_general(
        db,
        organization_id,
        user_id,
        dominio="evaluacion",
        contexto_id=exp.id,
        objeto_tipo=objeto_tipo,
        objeto_id=objeto_id,
        visible=visible_entidad,
        correlation_id=exp.correlation_id,
    )
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="evaluacion.visibility",
        detail=json.dumps({"antes": prev, "despues": visible_entidad, "resource_id": h.id}),
        commit=False,
    )
    return _hallazgo_dict(h)


def get_vista_entidad(db: Session, expediente_id: str, organization_id: str) -> dict[str, Any]:
    """Vista filtrada — sin datos internos sensibles."""
    exp = _get_expediente(db, expediente_id, organization_id)
    detail = expediente_to_detail(db, exp, include_internal=False)
    # Eliminar campos internos explícitamente
    safe = {
        "codigo": detail["codigo"],
        "titulo": detail["titulo"],
        "entidad_nombre": detail["entidad_nombre"],
        "estado": detail["estado"],
        "nivel": detail["nivel"],
        "objetivo": detail.get("objetivo"),
        "area_proceso": detail.get("area_proceso"),
        "confianza_global": detail["confianza_global"],
        "porcentaje_informacion": detail["porcentaje_informacion"],
        "hallazgos": [
            h for h in detail["hallazgos"]
            if h.get("visible_entidad")
        ],
        "informacion": [
            {
                "etiqueta": i["etiqueta"],
                "estado": i["estado"],
            }
            for i in detail["informacion"]
            if i["estado"] == "RECIBIDO"
        ],
        "impacto": get_impacto_resumen(db, exp.id, organization_id, vista_entidad=True),
        "oportunidades": _oportunidades_visibles(db, exp),
        "etiqueta_demo": "DEMO — DATOS SIMULADOS" if _is_demo_expediente(exp) else None,
        "valor_publicable": _valor_publicable_entidad(db, exp, organization_id),
        "recomendacion_publicable": (
            "Priorizar piloto de automatización de codificación y publicar hallazgos autorizados."
            if _is_demo_expediente(exp)
            else None
        ),
    }
    return safe


def _valor_publicable_entidad(
    db: Session,
    exp: EvaluacionExpediente,
    organization_id: str,
) -> dict[str, Any] | None:
    """Valor/impacto autorizado para vista empresa — sin economía privada."""
    from app.services.demo_economico_horizonte import expediente_economic_resumen

    resumen = expediente_economic_resumen(db, organization_id, exp.id, vista_entidad=True)
    if not resumen:
        return None
    if _is_demo_expediente(exp):
        return {
            "banner": "DEMO — DATOS SIMULADOS",
            "nota": "Cifras ilustrativas para demostración; no constituyen verificación real.",
            "estimado_publicable": resumen.get("estimado"),
            "proyectado_publicable": resumen.get("proyectado"),
            "potencial_publicable": resumen.get("potencial"),
            "simulacion_verificado_publicable": resumen.get("simulacion_verificado"),
        }
    return {
        "estimado": resumen.get("estimado"),
        "potencial": resumen.get("potencial"),
        "verificado": resumen.get("verificado"),
    }


def _oportunidades_visibles(db: Session, exp: EvaluacionExpediente) -> list[dict[str, Any]]:
    links = (
        db.query(EvaluacionOportunidadLink, Opportunity)
        .join(Opportunity, Opportunity.id == EvaluacionOportunidadLink.opportunity_id)
        .filter(
            EvaluacionOportunidadLink.expediente_id == exp.id,
            EvaluacionOportunidadLink.organization_id == exp.organization_id,
        )
        .all()
    )
    visible_hallazgo_opp_ids = {
        h.opportunity_id
        for h in db.query(EvaluacionHallazgo)
        .filter(
            EvaluacionHallazgo.expediente_id == exp.id,
            EvaluacionHallazgo.visible_entidad.is_(True),
            EvaluacionHallazgo.opportunity_id.isnot(None),
        )
        .all()
    }
    result = []
    for _link, opp in links:
        if opp.id not in visible_hallazgo_opp_ids:
            continue
        result.append({
            "codigo": opp.codigo,
            "titulo": opp.titulo,
            "estado": opp.estado,
            "valor_potencial": float(opp.valor_potencial) if opp.valor_potencial else None,
        })
    return result


def get_trazabilidad(db: Session, expediente_id: str, organization_id: str) -> dict[str, Any]:
    from app.services import evaluacion_accion_service as acc_svc

    exp = _get_expediente(db, expediente_id, organization_id)
    vis_logs = (
        db.query(EvaluacionVisibilidadLog)
        .filter(EvaluacionVisibilidadLog.expediente_id == exp.id)
        .order_by(EvaluacionVisibilidadLog.created_at.desc())
        .all()
    )
    acciones_eventos = acc_svc.get_trazabilidad_acciones(db, expediente_id, organization_id)
    return {
        "expediente_id": exp.id,
        "correlation_id": exp.correlation_id,
        "diagnostic_id": exp.diagnostic_id,
        "cadena": {
            "organizacion": organization_id,
            "expediente": exp.id,
            "correlation_id": exp.correlation_id,
        },
        "visibilidad": [
            {
                "id": v.id,
                "objeto_tipo": v.objeto_tipo,
                "objeto_id": v.objeto_id,
                "visible_entidad": v.visible_entidad,
                "changed_by": v.changed_by,
                "fecha": v.created_at.isoformat() if v.created_at else None,
            }
            for v in vis_logs
        ],
        "hallazgos": [
            {
                "id": h.id,
                "titulo": h.titulo,
                "origen": h.origen,
                "tipo_contenido": h.tipo_contenido,
                "confianza": h.confianza,
                "visible_entidad": h.visible_entidad,
                "correlation_id": h.correlation_id,
                "fecha": h.created_at.isoformat() if h.created_at else None,
            }
            for h in db.query(EvaluacionHallazgo)
            .filter(EvaluacionHallazgo.expediente_id == exp.id)
            .order_by(EvaluacionHallazgo.created_at)
            .all()
        ],
        "acciones_externas": acciones_eventos,
    }


def get_impacto_resumen(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    vista_entidad: bool = False,
) -> dict[str, Any]:
    from app.services import evaluacion_accion_service as acc_svc

    exp = _get_expediente(db, expediente_id, organization_id)
    hallazgos = db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.expediente_id == exp.id).all()
    if vista_entidad:
        hallazgos = [h for h in hallazgos if h.visible_entidad]

    indicadores: list[dict[str, Any]] = []

    try:
        from app.services import resultados_service as res_svc

        for ind in res_svc.list_indicadores(db, organization_id, expediente_id=exp.id):
            if vista_entidad and not ind.get("visible_entidad"):
                continue
            grafico_src = {
                "valor_antes": ind["antes"],
                "valor_proyectado": ind["proyectado"],
                "valor_real": ind["real"],
                "unidad": ind["unidad"],
            }
            indicadores.append({
                "id": ind["id"],
                "nombre": ind["nombre"],
                "hallazgo": ind["nombre"],
                "antes": ind["antes"],
                "proyectado": ind["proyectado"],
                "real": ind["real"],
                "etiqueta_proyeccion": ind["proyectado"] is not None and ind["real"] is None,
                "sin_medicion_posterior": ind.get("sin_medicion_posterior", False),
                "confianza": ind["confianza"],
                "unidad": ind["unidad"],
                "fuente": ind["fuente"],
                "indicador_id": ind["id"],
                "grafico": _build_grafico_puntos(grafico_src),
            })
    except Exception:
        pass

    for ind in acc_svc.list_indicadores(db, expediente_id, organization_id, vista_entidad=vista_entidad):
        if any(i.get("indicador_id") == ind["id"] or i.get("nombre") == ind["nombre"] for i in indicadores):
            continue
        indicadores.append({
            "id": ind["id"],
            "nombre": ind["nombre"],
            "hallazgo": ind["nombre"],
            "unidad": ind.get("unidad"),
            "antes": ind.get("valor_antes"),
            "proyectado": ind.get("valor_proyectado"),
            "real": ind.get("valor_real"),
            "etiqueta_proyeccion": bool(ind.get("valor_proyectado") and not ind.get("valor_real")),
            "fuente": ind.get("fuente"),
            "grafico": _build_grafico_puntos(ind),
        })

    for h in hallazgos:
        if not h.impacto_resumen:
            continue
        if any(i.get("nombre") == h.titulo for i in indicadores):
            continue
        indicadores.append({
            "id": h.id,
            "nombre": h.titulo,
            "hallazgo": h.titulo,
            "unidad": None,
            "antes": None,
            "proyectado": h.impacto_resumen if h.tipo_contenido == "PROYECCION" else None,
            "real": h.impacto_resumen if h.tipo_contenido == "HECHO" else None,
            "etiqueta_proyeccion": h.tipo_contenido == "PROYECCION",
            "confianza": h.confianza,
            "grafico": None,
        })

    return {
        "expediente_id": exp.id,
        "valor_potencial": exp.valor_potencial if not vista_entidad else None,
        "indicadores": indicadores,
        "tiene_graficos": any(i.get("grafico") for i in indicadores),
        "nota": "PROYECTADO identifica estimaciones; REAL solo con evidencia verificada.",
        "resumen": _impacto_resumen_economico(db, exp, organization_id, vista_entidad=vista_entidad),
        "interpretacion": _impacto_interpretacion(exp, indicadores, hallazgos, vista_entidad=vista_entidad),
    }


def _impacto_resumen_economico(
    db: Session,
    exp: EvaluacionExpediente,
    organization_id: str,
    *,
    vista_entidad: bool = False,
) -> dict[str, Any]:
    from app.services.demo_economico_horizonte import expediente_economic_resumen

    return expediente_economic_resumen(db, organization_id, exp.id, vista_entidad=vista_entidad)


_INSUFICIENTE_INTERPRETACION = "Información insuficiente para determinar esta conclusión."


def _impacto_interpretacion(
    exp: EvaluacionExpediente,
    indicadores: list[dict[str, Any]],
    hallazgos: list[EvaluacionHallazgo],
    *,
    vista_entidad: bool = False,
) -> dict[str, Any]:
    is_demo = _is_demo_expediente(exp)
    banner = "DEMO — DATOS SIMULADOS" if is_demo else None
    titulos = [h.titulo for h in hallazgos if h.titulo]

    def _field(*candidates: str | None) -> str:
        for c in candidates:
            if c and str(c).strip():
                return str(c).strip()
        return _INSUFICIENTE_INTERPRETACION

    presentacion = f"/demo/presentacion/{exp.id}" if is_demo else f"/presentacion/{exp.id}"
    acciones = [
        {"label": "Abrir cabina", "ruta": f"/evaluaciones/{exp.id}"},
        {"label": "Oportunidades", "ruta": "/oportunidades"},
        {"label": "Presentar", "ruta": presentacion},
    ]

    if is_demo:
        from app.demo_comercial_constants import DEMO_NECESIDAD_RESUMEN

        que_demo = "; ".join(titulos[:3]) if titulos else (exp.necesidad or DEMO_NECESIDAD_RESUMEN.split(".")[0])
        return {
            "banner": banner,
            "que_ocurrio": f"[DEMO] {que_demo}",
            "por_que": _field(exp.area_proceso, "Escenario simulado de salud/facturación para demostración comercial."),
            "que_significa": _field(exp.objetivo, "Ilustra oportunidades de automatización — no es verificación real."),
            "requiere_atencion": _field(
                "Completar documentación demo y decidir piloto" if exp.porcentaje_informacion < 100 else None,
                "Revisar decisión de piloto en escenario demo.",
            ),
            "oportunidad": _field(
                titulos[0] if titulos else None,
                "Automatización de procesos críticos del escenario demo.",
            ),
            "valor": "Ver pestaña Valor — cifras etiquetadas; en demo son simulaciones, no verificación real.",
            "recomendacion": _field(
                exp.objetivo,
                "Capacitar equipo, desplegar reglas IA y medir antes/proyectado/real trimestral (demo).",
            ),
            "acciones": acciones,
            "indicadores_clave": len(indicadores),
            "vista_entidad": vista_entidad,
        }

    if not titulos and not indicadores and not (exp.necesidad or "").strip():
        return {
            "banner": banner,
            "que_ocurrio": _INSUFICIENTE_INTERPRETACION,
            "por_que": _INSUFICIENTE_INTERPRETACION,
            "que_significa": _INSUFICIENTE_INTERPRETACION,
            "requiere_atencion": _INSUFICIENTE_INTERPRETACION,
            "oportunidad": _INSUFICIENTE_INTERPRETACION,
            "valor": _INSUFICIENTE_INTERPRETACION,
            "recomendacion": _INSUFICIENTE_INTERPRETACION,
            "acciones": acciones,
            "indicadores_clave": 0,
            "vista_entidad": vista_entidad,
        }

    hechos = [h for h in hallazgos if h.tipo_contenido == "HECHO"]
    inferencias = [h for h in hallazgos if h.tipo_contenido == "INFERENCIA"]
    recomendaciones = [h for h in hallazgos if h.tipo_contenido == "RECOMENDACION"]
    impactos = [h.impacto_resumen for h in hallazgos if h.impacto_resumen and str(h.impacto_resumen).strip()]
    oportunidad_hallazgos = [h for h in hallazgos if h.opportunity_id or h.tipo_contenido == "RECOMENDACION"]

    if hechos:
        que_ocurrio = "; ".join(h.titulo for h in hechos[:3] if h.titulo)
    elif (exp.necesidad or "").strip():
        que_ocurrio = str(exp.necesidad).strip()
    else:
        que_ocurrio = _INSUFICIENTE_INTERPRETACION

    if inferencias:
        inf = inferencias[0]
        por_que = (inf.descripcion or inf.evidencia or inf.titulo or "").strip() or _INSUFICIENTE_INTERPRETACION
    else:
        por_que = _INSUFICIENTE_INTERPRETACION

    if impactos:
        que_significa = str(impactos[0]).strip()
    else:
        que_significa = _INSUFICIENTE_INTERPRETACION

    if oportunidad_hallazgos:
        oportunidad = oportunidad_hallazgos[0].titulo
    else:
        oportunidad = _INSUFICIENTE_INTERPRETACION

    if (exp.porcentaje_informacion or 0) < 80:
        requiere_atencion = (
            f"Completar información del expediente ({exp.porcentaje_informacion or 0}% registrado)."
        )
    else:
        requiere_atencion = _INSUFICIENTE_INTERPRETACION

    if recomendaciones:
        rec = recomendaciones[0]
        recomendacion = (rec.descripcion or rec.titulo or "").strip() or _INSUFICIENTE_INTERPRETACION
    else:
        recomendacion = _INSUFICIENTE_INTERPRETACION

    return {
        "banner": banner,
        "que_ocurrio": que_ocurrio,
        "por_que": por_que,
        "que_significa": que_significa,
        "requiere_atencion": requiere_atencion,
        "oportunidad": oportunidad,
        "valor": "Ver pestaña Valor — cifras etiquetadas según naturaleza (verificado/estimado/potencial).",
        "recomendacion": recomendacion,
        "acciones": acciones,
        "indicadores_clave": len(indicadores),
        "vista_entidad": vista_entidad,
    }


def _build_grafico_puntos(ind: dict[str, Any]) -> dict[str, Any] | None:
    mapping = [
        ("antes", ind.get("valor_antes"), False),
        ("proyectado", ind.get("valor_proyectado"), True),
        ("real", ind.get("valor_real"), False),
    ]
    puntos = []
    for serie, val, es_proy in mapping:
        if val is not None and str(val).strip():
            try:
                numerico = float(str(val).replace(",", ".").replace("%", ""))
            except ValueError:
                numerico = None
            puntos.append({"serie": serie, "valor": val, "numerico": numerico, "es_proyeccion": es_proy})
    if len(puntos) < 2:
        return None
    return {"puntos": puntos, "unidad": ind.get("unidad")}


def vincular_oportunidad(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    opportunity_id: str,
    hallazgo_id: str | None = None,
    user_id: str,
) -> EvaluacionOportunidadLink:
    exp = _get_expediente(db, expediente_id, organization_id)
    opp = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id, Opportunity.organization_id == organization_id)
        .first()
    )
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    existing = (
        db.query(EvaluacionOportunidadLink)
        .filter(
            EvaluacionOportunidadLink.expediente_id == exp.id,
            EvaluacionOportunidadLink.opportunity_id == opportunity_id,
        )
        .first()
    )
    if existing:
        return existing
    link = EvaluacionOportunidadLink(
        organization_id=organization_id,
        expediente_id=exp.id,
        opportunity_id=opportunity_id,
        hallazgo_id=hallazgo_id,
        rol="VINCULADA",
    )
    db.add(link)
    if hallazgo_id:
        h = db.query(EvaluacionHallazgo).filter(EvaluacionHallazgo.id == hallazgo_id).first()
        if h:
            h.opportunity_id = opportunity_id
    write_audit(
        db,
        organization_id=organization_id,
        user_id=user_id,
        action="evaluacion.link_opportunity",
        detail=json.dumps({"opportunity_id": opportunity_id, "resource_id": exp.id}),
        commit=False,
    )
    return link


def crear_oportunidad_desde_hallazgo(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    hallazgo_id: str,
    user_id: str,
    dominio: str = "operaciones",
) -> dict[str, Any]:
    exp = _get_expediente(db, expediente_id, organization_id)
    h = (
        db.query(EvaluacionHallazgo)
        .filter(
            EvaluacionHallazgo.id == hallazgo_id,
            EvaluacionHallazgo.expediente_id == exp.id,
        )
        .first()
    )
    if not h:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    payload = {
        "titulo": h.titulo[:200],
        "descripcion": h.descripcion or h.titulo,
        "tipo_oportunidad": "EVALUACION",
        "confianza": {"ALTA": 0.85, "MEDIA": 0.65, "BAJA": 0.4}.get(h.confianza, 0.5),
        "impacto_estimado": 0,
        "valor_potencial": 0,
        "source_reference": f"eval-{exp.codigo}-{h.id[:8]}",
        "evidencia": h.evidencia,
        "es_problema_original": h.es_problema_original,
    }
    result = opp_svc.run_proactive_pipeline(
        db,
        organization_id=organization_id,
        tipo="evaluacion",
        dominio=dominio,
        evento="evaluacion_expediente",
        payload=payload,
        origen="evaluacion_service",
        user_id=user_id,
    )
    opp_id = result.get("opportunity_id")
    if opp_id:
        vincular_oportunidad(
            db, exp.id, organization_id,
            opportunity_id=opp_id, hallazgo_id=h.id, user_id=user_id,
        )
        h.opportunity_id = opp_id
    return {"hallazgo_id": h.id, "opportunity_id": opp_id, "pipeline": result}


def _has_usable_llm(db: Session, organization_id: str) -> bool:
    rows = (
        db.query(LlmProviderConfig)
        .filter(
            LlmProviderConfig.organization_id == organization_id,
            LlmProviderConfig.is_enabled.is_(True),
        )
        .all()
    )
    for row in rows:
        if not is_executable_llm_provider(row.provider_type):
            continue
        if secret_configured(row.secret_ref) or row.provider_type.lower() == "ollama":
            return True
    return False


def _is_demo_expediente(exp: EvaluacionExpediente) -> bool:
    from app.demo_comercial_constants import DEMO_CORRELATION_PREFIX, DEMO_ENTIDAD_PREFIX

    if exp.correlation_id and exp.correlation_id.startswith(DEMO_CORRELATION_PREFIX):
        return True
    return exp.entidad_nombre.startswith(DEMO_ENTIDAD_PREFIX)


def _demo_ask_response(
    db: Session,
    exp: EvaluacionExpediente,
    organization_id: str,
    *,
    mensaje: str,
    accion: str | None,
    base: dict[str, Any],
) -> dict[str, Any] | None:
    """Respuestas demo coherentes sin LLM — contexto Horizonte."""
    if not _is_demo_expediente(exp):
        return None

    from app.services import economic_motor_service as motor_svc

    q = (mensaje or accion or "").lower()
    valores = motor_svc.sum_values_by_nature(db, organization_id)
    top_opp = (
        db.query(Opportunity)
        .join(EvaluacionOportunidadLink, EvaluacionOportunidadLink.opportunity_id == Opportunity.id)
        .filter(
            EvaluacionOportunidadLink.expediente_id == exp.id,
            EvaluacionOportunidadLink.organization_id == organization_id,
        )
        .order_by(Opportunity.valor_potencial.desc().nullslast())
        .first()
    )

    if any(k in q for k in ("falta", "informacion_faltante", "qué falta", "que falta")):
        pend = base["contexto_expediente"].get("informacion_pendiente") or []
        return {
            **base,
            "modo_respuesta": "demo_controlado",
            "proveedor": "plantillas_demo_horizonte",
            "estado": "respuesta_demo",
            "mensaje": (
                f"[DEMO] En {exp.entidad_nombre} falta completar: "
                f"{', '.join(pend[:5]) if pend else 'documentación de soporte y validación de codificación'}."
            ),
        }

    if any(k in q for k in ("encontró", "encontro", "hallazgo", "detectó", "detecto")):
        hallazgos = [
            h.titulo
            for h in db.query(EvaluacionHallazgo)
            .filter(EvaluacionHallazgo.expediente_id == exp.id, EvaluacionHallazgo.visible_entidad.is_(True))
            .limit(4)
            .all()
        ]
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": f"[DEMO] EIAAX identificó: {'; '.join(hallazgos) or 'glosas y reprocesos manuales'}.",
        }

    if "oportunidad" in q or accion == "identificar_oportunidades":
        titulo = top_opp.titulo if top_opp else "Automatización facturación"
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": f"[DEMO] Oportunidad prioritaria: {titulo} (eficiencia/ahorro estimado).",
        }

    if any(k in q for k in ("valor", "cuánto", "cuanto", "valem", "roi")):
        est = valores.get("valor_estimado")
        pot = valores.get("valor_potencial")
        return {
            **base,
            "modo_respuesta": "demo_controlado",
            "proveedor": "plantillas_demo_horizonte",
            "estado": "respuesta_demo",
            "mensaje": (
                f"[DEMO — ESTIMADO/PROYECTADO] Valor estimado org: {est or '—'} · "
                f"Potencial: {pot or '—'}. No equivale a valor verificado."
            ),
        }

    if any(k in q for k in ("decidir", "decisión", "decision", "aprob")):
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": "[DEMO] Decisión pendiente: aprobar piloto automatización codificación y publicar hallazgos a la empresa.",
        }

    if any(k in q for k in ("presentar", "presentación", "presentacion", "reunión")):
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": "[DEMO] Use Presentar en reunión con audiencia Gerencia/Dirección — sin costos internos ni margen.",
        }

    if any(k in q for k in ("empresa", "verá", "vera", "cliente", "vista")):
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": "[DEMO] La empresa verá hallazgos autorizados, indicadores antes/proyectado/real y recomendaciones — sin economía privada.",
        }

    if any(k in q for k in ("resultado", "indicador", "medición", "medicion")):
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": "[DEMO] Resultados: días respuesta glosa 16→9.5 (real piloto); recuperación cartera en mejora. Proyectado ≠ real.",
        }

    if any(k in q for k in ("siguiente", "acción", "accion", "siguiente_analisis")):
        return {
            **base,
            "estado": "respuesta_demo",
            "mensaje": "[DEMO] Siguiente acción: completar documentación faltante y decidir aprobación del piloto Empleado IA.",
        }

    return None


def ask_eiaax(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    user_id: str,
    mensaje: str,
    accion: str | None = None,
) -> dict[str, Any]:
    from app.services.evaluacion_intent_service import INTENCION_DESCRIPCIONES, classify_intent
    from app.services.piiax_bridge_service import get_piiax_status

    exp = _get_expediente(db, expediente_id, organization_id)
    pendientes = [
        i.etiqueta
        for i in db.query(EvaluacionInformacionItem)
        .filter(
            EvaluacionInformacionItem.expediente_id == exp.id,
            EvaluacionInformacionItem.estado.in_(("PENDIENTE", "INCOMPLETO")),
        )
        .all()
    ]
    tiene_llm = _has_usable_llm(db, organization_id)
    piiax = get_piiax_status(db, organization_id)

    intencion = classify_intent(
        mensaje,
        accion_sugerida=accion,
        porcentaje_informacion=exp.porcentaje_informacion,
        tiene_proveedor_llm=tiene_llm,
        piiax_disponible=piiax["disponible"],
        info_pendiente_count=len(pendientes),
    )

    base = {
        "intencion": intencion,
        "piiax": piiax,
        "contexto_expediente": {
            "codigo": exp.codigo,
            "entidad": exp.entidad_nombre,
            "estado": exp.estado,
            "confianza_global": exp.confianza_global,
            "informacion_pendiente": pendientes[:8],
        },
    }

    demo_resp = _demo_ask_response(
        db, exp, organization_id, mensaje=mensaje, accion=accion, base=base,
    )
    if demo_resp:
        demo_resp.setdefault("modo_respuesta", "demo_controlado")
        demo_resp.setdefault("proveedor", "plantillas_demo_horizonte")
        demo_resp.setdefault("llm_real", False)
        return demo_resp

    codigo = intencion["intencion"]

    if codigo == "A":
        return {
            **base,
            "modo_respuesta": "local_heuristica",
            "proveedor": "evaluacion_intent_service",
            "llm_real": False,
            "estado": "respuesta_local",
            "mensaje": (
                f"Con la información actual ({exp.porcentaje_informacion}% completada), "
                f"puede revisar el expediente {exp.codigo}: problema «{exp.necesidad or 'sin definir'}», "
                f"objetivo «{exp.objetivo or 'sin definir'}»."
            ),
            "respuesta": None,
        }

    if codigo == "B":
        return {
            **base,
            "estado": "informacion_adicional",
            "mensaje": "Se requiere completar información en la pestaña Información antes de profundizar.",
            "respuesta": None,
        }

    if codigo in ("D", "E", "F"):
        return {
            **base,
            "estado": "requiere_capacidad_externa",
            "mensaje": (
                f"{INTENCION_DESCRIPCIONES[codigo]} "
                "Puede crear una solicitud de acción externa desde el hallazgo; no se ejecutará automáticamente."
            ),
            "capacidad_sugerida": intencion.get("capacidad_sugerida"),
            "requiere_aprobacion": intencion.get("requiere_aprobacion"),
            "respuesta": None,
        }

    if codigo == "G":
        return {
            **base,
            "estado": "oportunidad_sugerida",
            "mensaje": (
                f"{INTENCION_DESCRIPCIONES['G']} "
                "Puede crear o vincular una oportunidad desde la pestaña Oportunidades o desde un hallazgo."
            ),
            "respuesta": None,
        }

    if codigo == "H":
        return {
            **base,
            "estado": "tarea_seguimiento",
            "mensaje": (
                f"{INTENCION_DESCRIPCIONES['H']} "
                "La asignación operativa se integrará con el Centro de Operaciones cuando esté disponible."
            ),
            "respuesta": None,
        }

    if codigo == "C" and not tiene_llm:
        return {
            **base,
            "estado": "sin_proveedor",
            "mensaje": (
                "Se requiere análisis IA pero no hay proveedor configurado. "
                "Configure un proveedor en Administración → Proveedores IA."
            ),
            "respuesta": None,
        }

    if codigo == "C":
        prompt = mensaje
        if accion:
            prompts = {
                "profundizar_hallazgo": f"Profundiza el hallazgo relacionado con: {mensaje}",
                "informacion_faltante": "¿Qué información falta en este expediente y por qué?",
                "buscar_causas": f"Busca posibles causas raíz para: {mensaje}",
                "cuantificar_impacto": f"Cuantifica el impacto potencial de: {mensaje}",
                "identificar_oportunidades": "Identifica oportunidades adicionales a partir del expediente.",
                "explicar_indicador": f"Explica este indicador en contexto del expediente: {mensaje}",
                "siguiente_analisis": "¿Qué deberíamos analizar después en este expediente?",
            }
            prompt = prompts.get(accion, mensaje)
        result = route_task(
            db,
            organization_id=organization_id,
            user_id=user_id,
            request=prompt,
            context={
                "expediente_id": exp.id,
                "expediente_codigo": exp.codigo,
                "intencion": codigo,
            },
            auto_execute=False,
        )
        return {
            **base,
            "modo_respuesta": "llm_real",
            "proveedor": "route_task",
            "llm_real": True,
            "estado": "ok",
            "respuesta": result,
        }

    return {**base, "modo_respuesta": "local_heuristica", "llm_real": False, "estado": "ok", "respuesta": None}


def get_siguiente_accion(
    db: Session,
    expediente_id: str,
    organization_id: str,
    *,
    permisos: set[str] | None = None,
    persistir: bool = True,
) -> dict[str, Any]:
    from app.services.evaluacion_siguiente_accion_service import (
        compute_siguiente_accion,
        persistir_siguiente_accion,
    )

    exp = _get_expediente(db, expediente_id, organization_id)
    resultado = compute_siguiente_accion(db, exp, permisos=permisos or set())
    if persistir:
        persistir_siguiente_accion(db, exp, resultado)
    return resultado
