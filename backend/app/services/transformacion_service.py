"""Arquitecto de Transformación Empresarial — orquestador sobre motores existentes."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.evaluacion_models import EvaluacionExpediente, EvaluacionHallazgo, EvaluacionInformacionItem
from app.services import evaluacion_service as eval_svc
from app.transformacion_models import (
    ALTERNATIVA_TIPOS,
    CAUSA_TIPOS,
    DossierCausa,
    DossierConocimientoItem,
    DossierEmpresarial,
    DossierMapaNodo,
    EmpleadoIARequerimiento,
    CapacidadExternaNecesidad,
    ESCENARIO_TIPOS,
    TransformacionAlternativa,
    TransformacionEscenario,
    TransformacionIniciativa,
)

_SCORE_MAP = {"BAJO": 1, "MEDIO": 2, "ALTO": 3, "MEDIA": 2, "ALTA": 3, "BAJA": 1}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_correlation() -> str:
    return str(uuid.uuid4())


def _json_loads(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _get_dossier(db: Session, organization_id: str) -> DossierEmpresarial:
    d = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == organization_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dossier empresarial no encontrado")
    return d


def get_or_create_dossier(db: Session, organization_id: str) -> DossierEmpresarial:
    d = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == organization_id).first()
    if d:
        return d
    d = DossierEmpresarial(
        organization_id=organization_id,
        etapa_actual="PROSPECTO",
        correlation_id=_new_correlation(),
    )
    db.add(d)
    db.flush()
    return d


def _dossier_dict(d: DossierEmpresarial) -> dict[str, Any]:
    return {
        "id": d.id,
        "organization_id": d.organization_id,
        "etapa_actual": d.etapa_actual,
        "sector": d.sector,
        "resumen": d.resumen,
        "confianza_global": d.confianza_global,
        "porcentaje_completitud": d.porcentaje_completitud,
        "expediente_activo_id": d.expediente_activo_id,
        "correlation_id": d.correlation_id,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def registrar_necesidad(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    titulo: str,
    necesidad: str,
    objetivo: str | None = None,
    area_proceso: str | None = None,
    entidad_nombre: str | None = None,
    nivel: str = "PRELIMINAR",
) -> dict[str, Any]:
    """NECESIDAD → expediente + dossier + información adaptativa."""
    dossier = get_or_create_dossier(db, organization_id)
    dossier.etapa_actual = "EVALUACION"
    nombre = entidad_nombre or titulo[:80]
    exp = eval_svc.create_expediente(
        db,
        organization_id=organization_id,
        user_id=user_id,
        titulo=titulo,
        entidad_nombre=nombre,
        necesidad=necesidad,
        objetivo=objetivo,
        area_proceso=area_proceso,
        nivel=nivel,
    )
    dossier.expediente_activo_id = exp.id
    dossier.resumen = necesidad[:500] if necesidad else dossier.resumen
    _absorber_conocimiento_expediente(db, dossier, exp)
    prefill_from_dossier(db, dossier, exp)
    dossier.updated_at = _utcnow()
    return {
        "dossier": _dossier_dict(dossier),
        "expediente": eval_svc.expediente_to_detail(db, exp),
        "paso": "necesidad_registrada",
    }


def _absorber_conocimiento_expediente(db: Session, dossier: DossierEmpresarial, exp: EvaluacionExpediente) -> None:
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .all()
    )
    for item in items:
        if not item.respuesta or not item.respuesta.strip():
            continue
        existing = (
            db.query(DossierConocimientoItem)
            .filter(
                DossierConocimientoItem.dossier_id == dossier.id,
                DossierConocimientoItem.campo == item.campo,
                DossierConocimientoItem.vigente.is_(True),
            )
            .first()
        )
        calidad = "ALTA" if item.estado == "RECIBIDO" else "MEDIA"
        if existing:
            existing.valor = item.respuesta
            existing.calidad = calidad
            existing.expediente_id = exp.id
            existing.updated_at = _utcnow()
        else:
            db.add(
                DossierConocimientoItem(
                    organization_id=dossier.organization_id,
                    dossier_id=dossier.id,
                    campo=item.campo,
                    etiqueta=item.etiqueta,
                    valor=item.respuesta,
                    fuente="expediente",
                    calidad=calidad,
                    expediente_id=exp.id,
                    explicacion_calidad=f"Absorbido del expediente {exp.codigo}",
                )
            )
    _recalc_dossier_completitud(db, dossier)


def prefill_from_dossier(db: Session, dossier: DossierEmpresarial, exp: EvaluacionExpediente) -> int:
    """Rellena ítems del expediente con conocimiento vigente del dossier — no repreguntar."""
    conocimiento = (
        db.query(DossierConocimientoItem)
        .filter(DossierConocimientoItem.dossier_id == dossier.id, DossierConocimientoItem.vigente.is_(True))
        .all()
    )
    by_campo = {c.campo: c for c in conocimiento}
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .all()
    )
    filled = 0
    for item in items:
        known = by_campo.get(item.campo)
        if known and known.valor and not item.respuesta:
            item.respuesta = known.valor
            item.estado = "RECIBIDO"
            item.evidencia_ref = item.evidencia_ref or f"dossier:{known.id}"
            filled += 1
    if items:
        eval_svc._recalc_metrics(exp, items)  # noqa: SLF001
    return filled


def evaluar_suficiencia(db: Session, organization_id: str, expediente_id: str) -> dict[str, Any]:
    """Evalúa completitud, faltantes y confianza sin bloquear el diagnóstico."""
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    items = (
        db.query(EvaluacionInformacionItem)
        .filter(EvaluacionInformacionItem.expediente_id == exp.id)
        .order_by(EvaluacionInformacionItem.orden)
        .all()
    )
    faltantes = [
        {
            "campo": i.campo,
            "etiqueta": i.etiqueta,
            "estado": i.estado,
            "obligatorio": i.obligatorio,
            "por_que": i.por_que,
            "impacto_precision": i.impacto_precision,
        }
        for i in items
        if i.estado in ("PENDIENTE", "INCOMPLETO") and i.obligatorio
    ]
    opcionales = [i.etiqueta for i in items if i.estado == "OPCIONAL" and not i.respuesta]
    puede_continuar = True
    explicacion = (
        "Puede continuar con diagnóstico preliminar; la confianza será menor."
        if faltantes
        else "Información suficiente para el nivel solicitado."
    )
    return {
        "expediente_id": expediente_id,
        "porcentaje_informacion": exp.porcentaje_informacion,
        "confianza_global": exp.confianza_global,
        "faltantes": faltantes,
        "opcionales_sin_responder": opcionales,
        "puede_continuar": puede_continuar,
        "explicacion": explicacion,
        "calidad": _evaluar_calidad(items),
    }


def _evaluar_calidad(items: list[EvaluacionInformacionItem]) -> dict[str, Any]:
    recibidos = [i for i in items if i.estado == "RECIBIDO"]
    return {
        "completitud": f"{len(recibidos)}/{len(items)} ítems con respuesta",
        "consistencia": "Sin contradicciones detectadas" if recibidos else "Datos insuficientes",
        "procedencia": "Captura guiada y dossier empresarial",
        "confiabilidad": "ALTA" if len(recibidos) >= len(items) * 0.75 else "MEDIA" if recibidos else "BAJA",
    }


def _recalc_dossier_completitud(db: Session, dossier: DossierEmpresarial) -> None:
    total = db.query(DossierConocimientoItem).filter(
        DossierConocimientoItem.dossier_id == dossier.id,
        DossierConocimientoItem.vigente.is_(True),
    ).count()
    dossier.porcentaje_completitud = min(100, total * 12)
    if dossier.porcentaje_completitud >= 75:
        dossier.confianza_global = "ALTA"
    elif dossier.porcentaje_completitud >= 40:
        dossier.confianza_global = "MEDIA"
    else:
        dossier.confianza_global = "BAJA"


def construir_mapa_desde_expediente(
    db: Session,
    organization_id: str,
    expediente_id: str,
) -> list[DossierMapaNodo]:
    dossier = get_or_create_dossier(db, organization_id)
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    nodos: list[DossierMapaNodo] = []
    area = exp.area_proceso or "Operaciones"
    area_nodo = _upsert_mapa_nodo(db, dossier, exp, None, "AREA", area, "Área derivada del expediente")
    nodos.append(area_nodo)
    proc_item = (
        db.query(EvaluacionInformacionItem)
        .filter(
            EvaluacionInformacionItem.expediente_id == exp.id,
            EvaluacionInformacionItem.campo == "procesos_afectados",
        )
        .first()
    )
    if proc_item and proc_item.respuesta:
        for proc in [p.strip() for p in proc_item.respuesta.split(",") if p.strip()][:5]:
            nodos.append(
                _upsert_mapa_nodo(db, dossier, exp, area_nodo.id, "PROCESO", proc, "Proceso declarado")
            )
    if exp.necesidad:
        nodos.append(
            _upsert_mapa_nodo(
                db, dossier, exp, area_nodo.id, "PROBLEMA", "Necesidad principal",
                exp.necesidad[:300], confianza=exp.confianza_global,
            )
        )
    return nodos


def _upsert_mapa_nodo(
    db: Session,
    dossier: DossierEmpresarial,
    exp: EvaluacionExpediente,
    parent_id: str | None,
    tipo: str,
    nombre: str,
    descripcion: str | None = None,
    *,
    confianza: str = "MEDIA",
) -> DossierMapaNodo:
    existing = (
        db.query(DossierMapaNodo)
        .filter(
            DossierMapaNodo.dossier_id == dossier.id,
            DossierMapaNodo.tipo == tipo,
            DossierMapaNodo.nombre == nombre,
        )
        .first()
    )
    if existing:
        existing.descripcion = descripcion or existing.descripcion
        existing.confianza = confianza
        return existing
    nodo = DossierMapaNodo(
        organization_id=dossier.organization_id,
        dossier_id=dossier.id,
        parent_id=parent_id,
        tipo=tipo,
        nombre=nombre,
        descripcion=descripcion,
        confianza=confianza,
        expediente_id=exp.id,
    )
    db.add(nodo)
    db.flush()
    return nodo


def _clasificar_causas_desde_hallazgos(
    db: Session,
    dossier: DossierEmpresarial,
    exp: EvaluacionExpediente,
    hallazgos: list[EvaluacionHallazgo],
) -> list[DossierCausa]:
    causas: list[DossierCausa] = []
    sintoma: DossierCausa | None = None
    for h in hallazgos:
        if h.es_problema_original:
            sintoma = DossierCausa(
                organization_id=exp.organization_id,
                dossier_id=dossier.id,
                expediente_id=exp.id,
                hallazgo_id=h.id,
                tipo="SINTOMA",
                titulo=h.titulo,
                descripcion=h.descripcion,
                evidencia=h.evidencia,
                confianza=h.confianza,
                explicacion_confianza=h.explicacion_confianza,
            )
            db.add(sintoma)
            db.flush()
            causas.append(sintoma)
    for h in hallazgos:
        if h.es_problema_original:
            continue
        tipo = "CAUSA_PROBABLE" if h.tipo_contenido == "INFERENCIA" else "PROBLEMA"
        if "pendiente" in (h.titulo or "").lower():
            tipo = "PROBLEMA"
        c = DossierCausa(
            organization_id=exp.organization_id,
            dossier_id=dossier.id,
            expediente_id=exp.id,
            hallazgo_id=h.id,
            parent_id=sintoma.id if sintoma else None,
            tipo=tipo,
            titulo=h.titulo,
            descripcion=h.descripcion,
            evidencia=h.evidencia,
            confianza=h.confianza,
            explicacion_confianza=h.explicacion_confianza or "Hipótesis — requiere validación.",
        )
        db.add(c)
        causas.append(c)
    db.flush()
    return causas


def _generar_alternativas(
    db: Session,
    dossier: DossierEmpresarial,
    exp: EvaluacionExpediente,
    causas: list[DossierCausa],
    confianza: str,
) -> list[TransformacionAlternativa]:
    alternativas: list[TransformacionAlternativa] = []
    specs: list[tuple[str, str, str]] = [
        ("SIMPLIFICAR", "Simplificar proceso afectado", "Reducir pasos manuales y duplicidades detectadas."),
        ("DIGITALIZAR", "Digitalizar captura y seguimiento", "Reemplazar controles manuales por flujo digital trazable."),
        ("AUTOMATIZAR", "Automatizar tareas repetitivas", "Liberar capacidad operativa en actividades de alto volumen."),
        ("MANTENER_HUMANO", "Mantener decisión humana crítica", "Conservar supervisión donde el riesgo o la variabilidad lo exigen."),
    ]
    if confianza != "ALTA":
        specs.append(
            ("MEDIR", "Establecer línea base antes de transformar", "Medir indicadores actuales para fundamentar decisiones."),
        )
    if any("sistema" in (c.descripcion or "").lower() or "integr" in (c.titulo or "").lower() for c in causas):
        specs.append(
            ("INTEGRAR", "Integrar sistemas y fuentes de información", "Eliminar silos de datos entre herramientas."),
        )
    if exp.nivel in ("DIAGNOSTICA", "PROFUNDA"):
        specs.append(
            ("APLICAR_IA", "Aplicar IA donde aporte valor verificable", "Solo si existe información suficiente y supervisión definida."),
        )
        specs.append(
            ("EMPLEADO_IA", "Empleado IA para tarea recurrente", "Delegar rutina con entradas/salidas acotadas."),
        )
    causa_ref = causas[0] if causas else None
    for tipo, titulo, desc in specs:
        if tipo not in ALTERNATIVA_TIPOS:
            continue
        impacto = "ALTO" if tipo in ("AUTOMATIZAR", "INTEGRAR") else "MEDIO"
        esfuerzo = "ALTO" if tipo in ("INTEGRAR", "APLICAR_IA") else "MEDIO"
        riesgo = "BAJO" if tipo == "MANTENER_HUMANO" else "MEDIO"
        score = _score_alternativa(impacto, esfuerzo, riesgo, confianza)
        alt = TransformacionAlternativa(
            organization_id=exp.organization_id,
            dossier_id=dossier.id,
            expediente_id=exp.id,
            causa_id=causa_ref.id if causa_ref else None,
            tipo=tipo,
            titulo=titulo,
            descripcion=desc,
            impacto=impacto,
            costo="MEDIO",
            esfuerzo=esfuerzo,
            riesgo=riesgo,
            tiempo="1-3 meses" if esfuerzo == "MEDIO" else "3-6 meses",
            complejidad=esfuerzo.replace("ALTO", "ALTA").replace("MEDIO", "MEDIA").replace("BAJO", "BAJA"),
            reversibilidad="MEDIA",
            madurez=confianza.replace("ALTA", "ALTA").replace("MEDIA", "MEDIA").replace("BAJA", "BAJA"),
            confianza=confianza,
            explicacion=f"Recomendada porque aborda {causa_ref.titulo if causa_ref else 'la necesidad'} con balance impacto/esfuerzo.",
            score_total=score,
            scores_json=json.dumps({"impacto": impacto, "esfuerzo": esfuerzo, "riesgo": riesgo}, ensure_ascii=False),
            recomendada=score >= 7,
        )
        db.add(alt)
        alternativas.append(alt)
    db.flush()
    if alternativas:
        best = max(alternativas, key=lambda a: a.score_total)
        for a in alternativas:
            a.recomendada = a.id == best.id
    return alternativas


def _score_alternativa(impacto: str, esfuerzo: str, riesgo: str, confianza: str) -> int:
    return (
        _SCORE_MAP.get(impacto, 2) * 3
        + (4 - _SCORE_MAP.get(esfuerzo, 2))
        + (4 - _SCORE_MAP.get(riesgo, 2))
        + _SCORE_MAP.get(confianza, 2)
    )


def _priorizar_iniciativas(
    db: Session,
    dossier: DossierEmpresarial,
    alternativas: list[TransformacionAlternativa],
) -> list[TransformacionIniciativa]:
    iniciativas: list[TransformacionIniciativa] = []
    for alt in sorted(alternativas, key=lambda a: a.score_total, reverse=True):
        clasificacion = "RAPIDA" if alt.esfuerzo == "BAJO" else "ESTRATEGICA" if alt.impacto == "ALTO" else "TACTICA"
        ini = TransformacionIniciativa(
            organization_id=dossier.organization_id,
            dossier_id=dossier.id,
            alternativa_id=alt.id,
            titulo=alt.titulo,
            descripcion=alt.descripcion,
            clasificacion=clasificacion,
            prioridad_score=alt.score_total,
            impacto_vs_esfuerzo_json=json.dumps(
                {"impacto": alt.impacto, "esfuerzo": alt.esfuerzo, "riesgo": alt.riesgo},
                ensure_ascii=False,
            ),
            confianza=alt.confianza,
        )
        db.add(ini)
        iniciativas.append(ini)
    db.flush()
    return iniciativas


def _generar_escenarios(
    db: Session,
    dossier: DossierEmpresarial,
    exp: EvaluacionExpediente,
    iniciativas: list[TransformacionIniciativa],
) -> list[TransformacionEscenario]:
    escenarios_def = [
        ("ACTUAL", "Situación actual (proceso vigente)", False, "Estado base sin cambios estructurales."),
        ("OPTIMIZADO", "Escenario optimizado (proyectado)", True, "Mejoras de proceso sin automatización completa."),
        ("AUTOMATIZADO", "Escenario automatizado (proyectado)", True, "Automatización de tareas repetitivas."),
        ("ASISTIDO_IA", "Escenario asistido por IA (proyectado)", True, "IA asiste al humano — no sustituye todo el proceso."),
        ("ALTAMENTE_AUTOMATIZADO", "Altamente automatizado (proyectado)", True, "Máxima automatización viable con controles."),
    ]
    escenarios: list[TransformacionEscenario] = []
    for tipo, titulo, proyectado, nota in escenarios_def:
        if tipo not in ESCENARIO_TIPOS:
            continue
        desc = (
            exp.necesidad or "Estado base registrado en el dossier."
            if tipo == "ACTUAL"
            else f"{nota} Basado en {len(iniciativas)} iniciativa(s)."
        )
        esc = TransformacionEscenario(
            organization_id=dossier.organization_id,
            dossier_id=dossier.id,
            tipo=tipo,
            titulo=titulo,
            descripcion=desc,
            proyeccion_json=json.dumps(
                {
                    "iniciativas": [i.titulo for i in iniciativas[:3]],
                    "advertencia": "Proyección — no es resultado real" if proyectado else None,
                },
                ensure_ascii=False,
            ),
            es_proyectado=proyectado,
            confianza=exp.confianza_global,
        )
        db.add(esc)
        escenarios.append(esc)
    db.flush()
    return escenarios


def _generar_requerimientos_empleado_ia(
    db: Session,
    dossier: DossierEmpresarial,
    alternativas: list[TransformacionAlternativa],
    iniciativas: list[TransformacionIniciativa],
) -> list[EmpleadoIARequerimiento]:
    reqs: list[EmpleadoIARequerimiento] = []
    ia_alts = [a for a in alternativas if a.tipo in ("EMPLEADO_IA", "APLICAR_IA")]
    for alt in ia_alts:
        ini = next((i for i in iniciativas if i.alternativa_id == alt.id), None)
        req = EmpleadoIARequerimiento(
            organization_id=dossier.organization_id,
            dossier_id=dossier.id,
            iniciativa_id=ini.id if ini else None,
            alternativa_id=alt.id,
            objetivo=alt.titulo,
            responsabilidad="Ejecutar tarea recurrente con supervisión humana definida",
            entradas_json=json.dumps(["Datos del proceso", "Reglas de negocio"], ensure_ascii=False),
            salidas_json=json.dumps(["Informe", "Alertas"], ensure_ascii=False),
            herramientas_json=json.dumps(["conocimiento", "operaciones"], ensure_ascii=False),
            frecuencia="Diaria",
            riesgo=alt.riesgo.replace("MEDIO", "MEDIO"),
            supervision="Revisión humana en excepciones y muestras periódicas",
            indicadores_json=json.dumps(["Tiempo de ciclo", "Tasa de error"], ensure_ascii=False),
            confianza=alt.confianza,
        )
        db.add(req)
        reqs.append(req)
    db.flush()
    return reqs


def _generar_capacidades_externas(
    db: Session,
    dossier: DossierEmpresarial,
    alternativas: list[TransformacionAlternativa],
) -> list[CapacidadExternaNecesidad]:
    necesidades: list[CapacidadExternaNecesidad] = []
    for alt in [a for a in alternativas if a.tipo in ("INTEGRAR", "AUTOMATIZAR", "DIGITALIZAR")]:
        n = CapacidadExternaNecesidad(
            organization_id=dossier.organization_id,
            dossier_id=dossier.id,
            alternativa_id=alt.id,
            necesidad_empresarial=f"Integrar o automatizar: {alt.titulo}",
            contrato_json=json.dumps(
                {
                    "tipo_necesidad": alt.tipo,
                    "descripcion": alt.descripcion,
                    "integracion_futura": "capacidad_externa_abstraccion_GENERAL",
                    "piiax": False,
                },
                ensure_ascii=False,
            ),
            confianza=alt.confianza,
        )
        db.add(n)
        necesidades.append(n)
    db.flush()
    return necesidades


def ejecutar_diagnostico_transformacion(
    db: Session,
    organization_id: str,
    expediente_id: str,
    *,
    user_id: str,
) -> dict[str, Any]:
    """Flujo completo: evaluar → mapa → causas → alternativas → priorizar → escenarios."""
    dossier = get_or_create_dossier(db, organization_id)
    exp = eval_svc._get_expediente(db, expediente_id, organization_id)  # noqa: SLF001
    dossier.expediente_activo_id = exp.id
    dossier.etapa_actual = "DIAGNOSTICO"
    _absorber_conocimiento_expediente(db, dossier, exp)

    suficiencia = evaluar_suficiencia(db, organization_id, expediente_id)
    eval_result = eval_svc.ejecutar_evaluacion_preliminar(
        db, expediente_id, organization_id, user_id=user_id,
    )
    hallazgos = (
        db.query(EvaluacionHallazgo)
        .filter(EvaluacionHallazgo.expediente_id == exp.id)
        .all()
    )
    mapa = construir_mapa_desde_expediente(db, organization_id, expediente_id)
    causas = _clasificar_causas_desde_hallazgos(db, dossier, exp, hallazgos)
    alternativas = _generar_alternativas(db, dossier, exp, causas, exp.confianza_global)
    iniciativas = _priorizar_iniciativas(db, dossier, alternativas)
    escenarios = _generar_escenarios(db, dossier, exp, iniciativas)
    empleado_ia = _generar_requerimientos_empleado_ia(db, dossier, alternativas, iniciativas)
    capacidades = _generar_capacidades_externas(db, dossier, alternativas)

    exp.estado = "PRELIMINAR" if exp.nivel == "PRELIMINAR" else "DIAGNOSTICA"
    dossier.etapa_actual = "OPORTUNIDADES"
    dossier.confianza_global = exp.confianza_global
    dossier.updated_at = _utcnow()

    return {
        "paso": "diagnostico_completado",
        "dossier": _dossier_dict(dossier),
        "suficiencia": suficiencia,
        "evaluacion": eval_result,
        "mapa_nodos": len(mapa),
        "causas": [_causa_dict(c) for c in causas],
        "alternativas": [_alternativa_dict(a) for a in alternativas],
        "iniciativas": [_iniciativa_dict(i) for i in iniciativas],
        "escenarios": [_escenario_dict(e) for e in escenarios],
        "empleado_ia_requerimientos": [_empleado_ia_dict(r) for r in empleado_ia],
        "capacidades_externas": [_capacidad_dict(c) for c in capacidades],
        "siguiente_accion": _siguiente_accion(alternativas, suficiencia),
    }


def _causa_dict(c: DossierCausa) -> dict[str, Any]:
    return {
        "id": c.id, "tipo": c.tipo, "titulo": c.titulo,
        "descripcion": c.descripcion, "confianza": c.confianza,
        "explicacion_confianza": c.explicacion_confianza,
    }


def _alternativa_dict(a: TransformacionAlternativa) -> dict[str, Any]:
    return {
        "id": a.id, "tipo": a.tipo, "titulo": a.titulo, "descripcion": a.descripcion,
        "impacto": a.impacto, "esfuerzo": a.esfuerzo, "riesgo": a.riesgo,
        "confianza": a.confianza, "explicacion": a.explicacion,
        "score_total": a.score_total, "recomendada": a.recomendada,
    }


def _iniciativa_dict(i: TransformacionIniciativa) -> dict[str, Any]:
    return {
        "id": i.id, "titulo": i.titulo, "clasificacion": i.clasificacion,
        "prioridad_score": i.prioridad_score, "confianza": i.confianza,
    }


def _escenario_dict(e: TransformacionEscenario) -> dict[str, Any]:
    return {
        "id": e.id, "tipo": e.tipo, "titulo": e.titulo,
        "es_proyectado": e.es_proyectado, "confianza": e.confianza,
        "proyeccion": _json_loads(e.proyeccion_json, {}),
    }


def _empleado_ia_dict(r: EmpleadoIARequerimiento) -> dict[str, Any]:
    return {"id": r.id, "objetivo": r.objetivo, "frecuencia": r.frecuencia, "confianza": r.confianza}


def _capacidad_dict(c: CapacidadExternaNecesidad) -> dict[str, Any]:
    return {
        "id": c.id,
        "necesidad_empresarial": c.necesidad_empresarial,
        "contrato": _json_loads(c.contrato_json, {}),
    }


def _siguiente_accion(
    alternativas: list[TransformacionAlternativa],
    suficiencia: dict[str, Any],
) -> dict[str, Any]:
    recomendada = next((a for a in alternativas if a.recomendada), None)
    if suficiencia.get("faltantes"):
        return {
            "accion": "completar_informacion",
            "mensaje": "Complete información pendiente para aumentar confianza.",
            "faltantes": [f["etiqueta"] for f in suficiencia["faltantes"][:3]],
        }
    if recomendada:
        return {
            "accion": "iniciar_transformacion",
            "mensaje": f"Priorizar: {recomendada.titulo}",
            "alternativa_id": recomendada.id,
        }
    return {"accion": "revisar_diagnostico", "mensaje": "Revise hallazgos y alternativas generadas."}


def get_dossier_completo(db: Session, organization_id: str, *, create: bool = True) -> dict[str, Any] | None:
    if create:
        dossier = get_or_create_dossier(db, organization_id)
    else:
        dossier = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == organization_id).first()
        if dossier is None:
            return None
    conocimiento = (
        db.query(DossierConocimientoItem)
        .filter(DossierConocimientoItem.dossier_id == dossier.id, DossierConocimientoItem.vigente.is_(True))
        .all()
    )
    mapa = db.query(DossierMapaNodo).filter(DossierMapaNodo.dossier_id == dossier.id).all()
    causas = db.query(DossierCausa).filter(DossierCausa.dossier_id == dossier.id).all()
    alternativas = (
        db.query(TransformacionAlternativa)
        .filter(TransformacionAlternativa.dossier_id == dossier.id)
        .order_by(TransformacionAlternativa.score_total.desc())
        .all()
    )
    iniciativas = (
        db.query(TransformacionIniciativa)
        .filter(TransformacionIniciativa.dossier_id == dossier.id)
        .order_by(TransformacionIniciativa.prioridad_score.desc())
        .all()
    )
    escenarios = db.query(TransformacionEscenario).filter(TransformacionEscenario.dossier_id == dossier.id).all()
    exp_detail = None
    if dossier.expediente_activo_id:
        try:
            exp = eval_svc._get_expediente(db, dossier.expediente_activo_id, organization_id)  # noqa: SLF001
            exp_detail = eval_svc.expediente_to_summary(exp)
        except HTTPException:
            pass
    return {
        **_dossier_dict(dossier),
        "expediente_activo": exp_detail,
        "conocimiento": [
            {"campo": c.campo, "etiqueta": c.etiqueta, "valor": c.valor, "fuente": c.fuente, "calidad": c.calidad}
            for c in conocimiento
        ],
        "mapa": [{"id": n.id, "tipo": n.tipo, "nombre": n.nombre, "parent_id": n.parent_id} for n in mapa],
        "causas": [_causa_dict(c) for c in causas],
        "alternativas": [_alternativa_dict(a) for a in alternativas],
        "iniciativas": [_iniciativa_dict(i) for i in iniciativas],
        "escenarios": [_escenario_dict(e) for e in escenarios],
    }


def get_recorrido_estado(
    db: Session, organization_id: str, expediente_id: str | None = None, *, create: bool = True,
) -> dict[str, Any]:
    """Estado del recorrido progresivo para UX."""
    if create:
        dossier = get_or_create_dossier(db, organization_id)
    else:
        dossier = db.query(DossierEmpresarial).filter(DossierEmpresarial.organization_id == organization_id).first()
        if dossier is None:
            return {"pasos": [], "dossier": None, "suficiencia": None}
    eid = expediente_id or dossier.expediente_activo_id
    pasos = [
        {"id": "necesidad", "label": "Necesidad", "completo": bool(dossier.resumen)},
        {"id": "informacion", "label": "Información", "completo": dossier.porcentaje_completitud > 0},
        {"id": "diagnostico", "label": "Diagnóstico", "completo": dossier.etapa_actual in ("DIAGNOSTICO", "OPORTUNIDADES", "PROPUESTA", "CLIENTE", "IMPLEMENTACION", "OPERACION", "MEDICION")},
        {"id": "transformacion", "label": "Transformación", "completo": db.query(TransformacionAlternativa).filter(TransformacionAlternativa.dossier_id == dossier.id).count() > 0},
        {"id": "accion", "label": "Siguiente acción", "completo": False},
    ]
    suficiencia = None
    if eid:
        try:
            suficiencia = evaluar_suficiencia(db, organization_id, eid)
            pasos[1]["detalle"] = f"{suficiencia['porcentaje_informacion']}% — {suficiencia['confianza_global']}"
        except HTTPException:
            pass
    alt_count = db.query(TransformacionAlternativa).filter(TransformacionAlternativa.dossier_id == dossier.id).count()
    if alt_count:
        pasos[4]["completo"] = True
    return {"pasos": pasos, "dossier": _dossier_dict(dossier), "suficiencia": suficiencia}
