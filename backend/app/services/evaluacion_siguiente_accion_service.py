"""Motor de siguiente acción para expedientes de evaluación — Bloque Producto 2."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.evaluacion_models import (
    EvaluacionAccionExterna,
    EvaluacionExpediente,
    EvaluacionHallazgo,
    EvaluacionIndicador,
    EvaluacionInformacionItem,
    EvaluacionOportunidadLink,
)
from app.services.evaluacion_proveedor_externo_service import listar_proveedores
from app.services.evaluacion_integracion_gobierno import evaluar_politica_aprobacion
from app.services.evaluacion_integracion_finops import obtener_indicadores_economicos


def _pendientes_info(db: Session, expediente_id: str) -> list[EvaluacionInformacionItem]:
    return (
        db.query(EvaluacionInformacionItem)
        .filter(
            EvaluacionInformacionItem.expediente_id == expediente_id,
            EvaluacionInformacionItem.estado.in_(("PENDIENTE", "INCOMPLETO")),
        )
        .all()
    )


def _hallazgos(db: Session, expediente_id: str) -> list[EvaluacionHallazgo]:
    return (
        db.query(EvaluacionHallazgo)
        .filter(EvaluacionHallazgo.expediente_id == expediente_id)
        .order_by(EvaluacionHallazgo.created_at.desc())
        .all()
    )


def _acciones_pendientes(db: Session, expediente_id: str, org_id: str) -> list[EvaluacionAccionExterna]:
    return (
        db.query(EvaluacionAccionExterna)
        .filter(
            EvaluacionAccionExterna.expediente_id == expediente_id,
            EvaluacionAccionExterna.organization_id == org_id,
            EvaluacionAccionExterna.estado.in_(
                ("PENDIENTE_APROBACION", "PIIAX_NO_DISPONIBLE", "SOLICITADA", "EN_PROCESO"),
            ),
        )
        .all()
    )


def compute_siguiente_accion(
    db: Session,
    expediente: EvaluacionExpediente,
    *,
    permisos: set[str] | None = None,
) -> dict[str, Any]:
    """Determina acciones sugeridas según contexto — no botones estáticos."""
    permisos = permisos or set()
    org_id = expediente.organization_id
    pendientes = _pendientes_info(db, expediente.id)
    hallazgos = _hallazgos(db, expediente.id)
    acciones_pend = _acciones_pendientes(db, expediente.id, org_id)
    proveedores = listar_proveedores(db, org_id)
    proveedor_disp = any(p["disponible"] for p in proveedores)

    indicadores = (
        db.query(EvaluacionIndicador)
        .filter(EvaluacionIndicador.expediente_id == expediente.id)
        .count()
    )
    links_opp = (
        db.query(EvaluacionOportunidadLink)
        .filter(EvaluacionOportunidadLink.expediente_id == expediente.id)
        .count()
    )

    candidatas: list[dict[str, Any]] = []

    if pendientes or expediente.porcentaje_informacion < 55:
        candidatas.append({
            "codigo": "solicitar_informacion",
            "titulo": "Completar información faltante",
            "descripcion": f"Hay {len(pendientes)} requisito(s) pendiente(s). Sin esto, la confianza del análisis permanece limitada.",
            "prioridad": 95,
            "intencion": "B",
            "pestaña": "informacion",
            "requiere_permiso": "evaluacion.manage",
            "disponible": "evaluacion.manage" in permisos,
        })

    if not hallazgos and expediente.estado in ("BORRADOR", "EN_CURSO", "PRELIMINAR"):
        candidatas.append({
            "codigo": "ejecutar_evaluacion",
            "titulo": "Ejecutar evaluación preliminar",
            "descripcion": "Aún no hay hallazgos. Ejecute el análisis preliminar para generar hipótesis y evidencia.",
            "prioridad": 90,
            "intencion": "C",
            "pestaña": "analisis",
            "requiere_permiso": "evaluacion.evaluate",
            "disponible": "evaluacion.evaluate" in permisos,
        })

    if hallazgos and expediente.confianza_global in ("BAJA", "MEDIA"):
        candidatas.append({
            "codigo": "profundizar_analisis",
            "titulo": "Profundizar análisis",
            "descripcion": f"Confianza {expediente.confianza_global}. Conviene validar hipótesis con más evidencia o análisis IA.",
            "prioridad": 75,
            "intencion": "C",
            "pestaña": "analisis",
            "accion_agente": "profundizar_hallazgo",
            "disponible": True,
        })

    hallazgos_sin_opp = [h for h in hallazgos if not h.opportunity_id]
    if hallazgos_sin_opp and links_opp == 0:
        candidatas.append({
            "codigo": "detectar_oportunidad",
            "titulo": "Evaluar oportunidad de mejora",
            "descripcion": f"{len(hallazgos_sin_opp)} hallazgo(s) sin oportunidad vinculada. Puede crear una desde el hallazgo.",
            "prioridad": 70,
            "intencion": "G",
            "pestaña": "oportunidades",
            "requiere_permiso": "evaluacion.manage",
            "disponible": "evaluacion.manage" in permisos,
        })

    if hallazgos and indicadores == 0:
        candidatas.append({
            "codigo": "cuantificar_impacto",
            "titulo": "Cuantificar impacto",
            "descripcion": "Defina indicadores ANTES/PROYECTADO para separar proyección de resultado real.",
            "prioridad": 65,
            "intencion": "C",
            "pestaña": "impacto",
            "requiere_permiso": "evaluacion.indicadores.manage",
            "disponible": "evaluacion.indicadores.manage" in permisos,
        })

    hallazgos_externos = [
        h for h in hallazgos
        if any(k in (h.titulo + " " + (h.descripcion or "")).lower()
               for k in ("fuente", "externo", "sistema", "integración", "validar", "sincroniz"))
    ]
    if hallazgos_externos and "evaluacion.accion.request" in permisos:
        candidatas.append({
            "codigo": "solicitar_capacidad_externa",
            "titulo": "Validar contra fuente externa",
            "descripcion": "Un hallazgo sugiere verificación en sistema externo. Solicite la capacidad sin ejecutar automáticamente.",
            "prioridad": 60,
            "intencion": "D",
            "capacidad_sugerida": "consultar_datos",
            "pestaña": "analisis",
            "proveedor_disponible": proveedor_disp,
            "disponible": True,
        })

    for acc in acciones_pend:
        if acc.estado == "PENDIENTE_APROBACION":
            politica = evaluar_politica_aprobacion(acc.tipo_accion, {"accion_id": acc.id})
            candidatas.append({
                "codigo": "solicitar_aprobacion",
                "titulo": f"Aprobar acción: {acc.titulo}",
                "descripcion": politica.get("mensaje") or "Acción pendiente de aprobación humana.",
                "prioridad": 85,
                "intencion": "F",
                "accion_id": acc.id,
                "requiere_permiso": "evaluacion.accion.approve",
                "disponible": "evaluacion.accion.approve" in permisos,
            })
        elif acc.estado == "PIIAX_NO_DISPONIBLE":
            candidatas.append({
                "codigo": "proveedor_no_disponible",
                "titulo": "Proveedor externo no disponible",
                "descripcion": acc.error_mensaje or "La capacidad quedó registrada. Conecte un proveedor (PIIAX preferente) para ejecutar.",
                "prioridad": 50,
                "intencion": "E",
                "accion_id": acc.id,
                "estado_es": "NO DISPONIBLE",
                "disponible": True,
            })

    finops = obtener_indicadores_economicos(db, expediente.id, org_id)
    if finops and finops.get("integrado"):
        candidatas.append({
            "codigo": "incorporar_valor_finops",
            "titulo": "Incorporar valor económico (FinOps)",
            "descripcion": "Hay datos del motor económico disponibles para enriquecer el impacto.",
            "prioridad": 55,
            "intencion": "H",
            "pestaña": "impacto",
            "disponible": "evaluacion.indicadores.manage" in permisos,
        })

    if hallazgos and expediente.estado not in ("CERRADO", "ARCHIVADO"):
        candidatas.append({
            "codigo": "continuar_evaluacion",
            "titulo": "Continuar evaluación",
            "descripcion": "Revise hallazgos, impacto y oportunidades para decidir el siguiente paso del expediente.",
            "prioridad": 40,
            "intencion": "A",
            "pestaña": "resumen",
            "disponible": True,
        })

    candidatas.sort(key=lambda x: x["prioridad"], reverse=True)
    principal = candidatas[0] if candidatas else {
        "codigo": "sin_accion",
        "titulo": "Expediente al día",
        "descripcion": "No hay acciones prioritarias detectadas en este momento.",
        "prioridad": 0,
        "intencion": "A",
        "disponible": True,
    }

    resultado = {
        "principal": principal,
        "alternativas": candidatas[1:6],
        "contexto": {
            "estado_expediente": expediente.estado,
            "porcentaje_informacion": expediente.porcentaje_informacion,
            "confianza_global": expediente.confianza_global,
            "hallazgos_count": len(hallazgos),
            "proveedores": proveedores,
            "acciones_pendientes_count": len(acciones_pend),
        },
        "metodologia": "Motor contextual EIAAX — prioriza según información, hallazgos, confianza y capacidades.",
    }
    return resultado


def persistir_siguiente_accion(
    db: Session,
    expediente: EvaluacionExpediente,
    accion: dict[str, Any],
) -> None:
    expediente.siguiente_accion_json = json.dumps(accion, ensure_ascii=False)
    db.add(expediente)
