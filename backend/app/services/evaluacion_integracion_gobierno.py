"""Punto de integración con Gobierno Operacional (agente A) — sin duplicar su motor."""

from __future__ import annotations

from typing import Any

# Contrato preparado para cuando la rama de Gobierno esté disponible para merge.
INTEGRACION_GOBIERNO_DISPONIBLE = False


def evaluar_politica_aprobacion(tipo_accion: str, contexto: dict[str, Any]) -> dict[str, Any]:
    """
    Evalúa si una acción requiere aprobación según políticas de gobierno.
    Stub local hasta integración con /api/operations/approvals y motor de A.
    """
    requiere = tipo_accion in ("PROPUESTA", "EJECUCION")
    return {
        "requiere_aprobacion": requiere,
        "politica_ref": None,
        "integrado": INTEGRACION_GOBIERNO_DISPONIBLE,
        "mensaje": (
            "Requiere aprobación humana según tipo de acción."
            if requiere
            else "No requiere aprobación previa."
        ),
        "punto_integracion": "gobierno_operacional.aprobaciones",
    }


def solicitar_aprobacion_gobierno(
    organization_id: str,
    contexto: dict[str, Any],
) -> dict[str, Any]:
    """Reservado: delegar aprobación al motor de Gobierno Operacional."""
    return {
        "enviado": False,
        "integrado": INTEGRACION_GOBIERNO_DISPONIBLE,
        "mensaje": "Integración con Gobierno Operacional pendiente de merge (agente A).",
    }
