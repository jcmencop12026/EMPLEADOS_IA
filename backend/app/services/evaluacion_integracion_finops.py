"""Integración evaluación ↔ Motor Económico EIAAX — sin duplicar FinOps."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

INTEGRACION_FINOPS_DISPONIBLE = True


def obtener_indicadores_economicos(
    db: Session,
    expediente_id: str,
    organization_id: str,
) -> dict[str, Any]:
    """Consume motor económico real — sin exponer economía privada."""
    from app.services import economic_motor_service as motor

    try:
        values = motor.sum_values_by_nature(db, organization_id)
        costs = motor.sum_costs_by_class_and_kind(db, organization_id)
    except Exception:
        return {"integrado": True, "indicadores": [], "error": "motor_no_disponible"}

    return {
        "integrado": True,
        "indicadores": values,
        "costos": costs,
        "economia_privada_expuesta": False,
        "nota": "PROYECTADO y POTENCIAL no equivalen a REAL",
    }


def enriquecer_impacto_desde_finops(
    db: Session,
    expediente_id: str,
    organization_id: str,
) -> dict[str, Any]:
    """Enriquece resumen de impacto con datos del motor económico (sin economía privada)."""
    from app.services import economic_motor_service as motor

    datos = obtener_indicadores_economicos(db, expediente_id, organization_id)
    entity = motor.entity_view_summary(db, organization_id)
    return {
        "integrado": INTEGRACION_FINOPS_DISPONIBLE,
        "punto_integracion": "economic_motor_service",
        "datos": datos,
        "vista_entidad_segura": {
            "valores": entity.get("valores"),
            "nota_potencial": entity.get("nota_potencial"),
            "economia_privada_incluida": False,
        },
    }
