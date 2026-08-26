"""Ideación multiagente — alternativas por hallazgo."""

from __future__ import annotations

from typing import Any


def generate_alternatives(
    hallazgos: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    indicators: dict[str, Any],
) -> list[dict[str, Any]]:
    """Genera alternativas diferenciadas — no aceptar la primera propuesta."""
    alternatives: list[dict[str, Any]] = []
    primary_hyp = next((h for h in hypotheses if h.get("estado") in ("CONFIRMADA", "PROBABLE")), None)

    for h in hallazgos[:5]:
        cat = h.get("category", "general")
        base_impact = h.get("economic_impact") or 0
        alts = _alternatives_for_category(cat, h, indicators, primary_hyp)
        for i, alt in enumerate(alts):
            alternatives.append({
                "hallazgo_ref": h.get("title"),
                "alternativa_id": f"ALT-{cat[:3].upper()}-{i+1}",
                "descripcion": alt["descripcion"],
                "fundamento": alt["fundamento"],
                "impacto_esperado": alt.get("impacto_esperado", base_impact),
                "costo_estimado": alt.get("costo", "MEDIO"),
                "esfuerzo": alt.get("esfuerzo", "MEDIO"),
                "plazo": alt.get("plazo", "60 días"),
                "riesgo": alt.get("riesgo", "MEDIO"),
                "dependencias": alt.get("dependencias", []),
                "reversibilidad": alt.get("reversibilidad", "ALTA"),
                "evidencia": h.get("evidence", {}),
                "confianza": h.get("confidence", "MEDIA"),
                "tipo": "RECOMENDACION",
            })

    return alternatives


def _alternatives_for_category(
    cat: str,
    hallazgo: dict,
    indicators: dict,
    primary_hyp: dict | None,
) -> list[dict[str, Any]]:
    templates: dict[str, list[dict]] = {
        "radicacion": [
            {
                "descripcion": "Control diario de pendientes de radicación con alertas automáticas",
                "fundamento": "Reduce demora factura→radicación identificada en indicadores",
                "impacto_esperado": hallazgo.get("economic_impact"),
                "costo": "BAJO", "esfuerzo": "BAJO", "plazo": "30 días", "riesgo": "BAJO",
                "dependencias": ["Equipo de radicación"],
            },
            {
                "descripcion": "Auditoría de cuellos de botella entre facturación y radicación",
                "fundamento": "Identifica si la demora es de validación RIPS o envío al pagador",
                "costo": "MEDIO", "esfuerzo": "MEDIO", "plazo": "45 días", "riesgo": "BAJO",
                "dependencias": ["TI", "Facturación"],
            },
            {
                "descripcion": "Outsourcing parcial de radicación para picos de volumen",
                "fundamento": "Alternativa si capacidad interna es el limitante",
                "costo": "ALTO", "esfuerzo": "ALTO", "plazo": "90 días", "riesgo": "MEDIO",
                "reversibilidad": "MEDIA",
            },
        ],
        "glosas": [
            {
                "descripcion": "Plantillas de respuesta para las 3 causales con mayor valor glosado",
                "fundamento": "Ataca concentración de glosas por causal",
                "impacto_esperado": hallazgo.get("economic_impact"),
                "costo": "BAJO", "esfuerzo": "MEDIO", "plazo": "30 días",
            },
            {
                "descripcion": "Comité semanal glosas-devoluciones con trazabilidad por factura",
                "fundamento": "Integra devoluciones y respuestas en un solo flujo",
                "costo": "MEDIO", "esfuerzo": "MEDIO", "plazo": "60 días",
            },
            {
                "descripcion": "Capacitación en codificación y soportes para servicios más glosados",
                "fundamento": "Reduce glosas por soporte deficiente (H5)",
                "costo": "MEDIO", "esfuerzo": "ALTO", "plazo": "90 días", "riesgo": "BAJO",
            },
        ],
        "cartera": [
            {
                "descripcion": "Gestión prioritaria de cartera 91+ con negociación por pagador",
                "fundamento": "Impacto directo en flujo de caja",
                "impacto_esperado": hallazgo.get("economic_impact"),
                "costo": "BAJO", "esfuerzo": "MEDIO", "plazo": "30 días",
            },
            {
                "descripcion": "Seguimiento contractual con pagadores de mayor mora",
                "fundamento": "H7 — comportamiento del pagador cuando proceso interno es sólido",
                "costo": "MEDIO", "esfuerzo": "MEDIO", "plazo": "45 días",
                "dependencias": ["Jurídico", "Cartera"],
            },
            {
                "descripcion": "Factoring selectivo de cartera con pagadores de riesgo bajo",
                "fundamento": "Liquidez inmediata con costo financiero",
                "costo": "ALTO", "esfuerzo": "BAJO", "plazo": "15 días", "riesgo": "MEDIO",
                "reversibilidad": "BAJA",
            },
        ],
        "facturacion": [
            {
                "descripcion": "Plan de diversificación de cartera de pagadores",
                "fundamento": "Reduce concentración identificada",
                "costo": "ALTO", "esfuerzo": "ALTO", "plazo": "180 días",
            },
            {
                "descripcion": "Renegociación de volumen con pagador principal",
                "fundamento": "Mantiene relación pero mejora condiciones",
                "costo": "MEDIO", "esfuerzo": "MEDIO", "plazo": "90 días",
            },
        ],
    }

    alts = list(templates.get(cat, []))
    if primary_hyp and primary_hyp.get("dominio") == "pagador" and cat == "cartera":
        alts.insert(0, {
            "descripcion": "Mesa de trabajo con pagador de mayor mora y evidencia de radicación oportuna",
            "fundamento": primary_hyp.get("titulo", "Comportamiento del pagador"),
            "impacto_esperado": hallazgo.get("economic_impact"),
            "costo": "BAJO", "esfuerzo": "BAJO", "plazo": "21 días",
        })
    if not alts:
        alts = [{
            "descripcion": f"Plan de acción para: {hallazgo.get('title', 'hallazgo')}",
            "fundamento": hallazgo.get("description", ""),
            "costo": "MEDIO", "esfuerzo": "MEDIO", "plazo": "60 días",
        }]
    return alts[:3]
