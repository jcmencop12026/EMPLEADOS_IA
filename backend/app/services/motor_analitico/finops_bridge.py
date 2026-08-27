"""Puente FINOPS — estimación de valor sin confundir con resultado real."""

from __future__ import annotations

from decimal import Decimal
from decimal import Decimal
from typing import Any

from app.services.salud_indicators import INSUFICIENTE


def estimate_finops_values(
    propuestas: list[dict[str, Any]],
    scenarios: dict[str, Any],
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Estima costo/beneficio/ROI para propuestas — REAL/ESTIMADO/PROYECTADO."""
    probable = scenarios.get("escenarios", {}).get("PROBABLE", {})
    recovery = probable.get("valor_recuperable_estimado")
    estimates: list[dict[str, Any]] = []

    for i, p in enumerate(propuestas):
        ref = p.get("problema") or p.get("hallazgo_ref")
        impact = _numeric(p.get("economic_impact") or p.get("impacto"))
        benefit = recovery if i == 0 and isinstance(recovery, (int, float)) else impact * 0.15 if impact else None
        cost = _estimate_cost(p.get("plazo"), p.get("responsable_sugerido"))
        roi = round((benefit - cost) / cost, 2) if benefit and cost and cost > 0 else None
        payback_days = _payback_days(p.get("plazo"))

        estimates.append({
            "referencia": ref,
            "costo_estimado": cost,
            "beneficio_esperado": benefit,
            "valor_recuperable": benefit,
            "ahorro": benefit,
            "roi": roi,
            "payback_dias": payback_days,
            "certidumbre": "ESTIMADO" if benefit else "NO CUANTIFICABLE",
            "metodologia": "Beneficio = impacto económico del hallazgo × tasa de escenario probable",
            "advertencia": "Estimación — no presentar como resultado real.",
        })

    return estimates


def register_finops_values(
    db,
    *,
    organization_id: str,
    user_id: str,
    analysis_id: str,
    estimates: list[dict[str, Any]],
    work_plan_id: str | None = None,
    opportunity_id: str | None = None,
    employee_id: str | None = None,
) -> list[str]:
    """Registra valores estimados en FINOPS cuando es cuantificable — G-02."""
    from app.services.finops_service import registrar_valor

    ids: list[str] = []
    for est in estimates:
        amount = est.get("beneficio_esperado")
        if not isinstance(amount, (int, float)) or amount <= 0:
            continue
        row = registrar_valor(
            db,
            organization_id=organization_id,
            user_id=user_id,
            employee_id=employee_id,
            work_plan_id=work_plan_id,
            value_type=est.get("value_type", "valor_recuperable_ips"),
            certainty=est.get("certidumbre", "Estimado"),
            amount=Decimal(str(round(amount, 2))),
            currency="COP",
            methodology=est.get("metodologia"),
            source=est.get("source") or f"motor_analitico:{analysis_id}",
            notes=est.get("referencia"),
        )
        if opportunity_id:
            row.opportunity_id = opportunity_id
        ids.append(row.id)
    return ids


def _numeric(val: Any) -> float | None:
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        digits = "".join(c if c.isdigit() else " " for c in val).split()
        if digits:
            try:
                return float(digits[0])
            except ValueError:
                return None
    return None


def _estimate_cost(plazo: str | None, responsable: str | None) -> float:
    base = 2_500_000
    if plazo and "90" in plazo:
        return base * 2.5
    if plazo and "60" in plazo:
        return base * 1.8
    if responsable and "outsourcing" in (responsable or "").lower():
        return base * 3
    return base


def _payback_days(plazo: str | None) -> int | str:
    if not plazo:
        return INSUFICIENTE
    for d in (15, 21, 30, 45, 60, 90):
        if str(d) in plazo:
            return d + 30
    return 90
