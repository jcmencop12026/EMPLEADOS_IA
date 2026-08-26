"""Contraste entre especialistas — MOTOR-ANALITICO-1000."""

from __future__ import annotations

from typing import Any


def build_contrasts(
    hypotheses: list[dict[str, Any]],
    specialists: dict[str, Any],
    hallazgos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Especialistas APOYAN / CUESTIONAN / REFUTAN / COMPLEMENTAN hipótesis."""
    contrasts: list[dict[str, Any]] = []
    assignments = specialists.get("asignaciones", [])
    consolidador = specialists.get("consolidador")

    domain_to_specialist = {a["domain"]: a for a in assignments}
    top_hypotheses = [h for h in hypotheses if h.get("estado") not in ("REFUTADA",)][:5]

    for hyp in top_hypotheses:
        domain = hyp.get("dominio", "estrategico")
        spec = domain_to_specialist.get(domain) or domain_to_specialist.get("estrategico")
        if not spec and assignments:
            spec = assignments[0]
        if not spec:
            continue

        stance, argument = _stance_for_hypothesis(hyp, hallazgos)
        contrasts.append({
            "hipotesis_id": hyp["id"],
            "hipotesis_titulo": hyp["titulo"],
            "especialista": spec.get("employee_name"),
            "employee_id": spec.get("employee_id"),
            "dominio": domain,
            "postura": stance,
            "argumento": argument,
            "evidencia_citada": hyp.get("evidencia_a_favor", [])[:2],
        })

        # Segundo especialista con postura complementaria o de contraste
        other = _pick_counter_specialist(assignments, domain)
        if other:
            alt_stance = "COMPLEMENTAR" if stance == "APOYAR" else "CUESTIONAR"
            contrasts.append({
                "hipotesis_id": hyp["id"],
                "hipotesis_titulo": hyp["titulo"],
                "especialista": other.get("employee_name"),
                "employee_id": other.get("employee_id"),
                "dominio": other.get("domain"),
                "postura": alt_stance,
                "argumento": _counter_argument(hyp, alt_stance),
                "evidencia_citada": hyp.get("evidencia_en_contra", [])[:1] or hyp.get("informacion_faltante", [])[:1],
            })

    if consolidador and top_hypotheses:
        primary = top_hypotheses[0]
        contrasts.append({
            "hipotesis_id": primary["id"],
            "hipotesis_titulo": primary["titulo"],
            "especialista": consolidador.get("employee_name"),
            "employee_id": consolidador.get("employee_id"),
            "dominio": "consolidacion",
            "postura": "COMPLEMENTAR",
            "argumento": (
                f"Consolidador recibe {len(contrasts)} intervenciones de especialistas "
                f"sobre '{primary['titulo']}' — síntesis requerida antes de recomendar."
            ),
            "evidencia_citada": [],
            "rol": "CONSOLIDADOR",
        })

    return contrasts


def _stance_for_hypothesis(hyp: dict, hallazgos: list[dict]) -> tuple[str, str]:
    estado = hyp.get("estado", "")
    if estado == "CONFIRMADA":
        return "APOYAR", f"Evidencia consistente: {'; '.join(hyp.get('evidencia_a_favor', [])[:2])}"
    if estado == "PROBABLE":
        return "APOYAR", f"Hipótesis probable con reservas: {hyp.get('titulo')}"
    if estado == "REFUTADA":
        return "REFUTAR", f"Evidencia en contra: {'; '.join(hyp.get('evidencia_en_contra', [])[:2])}"
    if hyp.get("informacion_faltante"):
        return "CUESTIONAR", "Información faltante impide confirmar — no convertir correlación en causalidad."
    matching = [h for h in hallazgos if h.get("category") == hyp.get("dominio")]
    if matching:
        return "COMPLEMENTAR", f"Hallazgo relacionado: {matching[0].get('title', '')}"
    return "CUESTIONAR", "Asociación débil — requiere más datos."


def _pick_counter_specialist(assignments: list[dict], exclude_domain: str) -> dict | None:
    for a in assignments:
        if a.get("domain") != exclude_domain:
            return a
    return None


def _counter_argument(hyp: dict, stance: str) -> str:
    if stance == "CUESTIONAR":
        missing = hyp.get("informacion_faltante", [])
        if missing:
            return f"Falta: {missing[0] if isinstance(missing[0], str) else missing[0].get('que_falta', '')}"
        return "La correlación observada no demuestra causalidad directa."
    return f"Complementa con acciones en dominio {hyp.get('dominio')}."
