"""Servicio — Flujo comercial V1 EIAAX (1730).

Orquesta expediente (dossier), oportunidades, presentación ejecutiva,
propuesta, instrumentos contractuales y garantías reutilizando módulos existentes.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.commercial_models import CommercialProposal
from app.evaluacion_models import (
    EvaluacionExpediente,
    EvaluacionHallazgo,
    EvaluacionInformacionItem,
    EvaluacionOportunidadLink,
)
from app.flujo_comercial_enums import (
    ClasificacionValorOportunidad,
    EstadoInstrumentoContractual,
    EstadoPresentacionEjecutiva,
    OrigenOportunidadComercial,
    SuficienciaEvaluacion,
    TipoCompromisoGarantia,
    TipoInstrumentoContractual,
)
from app.flujo_comercial_models import (
    ComercialCompromisoGarantia,
    ComercialInstrumentoContractual,
    ComercialPresentacionEjecutiva,
)
from app.models import User
from app.negocio_enums import PerspectivaPropuesta
from app.negocio_models import NegocioProposalExtension
from app.opportunity_models import Opportunity
from app.services import evaluacion_service as eval_svc
from app.services import negocio_service as neg_svc

POTENCIAL_NOTE = "POTENCIAL no cuenta como valor realizado ni en ROI/payback realizado."

# Catálogo contextual por sector/problema — no universal
_INFO_CATALOGO_CONTEXTUAL: list[dict[str, Any]] = [
    {
        "campo": "salud_facturacion",
        "etiqueta": "Facturación y radicación",
        "explicacion": "Volúmenes, tiempos y rechazos en facturación.",
        "por_que": "Contextualiza oportunidades de mejora en ciclo de ingresos.",
        "impacto_precision": "Sin datos de facturación, el impacto es estimado.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
        "sectores": {"salud", "ips", "hospital", "clinica"},
        "problemas": {"facturacion", "auditoria", "glosa", "radicacion", "cartera"},
    },
    {
        "campo": "salud_glosas",
        "etiqueta": "Glosas y devoluciones",
        "explicacion": "Tipos de glosa, montos, causales y tiempos de respuesta.",
        "por_que": "Permite cuantificar recuperación y automatización.",
        "impacto_precision": "Sin glosas, no se dimensiona recuperación real.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
        "sectores": {"salud", "ips", "hospital"},
        "problemas": {"glosa", "devolucion", "facturacion", "auditoria"},
    },
    {
        "campo": "salud_pagos",
        "etiqueta": "Pagos y tiempos de recaudo",
        "explicacion": "Días de pago, cartera vencida, acuerdos de pago.",
        "por_que": "Relaciona eficiencia operativa con flujo de caja.",
        "impacto_precision": "Mejora proyección de valor verificable.",
        "niveles": {"PROFUNDA"},
        "obligatorio": False,
        "sectores": {"salud", "ips"},
        "problemas": {"pago", "cartera", "recaudo", "facturacion"},
    },
    {
        "campo": "finanzas_cartera",
        "etiqueta": "Cartera y morosidad",
        "explicacion": "Días de mora, provisiones, gestión de cobro.",
        "por_que": "Base para oportunidades de recuperación.",
        "impacto_precision": "Sin cartera, el valor queda en POTENCIAL.",
        "niveles": {"DIAGNOSTICA", "PROFUNDA"},
        "obligatorio": True,
        "sectores": {"finanzas", "banca", "seguros"},
        "problemas": {"cartera", "mora", "cobranza", "recuperacion"},
    },
]

_INSTRUMENTO_PLANTILLAS: dict[str, str] = {
    TipoInstrumentoContractual.NDA: "Acuerdo de confidencialidad para intercambio de información pre-comercial.",
    TipoInstrumentoContractual.AUTORIZACION_EVAL: "Autorización y términos para evaluación/diagnóstico.",
    TipoInstrumentoContractual.TRATAMIENTO_DATOS: "Tratamiento de datos personales y sensibles cuando aplique.",
    TipoInstrumentoContractual.DIAGNOSTICO: "Alcance y entregables del servicio de diagnóstico.",
    TipoInstrumentoContractual.IMPLEMENTACION: "Alcance de implementación, fases y criterios de aceptación.",
    TipoInstrumentoContractual.SERVICIO_EIAAX: "Términos del servicio EIAAX y responsabilidades.",
    TipoInstrumentoContractual.EMPLEADO_IA: "Definición del Empleado IA contratado y límites de uso.",
    TipoInstrumentoContractual.CONSUMO_IA: "Consumo incluido, proveedor IA y sobrecostos.",
    TipoInstrumentoContractual.INTEGRACION: "Integraciones técnicas y dependencias del cliente.",
    TipoInstrumentoContractual.SLA: "Niveles de servicio y tiempos de respuesta acordados.",
    TipoInstrumentoContractual.RESULTADOS: "Atribución de resultados y evidencia de medición.",
    TipoInstrumentoContractual.VARIABLE_EXITO: "Componente variable vinculado a resultados compartidos.",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _parse(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _normalize_tokens(*parts: str | None) -> set[str]:
    tokens: set[str] = set()
    for p in parts:
        if not p:
            continue
        for t in re.split(r"[\s,/\-_]+", p.lower()):
            if len(t) >= 3:
                tokens.add(t)
    return tokens


def resolve_catalogo_contextual(exp: EvaluacionExpediente) -> list[dict[str, Any]]:
    """Campos adicionales según sector, área y problema — no catálogo universal."""
    sector_tokens = _normalize_tokens(exp.sector, exp.area_proceso)
    problema_tokens = _normalize_tokens(exp.necesidad, exp.objetivo, exp.area_proceso, exp.titulo)
    result: list[dict[str, Any]] = []
    for spec in _INFO_CATALOGO_CONTEXTUAL:
        if exp.nivel not in spec["niveles"]:
            continue
        sectores = spec.get("sectores") or set()
        problemas = spec.get("problemas") or set()
        sector_match = not sectores or bool(sector_tokens & sectores)
        problema_match = not problemas or bool(problema_tokens & problemas)
        if sector_match and problema_match:
            result.append(spec)
    return result


def merge_catalogo_aplicable(exp: EvaluacionExpediente) -> list[dict[str, Any]]:
    base = [c for c in eval_svc._INFO_CATALOGO if exp.nivel in c["niveles"]]
    contextual = resolve_catalogo_contextual(exp)
    seen = {c["campo"] for c in base}
    merged = list(base)
    for c in contextual:
        if c["campo"] not in seen:
            merged.append(c)
            seen.add(c["campo"])
    return merged


def sync_informacion_contextual(db: Session, exp: EvaluacionExpediente, *, user_id: str | None = None) -> list[EvaluacionInformacionItem]:
    """Extiende sync adaptativo con campos sectoriales."""
    items = eval_svc.sync_informacion_adaptativa(db, exp, user_id=user_id)
    applicable = resolve_catalogo_contextual(exp)
    existing = {i.campo: i for i in items}
    for orden_offset, spec in enumerate(applicable):
        if spec["campo"] in existing:
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
            orden=len(items) + orden_offset,
            estado="PENDIENTE",
        )
        db.add(item)
        items.append(item)
    db.flush()
    return items


def evaluar_suficiencia(exp: EvaluacionExpediente, items: list[EvaluacionInformacionItem]) -> dict[str, Any]:
    obligatorios = [i for i in items if i.obligatorio]
    recibidos = [i for i in obligatorios if i.estado == "RECIBIDO" and i.respuesta]
    pct = int(round(100 * len(recibidos) / len(obligatorios))) if obligatorios else 100
    if pct >= 75:
        nivel = SuficienciaEvaluacion.SUFICIENTE
    elif pct >= 45:
        nivel = SuficienciaEvaluacion.PARCIAL
    else:
        nivel = SuficienciaEvaluacion.INSUFICIENTE
    return {
        "suficiencia": nivel,
        "porcentaje": pct,
        "obligatorios": len(obligatorios),
        "recibidos": len(recibidos),
        "puede_proponer": nivel != SuficienciaEvaluacion.INSUFICIENTE,
        "catalogo_contextual": len(resolve_catalogo_contextual(exp)),
    }


def importar_inteligencia_externa(
    db: Session,
    user: User,
    org_id: str,
    evaluacion_id: str,
    *,
    limite: int = 5,
) -> list[dict[str, Any]]:
    """Importa señales externas extendidas como hallazgos del expediente."""
    from app.external_models import ExternalSignalExtension
    from app.opportunity_models import ProactiveSignal

    exp = eval_svc._get_expediente(db, evaluacion_id, org_id)
    imported: list[dict[str, Any]] = []
    extensions = (
        db.query(ExternalSignalExtension, ProactiveSignal)
        .join(ProactiveSignal, ProactiveSignal.id == ExternalSignalExtension.signal_id)
        .filter(ExternalSignalExtension.organization_id == org_id)
        .order_by(ExternalSignalExtension.created_at.desc())
        .limit(limite)
        .all()
    )
    for ext, sig in extensions:
        titulo = ext.hecho_observado or sig.evento or "Señal externa"
        hallazgo = EvaluacionHallazgo(
            organization_id=org_id,
            expediente_id=exp.id,
            titulo=f"[Externa] {titulo[:200]}",
            descripcion=ext.interpretacion or ext.hipotesis or ext.oportunidad_propuesta,
            tipo_contenido="INFERENCIA",
            confianza="MEDIA",
            origen="inteligencia_externa",
            evidencia=sig.evidencia_resumen,
            visible_entidad=False,
            created_by=user.id,
        )
        db.add(hallazgo)
        db.flush()
        imported.append({"hallazgo_id": hallazgo.id, "origen": "inteligencia_externa", "titulo": hallazgo.titulo})
    write_audit(
        db,
        action="flujo_comercial.inteligencia_importada",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"evaluacion_id": evaluacion_id, "count": len(imported)}),
        commit=False,
    )
    return imported


def listar_oportunidades_expediente(db: Session, org_id: str, evaluacion_id: str) -> list[dict[str, Any]]:
    links = (
        db.query(EvaluacionOportunidadLink, Opportunity)
        .join(Opportunity, Opportunity.id == EvaluacionOportunidadLink.opportunity_id)
        .filter(
            EvaluacionOportunidadLink.expediente_id == evaluacion_id,
            EvaluacionOportunidadLink.organization_id == org_id,
        )
        .all()
    )
    result = []
    for link, opp in links:
        clasif = opp.valor_potencial_certidumbre or ClasificacionValorOportunidad.ESTIMADO
        result.append({
            "id": opp.id,
            "codigo": opp.codigo,
            "titulo": opp.titulo,
            "tipo": opp.tipo,
            "dominio": opp.dominio,
            "estado": opp.estado,
            "origen_comercial": getattr(opp, "origen_comercial", None) or OrigenOportunidadComercial.SOLICITADA,
            "presentar_cliente": bool(getattr(opp, "presentar_cliente", False)),
            "clasificacion_valor": clasif,
            "valor_potencial": float(opp.valor_potencial) if opp.valor_potencial else None,
            "es_valor_realizado": clasif in (ClasificacionValorOportunidad.VERIFICADO, ClasificacionValorOportunidad.ESTIMADO),
            "nota_potencial": POTENCIAL_NOTE if clasif == ClasificacionValorOportunidad.POTENCIAL else None,
            "rol_vinculo": link.rol,
        })
    return result


def seleccionar_oportunidades_presentacion(
    db: Session,
    user: User,
    org_id: str,
    evaluacion_id: str,
    opportunity_ids: list[str],
    *,
    presentar: bool = True,
) -> list[dict[str, Any]]:
    updated = []
    for oid in opportunity_ids:
        opp = db.query(Opportunity).filter(Opportunity.id == oid, Opportunity.organization_id == org_id).first()
        if not opp:
            raise HTTPException(status_code=404, detail=f"Oportunidad {oid} no encontrada")
        opp.presentar_cliente = presentar
        updated.append({"id": opp.id, "presentar_cliente": opp.presentar_cliente})
    db.flush()
    write_audit(
        db,
        action="flujo_comercial.oportunidades_seleccionadas",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"evaluacion_id": evaluacion_id, "ids": opportunity_ids}),
        commit=False,
    )
    return updated


def crear_presentacion_ejecutiva(
    db: Session,
    user: User,
    org_id: str,
    evaluacion_id: str,
    data: dict[str, Any],
) -> ComercialPresentacionEjecutiva:
    exp = eval_svc._get_expediente(db, evaluacion_id, org_id)
    hallazgos_ids = data.get("hallazgos_ids") or []
    oportunidades_ids = data.get("oportunidades_ids") or []
    if not oportunidades_ids:
        oportunidades_ids = [
            o["id"]
            for o in listar_oportunidades_expediente(db, org_id, evaluacion_id)
            if o.get("presentar_cliente")
        ]
    hallazgos = (
        db.query(EvaluacionHallazgo)
        .filter(
            EvaluacionHallazgo.expediente_id == evaluacion_id,
            EvaluacionHallazgo.organization_id == org_id,
        )
        .all()
    )
    if not hallazgos_ids:
        hallazgos_ids = [h.id for h in hallazgos if h.visible_entidad or h.es_problema_original]
    opps = db.query(Opportunity).filter(Opportunity.id.in_(oportunidades_ids)).all() if oportunidades_ids else []
    valor_verificado = sum(
        float(o.valor_potencial or 0)
        for o in opps
        if (o.valor_potencial_certidumbre or "") in ("VERIFICADO", "ESTIMADO")
    )
    valor_potencial = sum(
        float(o.valor_potencial or 0)
        for o in opps
        if (o.valor_potencial_certidumbre or "") == "POTENCIAL"
    )
    secciones = {
        "que_encontramos": [h.titulo for h in hallazgos if h.id in hallazgos_ids],
        "por_que_importa": exp.objetivo or exp.necesidad,
        "valor_verificado_estimado": valor_verificado or None,
        "valor_potencial": valor_potencial or None,
        "nota_potencial": POTENCIAL_NOTE,
        "solucion_alto_nivel": data.get("solucion") or "Solución EIAAX con Empleados IA y automatización",
        "alcance": data.get("alcance") or exp.area_proceso,
        "tiempo": data.get("tiempo"),
        "inversion": data.get("inversion"),
        "dependencias": data.get("dependencias") or [],
        "supuestos": data.get("supuestos") or [],
        "siguiente_paso": data.get("siguiente_paso") or "Aprobación interna y presentación al cliente",
    }
    row = ComercialPresentacionEjecutiva(
        organization_id=org_id,
        evaluacion_id=evaluacion_id,
        titulo=data.get("titulo") or f"Presentación — {exp.titulo}",
        estado=EstadoPresentacionEjecutiva.INTERNA,
        hallazgos_ids_json=_json(hallazgos_ids),
        oportunidades_ids_json=_json(oportunidades_ids),
        secciones_json=_json(secciones),
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    return row


def presentacion_to_dict(row: ComercialPresentacionEjecutiva) -> dict[str, Any]:
    return {
        "id": row.id,
        "evaluacion_id": row.evaluacion_id,
        "proposal_id": row.proposal_id,
        "titulo": row.titulo,
        "estado": row.estado,
        "hallazgos_ids": _parse(row.hallazgos_ids_json) or [],
        "oportunidades_ids": _parse(row.oportunidades_ids_json) or [],
        "secciones": _parse(row.secciones_json) or {},
    }


def generar_propuesta_desde_dossier(
    db: Session,
    user: User,
    org_id: str,
    evaluacion_id: str,
    *,
    opportunity_id: str | None = None,
    titulo: str | None = None,
    exigir_suficiencia: bool = True,
    presentacion_id: str | None = None,
) -> dict[str, Any]:
    """Genera propuesta desde dossier con hallazgos y presentación — sin economía interna al cliente."""
    exp = eval_svc._get_expediente(db, evaluacion_id, org_id)
    items = db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.expediente_id == evaluacion_id).all()
    suf = evaluar_suficiencia(exp, items)
    if exigir_suficiencia and not suf["puede_proponer"]:
        raise HTTPException(status_code=422, detail="Información insuficiente para generar propuesta")

    pres = None
    if presentacion_id:
        pres = db.query(ComercialPresentacionEjecutiva).filter(
            ComercialPresentacionEjecutiva.id == presentacion_id,
            ComercialPresentacionEjecutiva.organization_id == org_id,
        ).first()
    if not pres:
        pres = crear_presentacion_ejecutiva(db, user, org_id, evaluacion_id, {"titulo": titulo})

    if not opportunity_id:
        links = listar_oportunidades_expediente(db, org_id, evaluacion_id)
        selected = [l for l in links if l.get("presentar_cliente")]
        opportunity_id = (selected[0]["id"] if selected else None) or (links[0]["id"] if links else None)

    detail = neg_svc.create_proposal_from_expediente(
        db, user, org_id,
        evaluacion_id=evaluacion_id,
        opportunity_id=opportunity_id,
        titulo=titulo or pres.titulo,
    )
    proposal_id = detail["id"] if "id" in detail else detail.get("proposal", {}).get("id")
    if not proposal_id:
        raise HTTPException(status_code=500, detail="No se pudo crear propuesta")

    ext = db.query(NegocioProposalExtension).filter(NegocioProposalExtension.proposal_id == proposal_id).first()
    if ext:
        secciones = _parse(pres.secciones_json) or {}
        perspectives = _parse(ext.perspectivas_json) or neg_svc._default_perspectives(
            db.query(CommercialProposal).filter(CommercialProposal.id == proposal_id).first(),
            ext,
        )
        perspectives.setdefault(PerspectivaPropuesta.GERENCIA, {})
        perspectives[PerspectivaPropuesta.GERENCIA]["situacion"] = secciones.get("que_encontramos")
        perspectives[PerspectivaPropuesta.GERENCIA]["oportunidad"] = secciones.get("por_que_importa")
        perspectives.setdefault(PerspectivaPropuesta.OPERACIONES, {})
        perspectives[PerspectivaPropuesta.OPERACIONES]["solucion"] = secciones.get("solucion_alto_nivel")
        perspectives[PerspectivaPropuesta.OPERACIONES]["implementacion"] = secciones.get("alcance")
        ext.perspectivas_json = _json(perspectives)
        client_doc = neg_svc._build_client_document(
            db.query(CommercialProposal).filter(CommercialProposal.id == proposal_id).first(),
            ext,
            perspectives,
        )
        client_doc.update({
            "que_encontramos": secciones.get("que_encontramos"),
            "por_que_importa": secciones.get("por_que_importa"),
            "valor_potencial": secciones.get("valor_potencial"),
            "valor_verificado_estimado": secciones.get("valor_verificado_estimado"),
            "dependencias": secciones.get("dependencias"),
            "siguiente_paso": secciones.get("siguiente_paso"),
            "nota_potencial": POTENCIAL_NOTE,
            "economia_privada_incluida": False,
        })
        ext.documento_cliente_json = _json(client_doc)
        pres.proposal_id = proposal_id
        pres.estado = EstadoPresentacionEjecutiva.PRESENTADA
        db.flush()

    write_audit(
        db,
        action="flujo_comercial.propuesta_desde_dossier",
        organization_id=org_id,
        user_id=user.id,
        detail=_json({"evaluacion_id": evaluacion_id, "proposal_id": proposal_id}),
        commit=False,
    )
    return {
        "proposal_id": proposal_id,
        "presentacion_id": pres.id,
        "suficiencia": suf,
        "detail": neg_svc.get_proposal_negocio(db, org_id, proposal_id, include_internal=False),
    }


def listar_instrumentos_modulares() -> list[dict[str, str]]:
    return [{"tipo": k, "descripcion": v} for k, v in _INSTRUMENTO_PLANTILLAS.items()]


def crear_instrumento(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    data: dict[str, Any],
) -> ComercialInstrumentoContractual:
    tipo = data.get("tipo", TipoInstrumentoContractual.SERVICIO_EIAAX)
    if tipo not in _INSTRUMENTO_PLANTILLAS:
        raise HTTPException(status_code=422, detail=f"Tipo de instrumento no válido: {tipo}")
    row = ComercialInstrumentoContractual(
        organization_id=org_id,
        proposal_id=proposal_id,
        tipo=tipo,
        nombre=data.get("nombre") or tipo.replace("_", " ").title(),
        contenido_resumen=data.get("contenido_resumen") or _INSTRUMENTO_PLANTILLAS[tipo],
        estado=data.get("estado") or EstadoInstrumentoContractual.BORRADOR,
        metadata_json=_json(data.get("metadata")),
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    return row


def instrumento_to_dict(row: ComercialInstrumentoContractual) -> dict[str, Any]:
    return {
        "id": row.id,
        "proposal_id": row.proposal_id,
        "tipo": row.tipo,
        "nombre": row.nombre,
        "contenido_resumen": row.contenido_resumen,
        "estado": row.estado,
        "metadata": _parse(row.metadata_json),
    }


def crear_compromiso_garantia(
    db: Session,
    user: User,
    org_id: str,
    proposal_id: str,
    data: dict[str, Any],
) -> ComercialCompromisoGarantia:
    tipo = data.get("tipo_compromiso", TipoCompromisoGarantia.CONTROL_NUESTRO)
    if tipo == TipoCompromisoGarantia.RESULTADO_EXTERNO:
        if not data.get("dependencias") and not data.get("atribucion"):
            raise HTTPException(
                status_code=422,
                detail="Resultados externos requieren dependencias y atribución explícitas",
            )
    row = ComercialCompromisoGarantia(
        organization_id=org_id,
        proposal_id=proposal_id,
        tipo_compromiso=tipo,
        descripcion=data["descripcion"],
        baseline=data.get("baseline"),
        objetivo=data.get("objetivo"),
        dependencias_json=_json(data.get("dependencias")),
        evidencia=data.get("evidencia"),
        atribucion=data.get("atribucion"),
        cumplimiento_estado=data.get("cumplimiento_estado", "PENDIENTE"),
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()
    return row


def compromiso_to_dict(row: ComercialCompromisoGarantia) -> dict[str, Any]:
    return {
        "id": row.id,
        "proposal_id": row.proposal_id,
        "tipo_compromiso": row.tipo_compromiso,
        "descripcion": row.descripcion,
        "baseline": row.baseline,
        "objetivo": row.objetivo,
        "dependencias": _parse(row.dependencias_json),
        "evidencia": row.evidencia,
        "atribucion": row.atribucion,
        "cumplimiento_estado": row.cumplimiento_estado,
    }


def recorrido_demo(
    db: Session,
    user: User,
    org_id: str,
    *,
    sector: str = "salud",
    area: str = "facturacion",
) -> dict[str, Any]:
    """Orquesta flujo demo completo reutilizando APIs existentes."""
    from app.services import evaluacion_service as evs
    from app.services import proactive_service as psvc

    exp = evs.create_expediente(
        db,
        organization_id=org_id,
        user_id=user.id,
        titulo=f"Demo {sector} — {area}",
        entidad_nombre="Prospecto Demo EIAAX",
        necesidad=f"Optimizar {area} en sector {sector}",
        objetivo="Reducir tiempos y aumentar recuperación",
        area_proceso=area,
        sector=sector,
        nivel="DIAGNOSTICA",
    )
    sync_informacion_contextual(db, exp, user_id=user.id)
    for item in db.query(EvaluacionInformacionItem).filter(EvaluacionInformacionItem.expediente_id == exp.id).all():
        if item.obligatorio:
            item.respuesta = f"Datos demo para {item.campo}"
            item.estado = "RECIBIDO"
    db.flush()
    evs.ejecutar_evaluacion_preliminar(db, exp.id, org_id, user_id=user.id)

    opp_payload = psvc.run_proactive_pipeline(
        db,
        organization_id=org_id,
        tipo="operativa",
        dominio=sector,
        evento="flujo_comercial_demo",
        payload={"titulo": f"Oportunidad {area}", "descripcion": "Detectada en demo", "impacto_estimado": 80000},
        origen="demo",
        user_id=user.id,
    )
    opp_id = opp_payload.get("opportunity_id")
    if opp_id:
        opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if opp:
            opp.origen_comercial = OrigenOportunidadComercial.INTERNA
            opp.valor_potencial_certidumbre = ClasificacionValorOportunidad.ESTIMADO
            opp.presentar_cliente = True
        evs.vincular_oportunidad(db, exp.id, org_id, opportunity_id=opp_id, user_id=user.id)

    prop = generar_propuesta_desde_dossier(db, user, org_id, exp.id, opportunity_id=opp_id, exigir_suficiencia=True)
    crear_instrumento(db, user, org_id, prop["proposal_id"], {"tipo": TipoInstrumentoContractual.NDA})
    crear_instrumento(db, user, org_id, prop["proposal_id"], {"tipo": TipoInstrumentoContractual.SLA})
    gar = crear_compromiso_garantia(
        db,
        user,
        org_id,
        prop["proposal_id"],
        {
            "tipo_compromiso": TipoCompromisoGarantia.CONTROL_NUESTRO,
            "descripcion": "Entrega de informe de hallazgos en plazo acordado",
            "baseline": "Sin informe",
            "objetivo": "Informe entregado",
        },
    )
    return {
        "evaluacion_id": exp.id,
        "opportunity_id": opp_id,
        "proposal_id": prop["proposal_id"],
        "presentacion_id": prop["presentacion_id"],
        "instrumentos": 2,
        "compromiso_id": gar.id,
        "flujo": "DEMO→prospecto→dossier→evaluación→oportunidad→propuesta→instrumentos",
    }
