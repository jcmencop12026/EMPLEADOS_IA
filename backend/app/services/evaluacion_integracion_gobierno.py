"""Integración evaluación ↔ Gobierno Operacional — autoridad transversal de políticas."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

INTEGRACION_GOBIERNO_DISPONIBLE = True


def evaluar_politica_aprobacion(
    tipo_accion: str,
    contexto: dict[str, Any],
    *,
    db: Session | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Delega en gobierno_operacional_service.evaluar_accion — sin motor duplicado."""
    if db is not None and organization_id:
        from app.services.gobierno_operacional_service import evaluar_accion

        resultado = evaluar_accion(
            db,
            organization_id,
            tipo_accion=tipo_accion,
            recurso_tipo=contexto.get("recurso_tipo", "evaluacion_accion_externa"),
            criticidad=contexto.get("criticidad", "MEDIUM"),
            capacidad_externa=contexto.get("capacidad"),
        )
        return {
            "requiere_aprobacion": resultado.get("requiere_aprobacion_humana", False),
            "politica_ref": resultado.get("politica_id"),
            "integrado": True,
            "auto_ejecutar": resultado.get("auto_ejecutar"),
            "mensaje": resultado.get("motivo") or "Política evaluada por Gobierno Operacional",
            "punto_integracion": "gobierno_operacional.evaluar_accion",
        }

    requiere = tipo_accion in ("PROPUESTA", "EJECUCION")
    return {
        "requiere_aprobacion": requiere,
        "politica_ref": None,
        "integrado": False,
        "mensaje": "Contexto de organización requerido para evaluar política",
    }


def solicitar_aprobacion_gobierno(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    tipo_accion: str,
    descripcion: str,
    correlation_id: str,
    recurso_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crea solicitud en Gobierno Operacional vinculada al expediente/acción."""
    from app.services.gobierno_operacional_service import crear_solicitud

    return crear_solicitud(
        db,
        organization_id,
        user_id,
        {
            "tipo_accion": tipo_accion,
            "recurso_tipo": "evaluacion_accion_externa",
            "recurso_id": recurso_id,
            "descripcion": descripcion,
            "correlation_id": correlation_id,
            "payload": payload,
        },
    )
