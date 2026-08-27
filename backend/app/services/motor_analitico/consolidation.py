"""Recomendación consolidada ejecutiva — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def build_consolidated_recommendation(
    *,
    request_text: str,
    indicators: dict[str, Any],
    hallazgos: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    prioritization: dict[str, Any],
    scenarios: dict[str, Any],
    data_sufficiency: dict[str, Any],
    specialists: dict[str, Any],
) -> dict[str, Any]:
    """Responde las 14 preguntas ejecutivas."""
    primary_hyp = next((h for h in hypotheses if h.get("estado") in ("CONFIRMADA", "PROBABLE")), None)
    top_rank = (prioritization.get("ranking") or [{}])[0]
    probable = scenarios.get("escenarios", {}).get("PROBABLE", {})

    demonstrated = [h for h in hypotheses if h.get("estado") == "CONFIRMADA"]
    not_demonstrated = [h for h in hypotheses if h.get("estado") in ("NO DEMOSTRADA", "POSIBLE")]

    car = indicators.get("cartera", {})
    rad = indicators.get("radicacion", {})

    return {
        "que_ocurre": _what_is_happening(hallazgos, primary_hyp),
        "donde": _where(hallazgos, indicators),
        "desde_cuando": _since_when(indicators),
        "cuanto_representa": car.get("saldo_total") if car.get("disponible") else _sum_impact(hallazgos),
        "por_que_podria": primary_hyp.get("titulo") if primary_hyp else INSUFICIENTE,
        "que_demostrado": [h["titulo"] for h in demonstrated] or ["Ninguna causa demostrada — solo asociaciones"],
        "que_no_demostrado": [h["titulo"] for h in not_demonstrated[:5]],
        "oportunidades": [p.get("titulo") for p in prioritization.get("ranking", [])[:5]],
        "alternativas_evaluadas": len(prioritization.get("ranking", [])),
        "recomendacion": top_rank.get("accion") or top_rank.get("titulo") or INSUFICIENTE,
        "por_que_recomendamos": top_rank.get("por_que_primero", ""),
        "cuanto_podria_valer": probable.get("valor_recuperable_estimado", INSUFICIENTE),
        "que_hacer": [r.get("accion") for r in prioritization.get("ranking", [])[:3]],
        "como_medir": _measurement_plan(indicators, top_rank),
        "calidad_datos": data_sufficiency.get("clasificacion"),
        "especialistas_involucrados": len(specialists.get("asignaciones", [])),
        "solicitud": request_text,
    }


def _what_is_happening(hallazgos: list, primary_hyp: dict | None) -> str:
    if not hallazgos and primary_hyp and primary_hyp.get("tipo") == "INSUFICIENTE":
        return "Información insuficiente para diagnosticar con confianza."
    titles = [h.get("title") or h.get("titulo") for h in hallazgos[:3]]
    if primary_hyp:
        return f"{'; '.join(titles)} — hipótesis principal: {primary_hyp.get('titulo')}"
    return "; ".join(titles) if titles else INSUFICIENTE


def _where(hallazgos: list, indicators: dict) -> str:
    domains = sorted({h.get("category") or h.get("categoria") for h in hallazgos if h.get("category") or h.get("categoria")})
    car = indicators.get("cartera", {}).get("por_entidad", {})
    if car:
        top = max(car.items(), key=lambda x: x[1])
        return f"Dominios: {', '.join(domains)}. Mayor exposición: {top[0]}."
    return ", ".join(domains) if domains else INSUFICIENTE


def _since_when(indicators: dict) -> str:
    fact = indicators.get("facturacion", {})
    periods = fact.get("facturacion_por_periodo", {})
    if periods:
        keys = sorted(periods.keys())
        return f"{keys[0]} → {keys[-1]}" if keys else INSUFICIENTE
    return INSUFICIENTE


def _sum_impact(hallazgos: list) -> float | str:
    total = sum(h.get("economic_impact") or 0 for h in hallazgos if isinstance(h.get("economic_impact"), (int, float)))
    return total if total else INSUFICIENTE


def _measurement_plan(indicators: dict, top_rank: dict) -> list[str]:
    plan = []
    if indicators.get("radicacion", {}).get("disponible"):
        plan.append("Días promedio factura→radicación (meta: <7)")
    if indicators.get("glosas", {}).get("disponible"):
        plan.append("Porcentaje de glosa (meta: reducir 5 p.p.)")
    if indicators.get("cartera", {}).get("disponible"):
        plan.append("Saldo cartera 91+ días")
    if top_rank.get("titulo"):
        plan.append(f"Seguimiento acción: {top_rank['titulo'][:80]}")
    return plan or [INSUFICIENTE]
