"""Simulación de escenarios — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def simulate_scenarios(
    indicators: dict[str, Any],
    hypotheses: list[dict[str, Any]],
    primary_action: dict[str, Any] | None,
) -> dict[str, Any]:
    """Escenarios CONSERVADOR / PROBABLE / OPTIMISTA con supuestos explícitos."""
    car = indicators.get("cartera", {})
    rad = indicators.get("radicacion", {})
    glo = indicators.get("glosas", {})

    saldo = car.get("saldo_total", 0) if car.get("disponible") else 0
    tiempo_rad = rad.get("tiempo_promedio_factura_radicacion_dias")
    pct_glosa = glo.get("porcentaje_glosa") if glo.get("disponible") else None
    primary = next((h for h in hypotheses if h.get("estado") in ("CONFIRMADA", "PROBABLE")), None)

    base_assumption = _base_assumption(primary, tiempo_rad, pct_glosa)

    scenarios = {
        "CONSERVADOR": _scenario(
            name="Conservador",
            recovery_rate=0.08,
            time_reduction_days=2,
            assumption=f"{base_assumption} Efecto mínimo (8% recuperación).",
            saldo_base=saldo,
        ),
        "PROBABLE": _scenario(
            name="Probable",
            recovery_rate=0.18,
            time_reduction_days=5,
            assumption=f"{base_assumption} Efecto moderado (18% recuperación).",
            saldo_base=saldo,
        ),
        "OPTIMISTA": _scenario(
            name="Optimista",
            recovery_rate=0.32,
            time_reduction_days=10,
            assumption=f"{base_assumption} Efecto alto si ejecución disciplinada (32% recuperación).",
            saldo_base=saldo,
        ),
    }

    if isinstance(tiempo_rad, (int, float)) and tiempo_rad > 7:
        for key, sc in scenarios.items():
            sc["efecto_tiempo_radicacion_dias"] = sc["time_reduction_days"]
            sc["supuestos"].append(
                f"Reducción de {sc['time_reduction_days']} días en factura→radicación"
            )

    if primary_action:
        scenarios["PROBABLE"]["accion_simulada"] = primary_action.get("accion") or primary_action.get("accion_propuesta")

    return {
        "tipo": "PROYECTADO",
        "escenarios": scenarios,
        "advertencia": "Simulación con supuestos — no presentar como resultado real.",
    }


def _base_assumption(primary: dict | None, tiempo_rad: Any, pct_glosa: Any) -> str:
    if primary:
        return f"Hipótesis principal: {primary.get('titulo')}. "
    if isinstance(tiempo_rad, (int, float)) and tiempo_rad > 10:
        return "Demora de radicación identificada. "
    if isinstance(pct_glosa, (int, float)) and pct_glosa > 10:
        return "Glosas elevadas identificadas. "
    return "Sin hipótesis dominante — escenarios genéricos. "


def _scenario(
    *,
    name: str,
    recovery_rate: float,
    time_reduction_days: int,
    assumption: str,
    saldo_base: float,
) -> dict[str, Any]:
    valor = round(saldo_base * recovery_rate, 0) if saldo_base else INSUFICIENTE
    return {
        "nombre": name,
        "valor_recuperable_estimado": valor,
        "tasa_recuperacion": recovery_rate,
        "time_reduction_days": time_reduction_days,
        "supuestos": [assumption],
        "certidumbre": "PROYECTADO",
    }
