"""Punto de integración con Motor Económico / FinOps (agente B) — sin duplicarlo."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

INTEGRACION_FINOPS_DISPONIBLE = False


def obtener_indicadores_economicos(
    db: Session,
    expediente_id: str,
    organization_id: str,
) -> dict[str, Any] | None:
    """
    Reservado: consumir resultados del motor FinOps por expediente u oportunidad vinculada.
    Retorna None hasta que la rama de B esté integrada.
    """
    if not INTEGRACION_FINOPS_DISPONIBLE:
        return {"integrado": False, "indicadores": []}
    return None


def enriquecer_impacto_desde_finops(
    db: Session,
    expediente_id: str,
    organization_id: str,
) -> dict[str, Any]:
    """Punto de extensión para valor REAL desde FinOps."""
    return {
        "integrado": INTEGRACION_FINOPS_DISPONIBLE,
        "punto_integracion": "finops.valoracion",
        "datos": None,
    }
