"""Herramientas analíticas especializadas IPS — matemáticas fuera del prompt."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import (
    calc_cartera,
    calc_contratos,
    calc_facturacion,
    calc_glosas,
    calc_radicacion,
    calc_traceability,
    compute_all_indicators,
)
from app.services.salud_normalization import normalize_dataset, profile_data_quality


def analisis_facturado_radicado(fact_records: list[dict], rad_records: list[dict]) -> dict[str, Any]:
    return calc_radicacion(fact_records, rad_records)


def analisis_aging(cartera_records: list[dict]) -> dict[str, Any]:
    result = calc_cartera(cartera_records)
    if result.get("disponible"):
        return {"aging": result["aging"], "saldo_total": result["saldo_total"]}
    return result


def analisis_dias_pago(cartera_records: list[dict], pago_records: list[dict]) -> dict[str, Any]:
    cartera = calc_cartera(cartera_records, pago_records)
    if not cartera.get("disponible"):
        return cartera
    return {
        "recaudo": cartera.get("recaudo"),
        "saldo_pendiente": cartera.get("saldo_total"),
        "por_entidad": cartera.get("por_entidad"),
    }


def analisis_concentracion(fact_records: list[dict]) -> dict[str, Any]:
    fact = calc_facturacion(fact_records)
    if not fact.get("disponible"):
        return fact
    return {
        "concentracion": fact.get("concentracion_principal_pagador_pct"),
        "por_pagador": fact.get("facturacion_por_pagador"),
    }


def analisis_glosas(glosa_records: list[dict], fact_records: list[dict] | None = None) -> dict[str, Any]:
    return calc_glosas(glosa_records, fact_records)


def analisis_tendencias(fact_records: list[dict]) -> dict[str, Any]:
    fact = calc_facturacion(fact_records)
    if not fact.get("disponible"):
        return fact
    por_periodo = fact.get("facturacion_por_periodo", {})
    periods = sorted(por_periodo.keys())
    tendencia = []
    for i in range(1, len(periods)):
        prev = por_periodo[periods[i - 1]]
        curr = por_periodo[periods[i]]
        var = round(((curr - prev) / prev) * 100, 2) if prev else 0
        tendencia.append({"periodo": periods[i], "variacion_pct": var})
    return {"tendencia": tendencia, "por_periodo": por_periodo}


def analisis_anomalias(fact_records: list[dict]) -> dict[str, Any]:
    from app.services.salud_indicators import _to_float
    norm = normalize_dataset("facturacion", fact_records)
    valores = [_to_float(r.get("valor_facturado")) for r in norm]
    valores_ok = [v for v in valores if v is not None]
    if len(valores_ok) < 3:
        return {"disponible": False, "mensaje": "Información insuficiente"}
    media = sum(valores_ok) / len(valores_ok)
    umbral = media * 3
    anomalias = [
        {"numero_factura": r.get("numero_factura"), "valor": _to_float(r.get("valor_facturado"))}
        for r in norm
        if (_to_float(r.get("valor_facturado")) or 0) > umbral
    ]
    return {"disponible": True, "anomalias": anomalias, "media": media, "umbral": umbral}


def comparacion_historica(actual: dict[str, Any], historico: dict[str, Any]) -> dict[str, Any]:
    comparaciones = {}
    for key in ("valor_facturado", "porcentaje_radicado", "porcentaje_glosa", "saldo_total"):
        if key in actual and key in historico:
            a, h = actual[key], historico[key]
            if isinstance(a, (int, float)) and isinstance(h, (int, float)) and h != 0:
                comparaciones[key] = {"actual": a, "historico": h, "variacion_pct": round(((a - h) / h) * 100, 2)}
    return comparaciones


def ejecutar_herramienta(tool_code: str, datasets: dict[str, list[dict]]) -> dict[str, Any]:
    """Dispatcher de herramientas analíticas por código interno."""
    tools = {
        "salud-facturado-radicado": lambda: analisis_facturado_radicado(
            datasets.get("facturacion", []), datasets.get("radicacion", []),
        ),
        "salud-aging": lambda: analisis_aging(datasets.get("cartera", [])),
        "salud-dias-pago": lambda: analisis_dias_pago(
            datasets.get("cartera", []), datasets.get("pagos", []),
        ),
        "salud-concentracion": lambda: analisis_concentracion(datasets.get("facturacion", [])),
        "salud-glosas": lambda: analisis_glosas(datasets.get("glosas", []), datasets.get("facturacion")),
        "salud-tendencias": lambda: analisis_tendencias(datasets.get("facturacion", [])),
        "salud-anomalias": lambda: analisis_anomalias(datasets.get("facturacion", [])),
        "salud-trazabilidad": lambda: calc_traceability(
            datasets.get("facturacion", []),
            datasets.get("radicacion"),
            datasets.get("glosas"),
            datasets.get("conciliacion"),
            datasets.get("cartera"),
            datasets.get("pagos"),
        ),
        "salud-perfil-datos": lambda: {
            k: profile_data_quality(k, v) for k, v in datasets.items()
        },
        "salud-indicadores": lambda: compute_all_indicators(datasets),
        "salud-contratos": lambda: calc_contratos(datasets.get("contratos", [])),
    }
    fn = tools.get(tool_code)
    if not fn:
        return {"error": f"Herramienta no encontrada: {tool_code}"}
    return fn()
