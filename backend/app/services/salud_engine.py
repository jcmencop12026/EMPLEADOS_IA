"""Motor principal de análisis IPS — pipeline completo."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.salud_models import (
    IpsActionPlan,
    IpsAnalysis,
    IpsDataset,
    IpsHallazgo,
    IpsHistoricalProfile,
    IpsPropuesta,
)
from app.services.salud_experience import save_experience_case
from app.services.salud_findings import build_executive_summary, generate_hallazgos, generate_propuestas
from app.services.salud_indicators import compute_all_indicators
from app.services.salud_knowledge import (
    apply_knowledge_to_hallazgos,
    collect_analysis_knowledge,
    log_salud_knowledge_audit,
)
from app.services.salud_normalization import profile_data_quality
from app.services.salud_specialist_selection import select_specialists
from app.services.salud_workplan_bridge import (
    bridge_action_plan_to_workplan,
    find_idempotent_action_plan,
    normalize_propuesta_ids,
)
from app.services.motor_analitico.pipeline import run_motor_analitico
from app.services.motor_analitico.finops_bridge import register_finops_values


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_datasets_for_analysis(db: Session, org_id: str, dataset_ids: list[str] | None = None) -> dict[str, list[dict]]:
    query = db.query(IpsDataset).filter(IpsDataset.organization_id == org_id)
    if dataset_ids:
        query = query.filter(IpsDataset.id.in_(dataset_ids))
    datasets: dict[str, list[dict]] = {}
    for ds in query.all():
        try:
            records = json.loads(ds.data_json or "[]")
        except json.JSONDecodeError:
            records = []
        datasets[ds.source_type] = records
    return datasets


def profile_all_sources(datasets: dict[str, list[dict]]) -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    for source_type, records in datasets.items():
        profiles[source_type] = profile_data_quality(source_type, records)
    return profiles


def determine_available_analyses(datasets: dict[str, list[dict]]) -> dict[str, Any]:
    available = []
    unavailable = []

    checks = {
        "facturacion": ["facturacion"],
        "radicacion": ["facturacion", "radicacion"],
        "glosas": ["glosas"],
        "cartera": ["cartera"],
        "contratos": ["contratos"],
        "trazabilidad": ["facturacion"],
        "comparacion_historica": ["facturacion"],
    }

    for analysis, required in checks.items():
        if all(r in datasets and datasets[r] for r in required):
            available.append(analysis)
        else:
            missing = [r for r in required if r not in datasets or not datasets[r]]
            unavailable.append({"analisis": analysis, "faltante": missing})

    return {"puede_realizar": available, "no_puede_realizar": unavailable}


def run_ips_analysis(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    ips_name: str,
    request_text: str,
    dataset_ids: list[str] | None = None,
    inline_datasets: dict[str, list[dict]] | None = None,
) -> IpsAnalysis:
    """Ejecuta pipeline: datos → normalización → indicadores → hallazgos → propuestas."""
    analysis = IpsAnalysis(
        organization_id=organization_id,
        ips_name=ips_name,
        request_text=request_text,
        status="EJECUTANDO",
        created_by_id=user_id,
    )
    db.add(analysis)
    db.flush()

    if inline_datasets:
        datasets = inline_datasets
    else:
        datasets = load_datasets_for_analysis(db, organization_id, dataset_ids)

    data_profiles = profile_all_sources(datasets)
    available = determine_available_analyses(datasets)
    specialists = select_specialists(
        db, organization_id, request_text, list(datasets.keys()),
    )

    knowledge_ctx = collect_analysis_knowledge(
        db,
        organization_id=organization_id,
        analysis_id=analysis.id,
        user_id=user_id,
        request_text=request_text,
        ips_name=ips_name,
        specialists=specialists,
    )

    indicators = compute_all_indicators(datasets)

    # Asignar hallazgos por especialista según dominio
    all_hallazgos: list[dict[str, Any]] = []
    specialist_map = {a["domain"]: a["employee_id"] for a in specialists.get("asignaciones", [])}

    for domain in ("radicacion", "glosas", "cartera", "facturacion"):
        domain_indicators = {domain: indicators.get(domain, {}), **{k: indicators[k] for k in ("facturacion",) if k in indicators}}
        emp_id = specialist_map.get(domain)
        domain_profiles = {k: v for k, v in data_profiles.items() if k == domain or k == "facturacion"}
        all_hallazgos.extend(generate_hallazgos(domain_indicators, domain_profiles, emp_id))

    # Deduplicar por título
    seen_titles: set[str] = set()
    unique_hallazgos: list[dict[str, Any]] = []
    for h in all_hallazgos:
        if h["title"] not in seen_titles:
            seen_titles.add(h["title"])
            unique_hallazgos.append(h)

    unique_hallazgos = apply_knowledge_to_hallazgos(unique_hallazgos, knowledge_ctx, indicators)

    propuestas = generate_propuestas(unique_hallazgos)

    motor = run_motor_analitico(
        datasets=datasets,
        data_profiles=data_profiles,
        indicators=indicators,
        hallazgos=unique_hallazgos,
        propuestas=propuestas,
        specialists=specialists,
        request_text=request_text or "",
        knowledge_ctx=knowledge_ctx,
    )

    summary = build_executive_summary(unique_hallazgos, propuestas, indicators)

    # Comparación histórica
    historical = _compare_historical(db, organization_id, ips_name, indicators)

    # Persistir hallazgos
    persisted_hallazgos: list[IpsHallazgo] = []
    for h in unique_hallazgos:
        hallazgo = IpsHallazgo(
            organization_id=organization_id,
            analysis_id=analysis.id,
            employee_id=h.get("employee_id"),
            category=h["category"],
            title=h["title"],
            description=h["description"],
            kind=h.get("kind", "HECHO"),
            evidence_json=json.dumps(h.get("evidence", {}), ensure_ascii=False),
            indicator_code=h.get("indicator_code"),
            indicator_value=h.get("indicator_value"),
            severity=h.get("severity", "MEDIA"),
            priority_score=h.get("priority_score"),
            confidence=h.get("confidence", "MEDIA"),
            confidence_criteria_json=json.dumps(h.get("confidence_criteria", {}), ensure_ascii=False),
            probable_cause=h.get("probable_cause"),
            economic_impact=h.get("economic_impact"),
            sources_json=json.dumps(h.get("sources", []), ensure_ascii=False),
        )
        db.add(hallazgo)
        persisted_hallazgos.append(hallazgo)

    db.flush()

    # Persistir propuestas
    persisted_propuestas: list[IpsPropuesta] = []
    for i, p in enumerate(propuestas):
        hallazgo_id = persisted_hallazgos[i].id if i < len(persisted_hallazgos) else None
        prop = IpsPropuesta(
            organization_id=organization_id,
            analysis_id=analysis.id,
            hallazgo_id=hallazgo_id,
            problema=p["problema"],
            evidencia=p["evidencia"],
            causa_probable=p.get("causa_probable"),
            impacto=p["impacto"],
            accion_propuesta=p["accion_propuesta"],
            responsable_sugerido=p.get("responsable_sugerido"),
            plazo=p.get("plazo"),
            indicador_seguimiento=p.get("indicador_seguimiento"),
            meta=p.get("meta"),
            impacto_esperado=p.get("impacto_esperado"),
            confianza=p.get("confianza", "MEDIA"),
            priority_score=p.get("priority_score"),
        )
        db.add(prop)
        persisted_propuestas.append(prop)

    db.flush()

    # Actualizar perfil histórico
    _update_historical(db, organization_id, ips_name, indicators)

    employee_ids = list({a["employee_id"] for a in specialists.get("asignaciones", [])})
    if specialists.get("consolidador"):
        employee_ids.append(specialists["consolidador"]["employee_id"])

    analysis.status = "COMPLETADO"
    analysis.completed_at = _utcnow()
    analysis.data_profile_json = json.dumps(data_profiles, ensure_ascii=False)
    analysis.available_analyses_json = json.dumps(available, ensure_ascii=False)
    analysis.indicators_json = json.dumps(indicators, ensure_ascii=False)
    analysis.traceability_json = json.dumps(
        {
            **indicators.get("trazabilidad", {}),
            "conocimiento": knowledge_ctx,
            "motor": motor.get("trazabilidad_motor", {}),
        },
        ensure_ascii=False,
    )
    analysis.specialists_json = json.dumps(specialists, ensure_ascii=False)
    analysis.summary_json = json.dumps({
        "resumen_ejecutivo": summary,
        "comparacion_historica": historical,
        "total_hallazgos": len(persisted_hallazgos),
        "total_propuestas": len(persisted_propuestas),
        "conocimiento": {
            "utilizado": knowledge_ctx.get("utilizado"),
            "mensaje": knowledge_ctx.get("mensaje"),
            "fuentes": knowledge_ctx.get("fuentes_consultadas", []),
            "requiere_validacion": knowledge_ctx.get("requiere_validacion"),
        },
        "motor": {
            "suficiencia_datos": motor.get("suficiencia_datos"),
            "hipotesis": motor.get("hipotesis"),
            "hipotesis_principal": motor.get("hipotesis_principal"),
            "contrastes": motor.get("contrastes"),
            "alternativas": motor.get("alternativas"),
            "priorizacion": motor.get("priorizacion"),
            "escenarios": motor.get("escenarios"),
            "finops": motor.get("finops"),
            "recomendacion_consolidada": motor.get("recomendacion_consolidada"),
        },
    }, ensure_ascii=False)

    try:
        register_finops_values(
            db,
            organization_id=organization_id,
            user_id=user_id,
            analysis_id=analysis.id,
            estimates=motor.get("finops", []),
        )
    except Exception:
        pass  # FINOPS opcional — no bloquear análisis

    log_salud_knowledge_audit(
        db,
        organization_id=organization_id,
        analysis_id=analysis.id,
        user_id=user_id,
        knowledge_ctx=knowledge_ctx,
    )

    save_experience_case(
        db, organization_id,
        ips_name=ips_name,
        analysis_type="diagnostico_integral",
        analysis_id=analysis.id,
        context={"request": request_text, "fuentes": list(datasets.keys())},
        indicators={k: indicators.get(k, {}) for k in ("facturacion", "radicacion", "glosas", "cartera")},
        hallazgos=[{"title": h.title, "category": h.category} for h in persisted_hallazgos],
        recommendations=[{"accion": p.accion_propuesta} for p in persisted_propuestas],
        employee_ids=employee_ids,
    )

    db.commit()
    db.refresh(analysis)
    return analysis


def _compare_historical(db: Session, org_id: str, ips_name: str, indicators: dict) -> dict[str, Any]:
    profiles = (
        db.query(IpsHistoricalProfile)
        .filter(IpsHistoricalProfile.organization_id == org_id, IpsHistoricalProfile.ips_name == ips_name)
        .order_by(IpsHistoricalProfile.period.desc())
        .limit(3)
        .all()
    )
    if not profiles:
        return {"disponible": False, "mensaje": "Sin histórico previo para esta IPS"}

    comparisons: dict[str, Any] = {}
    latest = json.loads(profiles[0].metrics_json or "{}")
    fact = indicators.get("facturacion", {})
    if fact.get("disponible") and "valor_facturado" in latest:
        prev = latest["valor_facturado"]
        curr = fact["valor_facturado"]
        if isinstance(prev, (int, float)) and isinstance(curr, (int, float)) and prev > 0:
            comparisons["facturacion_variacion_pct"] = round(((curr - prev) / prev) * 100, 2)

    return {"disponible": True, "periodos": [p.period for p in profiles], "comparaciones": comparisons}


def _update_historical(db: Session, org_id: str, ips_name: str, indicators: dict) -> None:
    period = _utcnow().strftime("%Y-%m")
    metrics: dict[str, Any] = {}
    for key in ("facturacion", "radicacion", "glosas", "cartera"):
        ind = indicators.get(key, {})
        if ind.get("disponible"):
            if key == "facturacion":
                metrics["valor_facturado"] = ind.get("valor_facturado")
            elif key == "radicacion":
                metrics["porcentaje_radicado"] = ind.get("porcentaje_radicado")
            elif key == "glosas":
                metrics["porcentaje_glosa"] = ind.get("porcentaje_glosa")
            elif key == "cartera":
                metrics["saldo_total"] = ind.get("saldo_total")

    existing = (
        db.query(IpsHistoricalProfile)
        .filter(
            IpsHistoricalProfile.organization_id == org_id,
            IpsHistoricalProfile.ips_name == ips_name,
            IpsHistoricalProfile.period == period,
        )
        .first()
    )
    if existing:
        existing.metrics_json = json.dumps(metrics, ensure_ascii=False)
    else:
        db.add(IpsHistoricalProfile(
            organization_id=org_id,
            ips_name=ips_name,
            period=period,
            metrics_json=json.dumps(metrics, ensure_ascii=False),
        ))


def create_action_plan(
    db: Session,
    *,
    organization_id: str,
    analysis_id: str,
    propuesta_ids: list[str],
    user_id: str,
) -> IpsActionPlan:
    normalized_ids = normalize_propuesta_ids(propuesta_ids)
    if not normalized_ids:
        raise ValueError("Debe seleccionar al menos una propuesta")

    analysis = (
        db.query(IpsAnalysis)
        .filter(
            IpsAnalysis.id == analysis_id,
            IpsAnalysis.organization_id == organization_id,
        )
        .first()
    )
    if not analysis:
        raise ValueError("Análisis no encontrado para esta organización")

    existing = find_idempotent_action_plan(
        db, organization_id, analysis_id, normalized_ids
    )
    if existing:
        return existing

    propuestas = (
        db.query(IpsPropuesta)
        .filter(
            IpsPropuesta.organization_id == organization_id,
            IpsPropuesta.analysis_id == analysis_id,
            IpsPropuesta.id.in_(normalized_ids),
        )
        .all()
    )
    if len(propuestas) != len(normalized_ids):
        raise ValueError("Una o más propuestas no pertenecen a este análisis u organización")

    propuesta_by_id = {p.id: p for p in propuestas}
    ordered_propuestas = [propuesta_by_id[pid] for pid in normalized_ids]

    tasks = []
    for i, p in enumerate(ordered_propuestas):
        p.selected_for_plan = True
        tasks.append({
            "secuencia": i + 1,
            "titulo": p.problema,
            "propuesta_id": p.id,
            "hallazgo_id": p.hallazgo_id,
            "evidencia": p.evidencia,
            "accion": p.accion_propuesta,
            "responsable": p.responsable_sugerido,
            "plazo": p.plazo,
            "indicador": p.indicador_seguimiento,
            "meta": p.meta,
            "confianza": p.confianza,
            "prioridad": p.priority_score,
            "estado": "PENDIENTE",
        })

    plan = IpsActionPlan(
        organization_id=organization_id,
        analysis_id=analysis_id,
        title=f"Plan de acción IPS — {len(tasks)} tareas",
        status="ACTIVO",
        tasks_json=json.dumps(tasks, ensure_ascii=False),
        created_by_id=user_id,
    )
    db.add(plan)
    db.flush()

    bridge_action_plan_to_workplan(
        db,
        action_plan=plan,
        analysis=analysis,
        propuestas=ordered_propuestas,
        user_id=user_id,
    )
    db.refresh(plan)
    return plan


def get_diagnostico(db: Session, org_id: str, analysis_id: str) -> dict[str, Any]:
    analysis = (
        db.query(IpsAnalysis)
        .filter(IpsAnalysis.id == analysis_id, IpsAnalysis.organization_id == org_id)
        .first()
    )
    if not analysis:
        return {"error": "Análisis no encontrado"}

    hallazgos = (
        db.query(IpsHallazgo)
        .filter(IpsHallazgo.analysis_id == analysis_id, IpsHallazgo.organization_id == org_id)
        .order_by(IpsHallazgo.priority_score.desc())
        .all()
    )
    propuestas = (
        db.query(IpsPropuesta)
        .filter(IpsPropuesta.analysis_id == analysis_id, IpsPropuesta.organization_id == org_id)
        .order_by(IpsPropuesta.priority_score.desc())
        .all()
    )
    plans = (
        db.query(IpsActionPlan)
        .filter(IpsActionPlan.analysis_id == analysis_id, IpsActionPlan.organization_id == org_id)
        .all()
    )

    summary = json.loads(analysis.summary_json or "{}")
    motor_summary = summary.get("motor", {})
    from app.services.salud_experience import buscar_casos_similares
    casos = buscar_casos_similares(db, org_id, tipo_problema="diagnostico", limit=3)

    return {
        "id": analysis.id,
        "ips_name": analysis.ips_name,
        "estado": analysis.status,
        "resumen_ejecutivo": summary.get("resumen_ejecutivo", {}),
        "calidad_datos": json.loads(analysis.data_profile_json or "{}"),
        "suficiencia_datos": motor_summary.get("suficiencia_datos", {}),
        "analisis_disponibles": json.loads(analysis.available_analyses_json or "{}"),
        "indicadores": json.loads(analysis.indicators_json or "{}"),
        "trazabilidad": json.loads(analysis.traceability_json or "{}"),
        "hallazgos": [_hallazgo_to_dict(h) for h in hallazgos],
        "hipotesis": motor_summary.get("hipotesis", []),
        "hipotesis_principal": motor_summary.get("hipotesis_principal"),
        "contrastes": motor_summary.get("contrastes", []),
        "alternativas": motor_summary.get("alternativas", []),
        "priorizacion": motor_summary.get("priorizacion", {}),
        "escenarios": motor_summary.get("escenarios", {}),
        "finops": motor_summary.get("finops", []),
        "recomendacion_consolidada": motor_summary.get("recomendacion_consolidada", {}),
        "oportunidades": [_propuesta_to_dict(p) for p in propuestas],
        "work_plan_id": analysis.work_plan_id,
        "planes_accion": [
            {
                "id": pl.id,
                "work_plan_id": pl.work_plan_id,
                "titulo": pl.title,
                "tareas": json.loads(pl.tasks_json or "[]"),
            }
            for pl in plans
        ],
        "plan_accion": [json.loads(pl.tasks_json or "[]") for pl in plans],
        "especialistas": json.loads(analysis.specialists_json or "{}"),
        "comparacion_historica": summary.get("comparacion_historica", {}),
        "conocimiento": summary.get("conocimiento", {}),
        "experiencia": {"casos_similares": casos},
        "creado": analysis.created_at.isoformat() if analysis.created_at else None,
    }


def _hallazgo_to_dict(h: IpsHallazgo) -> dict[str, Any]:
    sources = json.loads(h.sources_json or "[]")
    fuentes_titulos = [
        s.get("titulo") or s.get("document_name")
        for s in sources
        if isinstance(s, dict) and (s.get("titulo") or s.get("document_name"))
    ]
    evidence = json.loads(h.evidence_json or "{}")
    return {
        "id": h.id,
        "categoria": h.category,
        "titulo": h.title,
        "descripcion": h.description,
        "tipo": h.kind,
        "indicador": h.indicator_code,
        "valor": h.indicator_value,
        "severidad": h.severity,
        "prioridad": h.priority_score,
        "confianza": h.confidence,
        "criterios_confianza": json.loads(h.confidence_criteria_json or "{}"),
        "causa_probable": h.probable_cause,
        "impacto_economico": h.economic_impact,
        "evidencia": evidence,
        "fuentes": json.loads(h.sources_json or "[]"),
        "fuentes_consultadas": fuentes_titulos,
        "evidencia_documental": evidence.get("fuentes_documentales") or evidence.get("documental"),
    }


def _propuesta_to_dict(p: IpsPropuesta) -> dict[str, Any]:
    return {
        "id": p.id,
        "problema": p.problema,
        "evidencia": p.evidencia,
        "causa_probable": p.causa_probable,
        "impacto": p.impacto,
        "accion_propuesta": p.accion_propuesta,
        "responsable_sugerido": p.responsable_sugerido,
        "plazo": p.plazo,
        "indicador_seguimiento": p.indicador_seguimiento,
        "meta": p.meta,
        "impacto_esperado": p.impacto_esperado,
        "confianza": p.confianza,
        "prioridad": p.priority_score,
    }
