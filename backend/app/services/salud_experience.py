"""Experiencia IPS: casos, feedback, casos similares y desempeño."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.salud_models import IpsEmployeePerformance, IpsExperienceCase, IpsFeedback


def buscar_casos_similares(
    db: Session,
    org_id: str,
    *,
    tipo_problema: str | None = None,
    indicadores: dict[str, Any] | None = None,
    pagador: str | None = None,
    proceso: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Búsqueda estructurada de casos similares (sin embeddings V1)."""
    query = db.query(IpsExperienceCase).filter(IpsExperienceCase.organization_id == org_id)
    if tipo_problema:
        query = query.filter(IpsExperienceCase.analysis_type.contains(tipo_problema))

    cases = query.order_by(IpsExperienceCase.created_at.desc()).limit(50).all()
    scored: list[tuple[float, IpsExperienceCase]] = []

    for case in cases:
        score = 0.0
        try:
            ctx = json.loads(case.context_json or "{}")
            inds = json.loads(case.indicators_json or "{}")
            hall = json.loads(case.hallazgos_json or "[]")
        except json.JSONDecodeError:
            continue

        if pagador and pagador.lower() in json.dumps(ctx).lower():
            score += 0.3
        if proceso and proceso.lower() in case.analysis_type.lower():
            score += 0.25
        if tipo_problema:
            for h in hall:
                if isinstance(h, dict) and tipo_problema.lower() in str(h.get("category", "")).lower():
                    score += 0.2
                    break

        if indicadores and inds:
            for key, val in indicadores.items():
                if key in inds and inds[key] == val:
                    score += 0.1

        if case.evaluation in ("POSITIVO", "MEJORO"):
            score += 0.15

        if score > 0:
            scored.append((score, case))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": c.id,
            "ips_name": c.ips_name,
            "analysis_type": c.analysis_type,
            "similitud": round(s, 3),
            "hallazgos": json.loads(c.hallazgos_json or "[]"),
            "recomendaciones": json.loads(c.recommendations_json or "[]"),
            "evaluacion": c.evaluation,
            "resultado": c.later_result,
        }
        for s, c in scored[:limit]
    ]


def record_feedback(
    db: Session,
    org_id: str,
    *,
    target_type: str,
    target_id: str,
    feedback_type: str,
    comment: str | None,
    user_id: str,
) -> IpsFeedback:
    fb = IpsFeedback(
        organization_id=org_id,
        target_type=target_type,
        target_id=target_id,
        feedback_type=feedback_type,
        comment=comment,
        user_id=user_id,
    )
    db.add(fb)
    db.flush()
    _update_performance_from_feedback(db, org_id, target_type, target_id, feedback_type)
    return fb


def _update_performance_from_feedback(
    db: Session, org_id: str, target_type: str, target_id: str, feedback_type: str,
) -> None:
    if target_type != "hallazgo":
        return
    from app.salud_models import IpsHallazgo
    hallazgo = db.query(IpsHallazgo).filter(IpsHallazgo.id == target_id).first()
    if not hallazgo or not hallazgo.employee_id:
        return

    perf = (
        db.query(IpsEmployeePerformance)
        .filter(
            IpsEmployeePerformance.organization_id == org_id,
            IpsEmployeePerformance.employee_id == hallazgo.employee_id,
        )
        .first()
    )
    if not perf:
        from app.orchestration_models import AIEmployee
        emp = db.query(AIEmployee).filter(AIEmployee.id == hallazgo.employee_id).first()
        perf = IpsEmployeePerformance(
            organization_id=org_id,
            employee_id=hallazgo.employee_id,
            specialty=emp.specialty if emp else "IPS",
            metrics_json=json.dumps({
                "analisis_realizados": 0,
                "hallazgos_aceptados": 0,
                "hallazgos_rechazados": 0,
                "tasa_aceptacion": 0.5,
                "resultados_positivos": 0,
            }),
        )
        db.add(perf)
        db.flush()

    metrics = json.loads(perf.metrics_json or "{}")
    if feedback_type in ("CORRECTO", "ACCION_ACEPTADA"):
        metrics["hallazgos_aceptados"] = metrics.get("hallazgos_aceptados", 0) + 1
    elif feedback_type in ("INCORRECTO", "ACCION_DESCARTADA"):
        metrics["hallazgos_rechazados"] = metrics.get("hallazgos_rechazados", 0) + 1

    total = metrics.get("hallazgos_aceptados", 0) + metrics.get("hallazgos_rechazados", 0)
    if total > 0:
        metrics["tasa_aceptacion"] = round(metrics.get("hallazgos_aceptados", 0) / total, 3)
    perf.metrics_json = json.dumps(metrics, ensure_ascii=False)


def save_experience_case(
    db: Session,
    org_id: str,
    *,
    ips_name: str,
    analysis_type: str,
    analysis_id: str | None,
    context: dict,
    indicators: dict,
    hallazgos: list,
    recommendations: list,
    employee_ids: list[str],
    human_decision: str | None = None,
) -> IpsExperienceCase:
    case = IpsExperienceCase(
        organization_id=org_id,
        ips_name=ips_name,
        analysis_type=analysis_type,
        analysis_id=analysis_id,
        context_json=json.dumps(context, ensure_ascii=False),
        indicators_json=json.dumps(indicators, ensure_ascii=False),
        hallazgos_json=json.dumps(hallazgos, ensure_ascii=False),
        recommendations_json=json.dumps(recommendations, ensure_ascii=False),
        employee_ids_json=json.dumps(employee_ids, ensure_ascii=False),
        human_decision=human_decision,
    )
    db.add(case)
    db.flush()

    for emp_id in employee_ids:
        perf = (
            db.query(IpsEmployeePerformance)
            .filter(IpsEmployeePerformance.organization_id == org_id, IpsEmployeePerformance.employee_id == emp_id)
            .first()
        )
        if perf:
            metrics = json.loads(perf.metrics_json or "{}")
            metrics["analisis_realizados"] = metrics.get("analisis_realizados", 0) + 1
            perf.metrics_json = json.dumps(metrics, ensure_ascii=False)

    return case


def get_employee_performance(db: Session, org_id: str, employee_id: str | None = None) -> list[dict[str, Any]]:
    query = db.query(IpsEmployeePerformance).filter(IpsEmployeePerformance.organization_id == org_id)
    if employee_id:
        query = query.filter(IpsEmployeePerformance.employee_id == employee_id)
    rows = query.all()
    return [
        {
            "employee_id": r.employee_id,
            "specialty": r.specialty,
            "metricas": json.loads(r.metrics_json or "{}"),
        }
        for r in rows
    ]
