"""Pipeline transversal MOTOR-ANALITICO-1000 — orquesta sin duplicar SALUD."""

from __future__ import annotations

from typing import Any

from app.services.motor_analitico.alternatives import generate_alternatives
from app.services.motor_analitico.consolidation import build_consolidated_recommendation
from app.services.motor_analitico.contrast import build_contrasts
from app.services.motor_analitico.data_sufficiency import assess_data_sufficiency
from app.services.motor_analitico.finops_bridge import estimate_finops_values
from app.services.motor_analitico.hypothesis_engine import generate_hypotheses, primary_hypothesis
from app.services.motor_analitico.prioritization import prioritize_opportunities
from app.services.motor_analitico.scenarios import simulate_scenarios


def run_motor_analitico(
    *,
    datasets: dict[str, list[dict]],
    data_profiles: dict[str, Any],
    indicators: dict[str, Any],
    hallazgos: list[dict[str, Any]],
    propuestas: list[dict[str, Any]],
    specialists: dict[str, Any],
    request_text: str,
    knowledge_ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ejecuta etapas del motor analítico sobre resultados SALUD existentes."""
    sufficiency = assess_data_sufficiency(data_profiles, indicators, request_text)
    hypotheses = generate_hypotheses(indicators, datasets, sufficiency, hallazgos)
    primary = primary_hypothesis(hypotheses)
    contrasts = build_contrasts(hypotheses, specialists, hallazgos)
    alternatives = generate_alternatives(hallazgos, hypotheses, indicators)
    scenarios = simulate_scenarios(indicators, hypotheses, propuestas[0] if propuestas else None)
    finops = estimate_finops_values(propuestas, scenarios, hypotheses)
    prioritization = prioritize_opportunities(propuestas, alternatives, hypotheses, finops)
    recommendation = build_consolidated_recommendation(
        request_text=request_text,
        indicators=indicators,
        hallazgos=hallazgos,
        hypotheses=hypotheses,
        prioritization=prioritization,
        scenarios=scenarios,
        data_sufficiency=sufficiency,
        specialists=specialists,
    )

    # Re-rank propuestas según motor
    rank_map = {
        r.get("titulo"): r.get("prioridad", 0)
        for r in prioritization.get("ranking", [])
        if r.get("tipo") == "propuesta"
    }
    for p in propuestas:
        ref = p.get("problema") or p.get("hallazgo_ref")
        if ref in rank_map:
            p["priority_score"] = rank_map[ref]
            p["motor_prioridad"] = rank_map[ref]
            p["por_que_primero"] = next(
                (r["por_que_primero"] for r in prioritization["ranking"] if r.get("titulo") == ref),
                None,
            )

    propuestas.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

    trace = {
        "motor": "MOTOR-ANALITICO-1000",
        "solicitud": request_text,
        "suficiencia": sufficiency["clasificacion"],
        "hipotesis_principal": primary.get("id") if primary else None,
        "especialistas": _specialist_trace(specialists),
        "contrastes_count": len(contrasts),
        "alternativas_count": len(alternatives),
        "conocimiento": knowledge_ctx or {},
    }

    return {
        "suficiencia_datos": sufficiency,
        "hipotesis": hypotheses,
        "hipotesis_principal": primary,
        "contrastes": contrasts,
        "alternativas": alternatives,
        "priorizacion": prioritization,
        "escenarios": scenarios,
        "finops": finops,
        "recomendacion_consolidada": recommendation,
        "trazabilidad_motor": trace,
    }


def _specialist_trace(specialists: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for a in specialists.get("asignaciones", []):
        factors = a.get("factors", {})
        top_factor = max(factors.items(), key=lambda x: x[1])[0] if factors else "capacidades"
        items.append({
            "nombre": a.get("employee_name"),
            "dominio": a.get("domain"),
            "score": a.get("score"),
            "razon_seleccion": f"Mayor puntaje en {a.get('domain')} por {top_factor} ({factors.get(top_factor, 0)})",
            "factores": factors,
        })
    if specialists.get("consolidador"):
        c = specialists["consolidador"]
        items.append({
            "nombre": c.get("employee_name"),
            "dominio": "consolidador",
            "score": c.get("score"),
            "razon_seleccion": "Consolidador estratégico con mayor puntaje en dominio estratégico",
            "factores": c.get("factors"),
        })
    return items


def fingerprint_motor_result(motor: dict[str, Any]) -> dict[str, Any]:
    """Huella para test anti-prefabricado."""
    hyp = motor.get("hipotesis_principal") or {}
    ranking = motor.get("priorizacion", {}).get("ranking", [])
    return {
        "hipotesis_principal_id": hyp.get("id"),
        "hipotesis_principal_titulo": hyp.get("titulo"),
        "top_ranking_titulos": [r.get("titulo") for r in ranking[:3]],
        "suficiencia": motor.get("suficiencia_datos", {}).get("clasificacion"),
        "finops_total": sum(
            f.get("beneficio_esperado") or 0
            for f in motor.get("finops", [])
            if isinstance(f.get("beneficio_esperado"), (int, float))
        ),
    }
