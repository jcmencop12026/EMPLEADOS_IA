"""Priorización documentada — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any

METHODOLOGY = (
    "prioridad = impacto_económico(35%) + urgencia(25%) + confianza(15%) "
    "+ esfuerzo_inverso(10%) + recuperabilidad(10%) + riesgo_inverso(5%)"
)


def prioritize_opportunities(
    propuestas: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    finops: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prioriza oportunidades con metodología explicable."""
    items: list[dict[str, Any]] = []

    finops_by_ref = {f.get("referencia"): f for f in finops}

    for p in propuestas:
        score, breakdown = _score_item(
            economic=_parse_impact(p.get("impacto_esperado") or p.get("impacto")),
            urgency=_urgency_from_plazo(p.get("plazo")),
            confidence=p.get("confianza", "MEDIA"),
            effort="MEDIO",
            recoverability=_recoverability(p, hypotheses),
            risk="MEDIO",
        )
        fin = finops_by_ref.get(p.get("problema") or p.get("hallazgo_ref"))
        items.append({
            "tipo": "propuesta",
            "id": p.get("hallazgo_ref") or p.get("problema"),
            "titulo": p.get("problema"),
            "accion": p.get("accion_propuesta"),
            "prioridad": round(score, 2),
            "desglose": breakdown,
            "finops": fin,
            "por_que_primero": _why_first(breakdown, p.get("problema", "")),
        })

    for a in alternatives[:6]:
        score, breakdown = _score_item(
            economic=a.get("impacto_esperado") if isinstance(a.get("impacto_esperado"), (int, float)) else 0,
            urgency=_urgency_from_plazo(a.get("plazo")),
            confidence=a.get("confianza", "MEDIA"),
            effort=a.get("esfuerzo", "MEDIO"),
            recoverability=0.6,
            risk=a.get("riesgo", "MEDIO"),
        )
        items.append({
            "tipo": "alternativa",
            "id": a.get("alternativa_id"),
            "titulo": a.get("descripcion"),
            "accion": a.get("descripcion"),
            "prioridad": round(score, 2),
            "desglose": breakdown,
            "por_que_primero": _why_first(breakdown, a.get("descripcion", "")),
        })

    items.sort(key=lambda x: x["prioridad"], reverse=True)
    for i, item in enumerate(items):
        item["ranking"] = i + 1

    return {
        "metodologia": METHODOLOGY,
        "ranking": items,
        "explicacion": "El ranking no es una suma arbitraria: cada factor tiene peso documentado en 'metodologia'.",
    }


def _score_item(
    *,
    economic: float,
    urgency: float,
    confidence: str,
    effort: str,
    recoverability: float,
    risk: str,
) -> tuple[float, dict[str, float]]:
    conf_map = {"ALTA": 1.0, "MEDIA": 0.7, "BAJA": 0.4}
    effort_map = {"BAJO": 1.0, "MEDIO": 0.6, "ALTO": 0.3}
    risk_map = {"BAJO": 1.0, "MEDIO": 0.6, "ALTO": 0.3}

    impact_norm = min(economic / 50_000_000, 1.0) if economic > 0 else 0.2

    breakdown = {
        "impacto_economico": round(impact_norm * 35, 2),
        "urgencia": round(urgency * 25, 2),
        "confianza": round(conf_map.get(confidence, 0.5) * 15, 2),
        "esfuerzo_inverso": round(effort_map.get(effort, 0.5) * 10, 2),
        "recuperabilidad": round(recoverability * 10, 2),
        "riesgo_inverso": round(risk_map.get(risk, 0.5) * 5, 2),
    }
    return sum(breakdown.values()), breakdown


def _urgency_from_plazo(plazo: str | None) -> float:
    if not plazo:
        return 0.5
    text = plazo.lower()
    if "15" in text or "21" in text or "30" in text:
        return 1.0
    if "45" in text or "60" in text:
        return 0.7
    return 0.4


def _recoverability(propuesta: dict, hypotheses: list[dict]) -> float:
    primary = next((h for h in hypotheses if h.get("estado") in ("CONFIRMADA", "PROBABLE")), None)
    if not primary:
        return 0.4
    cat = propuesta.get("problema", "").lower()
    if primary.get("dominio", "") in cat or primary.get("titulo", "").lower() in cat:
        return 0.85
    return 0.55


def _parse_impact(text: Any) -> float:
    if isinstance(text, (int, float)):
        return float(text)
    if isinstance(text, str):
        digits = "".join(c if c.isdigit() else " " for c in text).split()
        if digits:
            try:
                return float(digits[0])
            except ValueError:
                pass
    return 0.0


def _why_first(breakdown: dict[str, float], titulo: str) -> str:
    top_factor = max(breakdown.items(), key=lambda x: x[1])
    labels = {
        "impacto_economico": "alto impacto económico",
        "urgencia": "urgencia operativa",
        "confianza": "confianza en la evidencia",
        "esfuerzo_inverso": "bajo esfuerzo relativo",
        "recuperabilidad": "alta recuperabilidad de valor",
        "riesgo_inverso": "riesgo controlado",
    }
    return f"'{titulo[:60]}' prioriza por {labels.get(top_factor[0], top_factor[0])} ({top_factor[1]} pts)."
