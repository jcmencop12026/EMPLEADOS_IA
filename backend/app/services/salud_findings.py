"""Generación de hallazgos, propuestas y priorización determinística."""

from __future__ import annotations

import json
from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def _confidence_from_criteria(
    completeness: float,
    consistency: bool,
    case_count: int,
    association_strength: float,
) -> tuple[str, dict[str, Any]]:
    score = 0.0
    criteria: dict[str, Any] = {}

    if completeness >= 0.85:
        score += 0.3
        criteria["completitud"] = "alta"
    elif completeness >= 0.6:
        score += 0.2
        criteria["completitud"] = "media"
    else:
        criteria["completitud"] = "baja"

    criteria["consistencia"] = "si" if consistency else "no"
    if consistency:
        score += 0.25

    if case_count >= 50:
        score += 0.25
        criteria["casos"] = case_count
    elif case_count >= 10:
        score += 0.15
        criteria["casos"] = case_count
    else:
        criteria["casos"] = case_count

    criteria["fuerza_asociacion"] = association_strength
    score += min(association_strength, 0.2)

    if score >= 0.75:
        level = "ALTA"
    elif score >= 0.45:
        level = "MEDIA"
    else:
        level = "BAJA"

    criteria["puntaje"] = round(score, 3)
    return level, criteria


def _priority_score(
    economic_impact: float | None,
    urgency: str,
    recurrence: int,
    confidence: str,
    ease: float = 0.5,
) -> float:
    impact = min((economic_impact or 0) / 1_000_000, 100)
    urgency_map = {"ALTA": 1.0, "MEDIA": 0.6, "BAJA": 0.3}
    conf_map = {"ALTA": 1.0, "MEDIA": 0.7, "BAJA": 0.4}
    return round(
        impact * 0.35
        + urgency_map.get(urgency, 0.5) * 25
        + min(recurrence, 10) * 2
        + conf_map.get(confidence, 0.5) * 15
        + ease * 10,
        2,
    )


def generate_hallazgos(
    indicators: dict[str, Any],
    data_profiles: dict[str, Any],
    employee_id: str | None = None,
) -> list[dict[str, Any]]:
    hallazgos: list[dict[str, Any]] = []

    # Radicación pendiente
    rad = indicators.get("radicacion", {})
    if rad.get("disponible"):
        no_rad = rad.get("facturas_no_radicadas", 0)
        diff = rad.get("diferencia_facturado_radicado")
        if isinstance(no_rad, int) and no_rad > 0:
            completeness = data_profiles.get("radicacion", {}).get("completitud", 0.5)
            conf, crit = _confidence_from_criteria(completeness, True, no_rad, 0.15)
            hallazgos.append({
                "category": "radicacion",
                "title": f"{no_rad} facturas sin radicar",
                "description": f"Existen {no_rad} facturas facturadas sin registro de radicación.",
                "kind": "HECHO",
                "indicator_code": "facturas_no_radicadas",
                "indicator_value": str(no_rad),
                "severity": "ALTA" if no_rad > 5 else "MEDIA",
                "confidence": conf,
                "confidence_criteria": crit,
                "economic_impact": diff if isinstance(diff, (int, float)) else None,
                "probable_cause": None,
                "employee_id": employee_id,
                "sources": [{"dataset": "facturacion+radicacion", "regla": "facturas_no_radicadas"}],
                "evidence": rad.get("evidencia", {}),
            })
        tiempo = rad.get("tiempo_promedio_factura_radicacion_dias")
        if isinstance(tiempo, (int, float)) and tiempo > 7:
            completeness = data_profiles.get("radicacion", {}).get("completitud", 0.5)
            conf, crit = _confidence_from_criteria(completeness, True, int(rad.get("evidencia", {}).get("radicadas", 0)), 0.18)
            hallazgos.append({
                "category": "radicacion",
                "title": f"Demora promedio factura→radicación: {tiempo} días",
                "description": f"El tiempo promedio entre facturación y radicación es {tiempo} días, superior al umbral de 7 días.",
                "kind": "HECHO",
                "indicator_code": "tiempo_factura_radicacion",
                "indicator_value": str(tiempo),
                "severity": "ALTA" if tiempo > 14 else "MEDIA",
                "confidence": conf,
                "confidence_criteria": crit,
                "probable_cause": "Posible demora entre validación RIPS y radicación ante pagador.",
                "employee_id": employee_id,
                "sources": [{"dataset": "radicacion", "calculo": "promedio_dias"}],
                "evidence": {"tiempo_dias": tiempo, "umbral": 7},
            })

    # Glosas
    glosas = indicators.get("glosas", {})
    if glosas.get("disponible"):
        pct = glosas.get("porcentaje_glosa")
        if isinstance(pct, (int, float)) and pct > 5:
            val = glosas.get("valor_glosado", 0)
            completeness = data_profiles.get("glosas", {}).get("completitud", 0.5)
            conf, crit = _confidence_from_criteria(completeness, True, glosas.get("evidencia", {}).get("registros", 0), 0.2)
            hallazgos.append({
                "category": "glosas",
                "title": f"Porcentaje de glosa elevado: {pct}%",
                "description": f"El valor glosado representa el {pct}% de la facturación base (${val:,.0f}).",
                "kind": "HECHO",
                "indicator_code": "porcentaje_glosa",
                "indicator_value": f"{pct}%",
                "severity": "ALTA" if pct > 15 else "MEDIA",
                "confidence": conf,
                "confidence_criteria": crit,
                "economic_impact": val if isinstance(val, (int, float)) else None,
                "probable_cause": _top_causal(glosas.get("por_causal", {})),
                "employee_id": employee_id,
                "sources": [{"dataset": "glosas", "calculo": "porcentaje_glosa"}],
                "evidence": {"por_causal": glosas.get("por_causal", {})},
            })

    # Cartera
    cartera = indicators.get("cartera", {})
    if cartera.get("disponible"):
        aging = cartera.get("aging", {})
        mora_91 = aging.get("91+", 0)
        if isinstance(mora_91, (int, float)) and mora_91 > 0:
            completeness = data_profiles.get("cartera", {}).get("completitud", 0.5)
            conf, crit = _confidence_from_criteria(completeness, True, cartera.get("evidencia", {}).get("registros", 0), 0.15)
            hallazgos.append({
                "category": "cartera",
                "title": f"Cartera vencida 91+ días: ${mora_91:,.0f}",
                "description": f"Existe saldo en mora superior a 91 días por ${mora_91:,.0f}.",
                "kind": "HECHO",
                "indicator_code": "aging_91_mas",
                "indicator_value": f"${mora_91:,.0f}",
                "severity": "ALTA" if mora_91 > 50_000_000 else "MEDIA",
                "confidence": conf,
                "confidence_criteria": crit,
                "economic_impact": mora_91,
                "probable_cause": None,
                "employee_id": employee_id,
                "sources": [{"dataset": "cartera", "calculo": "aging"}],
                "evidence": {"aging": aging},
            })

    # Concentración facturación
    fact = indicators.get("facturacion", {})
    if fact.get("disponible"):
        conc = fact.get("concentracion_principal_pagador_pct")
        if isinstance(conc, (int, float)) and conc > 60:
            completeness = data_profiles.get("facturacion", {}).get("completitud", 0.5)
            conf, crit = _confidence_from_criteria(completeness, True, fact.get("cantidad_facturas", 0), 0.12)
            hallazgos.append({
                "category": "facturacion",
                "title": f"Alta concentración en un pagador: {conc}%",
                "description": f"El pagador principal concentra el {conc}% de la facturación.",
                "kind": "HECHO",
                "indicator_code": "concentracion_pagador",
                "indicator_value": f"{conc}%",
                "severity": "MEDIA",
                "confidence": conf,
                "confidence_criteria": crit,
                "economic_impact": None,
                "probable_cause": "Dependencia comercial elevada en un solo pagador.",
                "employee_id": employee_id,
                "sources": [{"dataset": "facturacion", "calculo": "concentracion"}],
                "evidence": {"por_pagador": fact.get("facturacion_por_pagador", {})},
            })

    for h in hallazgos:
        h["priority_score"] = _priority_score(
            h.get("economic_impact"),
            h.get("severity", "MEDIA"),
            1,
            h.get("confidence", "MEDIA"),
        )

    return sorted(hallazgos, key=lambda x: x.get("priority_score", 0), reverse=True)


def _top_causal(por_causal: dict[str, float]) -> str | None:
    if not por_causal:
        return None
    top = max(por_causal.items(), key=lambda x: x[1])
    pct = round((top[1] / sum(por_causal.values())) * 100, 1) if sum(por_causal.values()) else 0
    return f"{pct}% de glosas asociadas a causal {top[0]}."


def generate_propuestas(hallazgos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    propuestas: list[dict[str, Any]] = []
    actions = {
        "radicacion": ("Coordinador de radicación", "Reducir tiempo factura→radicación a <7 días", "dias_factura_radicacion"),
        "glosas": ("Analista de glosas", "Reducir porcentaje de glosa en 5 puntos", "porcentaje_glosa"),
        "cartera": ("Analista de cartera", "Reducir cartera 91+ en 20%", "aging_91_mas"),
        "facturacion": ("Analista de facturación", "Diversificar cartera de pagadores", "concentracion_pagador"),
    }

    for h in hallazgos:
        cat = h.get("category", "")
        resp, meta, ind = actions.get(cat, ("Coordinador IPS", "Atender hallazgo identificado", "indicador_general"))
        impacto_txt = f"Impacto estimado: ${h['economic_impact']:,.0f}" if h.get("economic_impact") else h.get("description", "")

        propuestas.append({
            "hallazgo_ref": h.get("title"),
            "problema": h.get("title"),
            "evidencia": h.get("description", ""),
            "causa_probable": h.get("probable_cause") or "Requiere validación con equipo operativo.",
            "impacto": impacto_txt,
            "accion_propuesta": _specific_action(cat, h),
            "responsable_sugerido": resp,
            "plazo": "30 días" if h.get("severity") == "ALTA" else "60 días",
            "indicador_seguimiento": ind,
            "meta": meta,
            "impacto_esperado": f"Mitigar {h.get('title', 'hallazgo')}",
            "confianza": h.get("confidence", "MEDIA"),
            "priority_score": h.get("priority_score", 0),
        })

    return propuestas


def _specific_action(category: str, hallazgo: dict[str, Any]) -> str:
    actions_map = {
        "radicacion": "Implementar control diario de facturas pendientes de radicación con alerta a los 5 días y escalamiento al día 10.",
        "glosas": "Revisar causales principales de glosa y ajustar plantillas de respuesta para las 3 causales con mayor valor.",
        "cartera": "Activar gestión de cobro prioritaria para facturas con mora superior a 91 días y negociar acuerdos de pago.",
        "facturacion": "Evaluar diversificación de contratos y revisar dependencia del pagador principal.",
    }
    action = actions_map.get(category)
    if action:
        return action
    return f"Atender hallazgo: {hallazgo.get('title', '')} con plan detallado y responsable asignado."


def build_executive_summary(
    hallazgos: list[dict[str, Any]],
    propuestas: list[dict[str, Any]],
    indicators: dict[str, Any],
) -> dict[str, Any]:
    total_impact = sum(h.get("economic_impact") or 0 for h in hallazgos)
    top_problems = [h["title"] for h in hallazgos[:3]]
    top_actions = [p["accion_propuesta"][:80] for p in propuestas[:3]]

    critical_indicators: dict[str, Any] = {}
    for key in ("facturacion", "radicacion", "glosas", "cartera"):
        ind = indicators.get(key, {})
        if ind.get("disponible"):
            if key == "facturacion":
                critical_indicators["valor_facturado"] = ind.get("valor_facturado")
            elif key == "radicacion":
                critical_indicators["porcentaje_radicado"] = ind.get("porcentaje_radicado")
            elif key == "glosas":
                critical_indicators["porcentaje_glosa"] = ind.get("porcentaje_glosa")
            elif key == "cartera":
                critical_indicators["saldo_total"] = ind.get("saldo_total")
        else:
            critical_indicators[key] = INSUFICIENTE

    return {
        "principales_problemas": top_problems,
        "impacto_acumulado": total_impact if total_impact else INSUFICIENTE,
        "oportunidades_principales": [p["problema"] for p in propuestas[:3]],
        "indicadores_criticos": critical_indicators,
        "acciones_prioritarias": top_actions,
    }
