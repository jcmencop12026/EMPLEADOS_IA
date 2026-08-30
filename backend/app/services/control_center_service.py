"""Centro de Control ejecutivo — capa de consolidación (solo lectura)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.automation_models import Automation, AutomationRun
from app.health import build_health_report
from app.llm_models import LlmInferenceLog, LlmProviderConfig
from app.models import AuditLog, Notification, User
from app.opportunity_models import Opportunity
from app.orchestration_models import AIEmployee, ApprovalRequest, WorkEvent, WorkPlan
from app.permissions import check_permission, user_permissions
from app.services import control_center_adapters as adapters
from app.services import finops_service, operations_center, proactive_service

EXECUTIVE_INDICATOR_DEFS = [
    {"id": "organizations_active", "label": "Organizaciones activas", "permiso": "platform.organization.view", "enlace": "/administracion/organizaciones"},
    {"id": "employees_active", "label": "Empleados IA activos", "permiso": "employee.view", "enlace": "/directorio"},
    {"id": "plans_active", "label": "Planes activos", "permiso": "operations.view", "enlace": "/operaciones"},
    {"id": "executions_running", "label": "Ejecuciones en curso", "permiso": "operations.view", "enlace": "/ejecuciones"},
    {"id": "approvals_pending", "label": "Aprobaciones pendientes", "permiso": "operations.view", "enlace": "/aprobaciones"},
    {"id": "automations_active", "label": "Automatizaciones activas", "permiso": "automation.view", "enlace": "/automatizaciones"},
    {"id": "notifications_unread", "label": "Notificaciones sin leer", "permiso": "notification.view", "enlace": "/notificaciones"},
    {"id": "opportunities_open", "label": "Oportunidades abiertas", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "verified_value", "label": "Valor verificado", "permiso": "valoracion.view", "enlace": "/costos-valor"},
    {"id": "estimated_value", "label": "Valor estimado", "permiso": "valoracion.view", "enlace": "/costos-valor"},
    {"id": "potential_value", "label": "Valor potencial", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "realized_value", "label": "Valor realizado", "permiso": "valoracion.view", "enlace": "/costos-valor"},
    {"id": "materialized_value", "label": "Valor materializado", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "ai_consumption", "label": "Consumo IA (periodo)", "permiso": "finops.view", "enlace": "/costos-valor"},
    {"id": "ai_cost", "label": "Costo IA (periodo)", "permiso": "finops.view", "enlace": "/costos-valor"},
    {"id": "tco_total", "label": "TCO mensual", "permiso": "tco.view", "enlace": "/tco"},
    {"id": "implementations_active", "label": "Implementaciones activas", "permiso": "implementacion.view", "enlace": "/implementacion"},
    {"id": "milestones_at_risk", "label": "Hitos en riesgo", "permiso": "implementacion.view", "enlace": "/implementacion"},
    {"id": "failed_executions", "label": "Ejecuciones fallidas", "permiso": "operations.view", "enlace": "/ejecuciones"},
    {"id": "external_sources_active", "label": "Fuentes externas activas", "permiso": "inteligencia_externa.view", "enlace": "/inteligencia-externa"},
    {"id": "external_signals_pending", "label": "Señales externas pendientes", "permiso": "inteligencia_externa.view", "enlace": "/inteligencia-externa"},
    {"id": "external_risks_open", "label": "Riesgos externos abiertos", "permiso": "inteligencia_externa.view", "enlace": "/inteligencia-externa"},
]

SEMANTICA_CONTRATO = {
    "HECHO": "Dato observado o verificado en fuente primaria",
    "INFERENCIA": "Derivado de cálculo, estimación o correlación — no es hecho demostrado",
    "RECOMENDACION": "Acción sugerida — requiere decisión humana",
    "SIN_CLASIFICAR": "Sin clasificación semántica disponible",
    "valor": adapters.SEMANTICA_VALOR,
}

INTEGRACIONES_FUTURAS = {
    "1100": "Integrado — estados operativos oportunidades",
    "1110": "Integrado — FinOps extendido",
    "1120": "Integrado — señales e ingesta",
    "1200": "Integrado — línea base e impacto",
    "1210": "Integrado — valoración y retorno",
    "1220": "Integrado — diagnóstico transversal",
    "1240": "Integrado — inteligencia externa",
    "1260": "Integrado — aprendizaje",
    "1270": "Integrado — multiproveedor IA",
    "1280": "Integrado — comercial y valor",
    "1290": "Integrado — optimización",
    "1320": "Integrado — TCO",
    "1340": "Integrado — implementación",
    "MB-07": "Integrado — planificador consumo/capacidad",
    "MB-11": "Integrado — comunicaciones ejecutivas",
    "MB-12": "Integrado — mesa de ayuda",
    "AUDITOR": "Integrado — auditor empleados IA (solo lectura)",
    "FABRICA": "Integrado vía empleados IA y auditor",
    "MI_TRABAJO": "Integrado — resumen Mi Trabajo",
    "CONTINUIDAD": "Integrado — continuidad y resiliencia",
    "CONOCIMIENTO_930": "Pendiente — Conocimiento",
    "INTEGRACIONES_T5": "Pendiente — Integraciones visuales Tramo 5",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    """Normaliza a UTC aware — compatible con SQLite (naive) y PostgreSQL (aware)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _max_utc(*values: datetime | None) -> datetime | None:
    normalized = [_as_utc(v) for v in values if v is not None]
    return max(normalized) if normalized else None


def _period_start(periodo: str | None) -> datetime | None:
    now = _utcnow()
    if periodo == "7d":
        return now - timedelta(days=7)
    if periodo == "30d":
        return now - timedelta(days=30)
    if periodo == "mtd":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _has(permissions: set[str], code: str) -> bool:
    try:
        return code in permissions
    except Exception:
        return False


def _employees_section(db: Session, org_id: str, *, employee_id: str | None = None) -> dict[str, Any]:
    query = db.query(AIEmployee).filter(AIEmployee.organization_id == org_id)
    if employee_id:
        query = query.filter(AIEmployee.id == employee_id)
    employees = query.limit(50).all()
    total = db.query(func.count(AIEmployee.id)).filter(AIEmployee.organization_id == org_id).scalar() or 0
    active = (
        db.query(func.count(AIEmployee.id))
        .filter(AIEmployee.organization_id == org_id, AIEmployee.lifecycle_status == "ACTIVE", AIEmployee.is_active.is_(True))
        .scalar()
        or 0
    )

    activity_rows: list[dict[str, Any]] = []
    for emp in employees:
        last_wp = (
            db.query(func.max(func.coalesce(WorkPlan.completed_at, WorkPlan.started_at, WorkPlan.created_at)))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.employee_id == emp.id)
            .scalar()
        )
        last_llm = (
            db.query(func.max(LlmInferenceLog.created_at))
            .filter(LlmInferenceLog.organization_id == org_id, LlmInferenceLog.employee_id == emp.id)
            .scalar()
        )
        last_activity = _max_utc(last_wp, last_llm, emp.updated_at)
        running = (
            db.query(func.count(WorkPlan.id))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.employee_id == emp.id, WorkPlan.status.in_(["RUNNING", "PLANNING", "PARTIAL"]))
            .scalar()
            or 0
        )
        failed = (
            db.query(func.count(WorkPlan.id))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.employee_id == emp.id, WorkPlan.status == "FAILED")
            .scalar()
            or 0
        )
        activity_rows.append({
            "id": emp.id,
            "nombre": emp.name,
            "estado": emp.status,
            "lifecycle_status": emp.lifecycle_status,
            "ultima_actividad": last_activity.isoformat() if last_activity else None,
            "ejecuciones_activas": running,
            "errores": failed,
            "enlace": f"/empleados/{emp.id}",
        })

    return {"total": total, "activos": active, "items": activity_rows}


def _atencion_requerida(db: Session, org_id: str, permissions: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    prio = 0

    if _has(permissions, "operations.view"):
        approvals = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.organization_id == org_id, ApprovalRequest.status == "PENDING")
            .order_by(ApprovalRequest.created_at.desc())
            .limit(10)
            .all()
        )
        for ap in approvals:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "aprobacion",
                "titulo": ap.action or "Aprobación pendiente",
                "detalle": ap.reason,
                "fecha": ap.created_at.isoformat() if ap.created_at else None,
                "enlace": "/aprobaciones",
                "origen": "operaciones",
            })

        failed_plans = (
            db.query(WorkPlan)
            .filter(WorkPlan.organization_id == org_id, WorkPlan.status == "FAILED")
            .order_by(WorkPlan.completed_at.desc().nullslast(), WorkPlan.created_at.desc())
            .limit(5)
            .all()
        )
        for plan in failed_plans:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "ejecucion_fallida",
                "titulo": plan.objective or plan.summary or "Ejecución fallida",
                "fecha": (plan.completed_at or plan.created_at).isoformat() if (plan.completed_at or plan.created_at) else None,
                "enlace": f"/ejecuciones/{plan.id}",
                "origen": "operaciones",
            })

        overdue = (
            db.query(WorkPlan)
            .filter(WorkPlan.organization_id == org_id, WorkPlan.status.notin_(["COMPLETED", "CANCELLED", "FAILED"]))
            .order_by(WorkPlan.vencimiento.asc().nullslast())
            .limit(20)
            .all()
        )
        now = _utcnow()
        for plan in overdue:
            vencimiento = _as_utc(plan.vencimiento)
            if vencimiento and vencimiento < now:
                prio += 1
                items.append({
                    "prioridad": prio,
                    "tipo": "tarea_vencida",
                    "titulo": plan.objective or "Plan vencido",
                    "fecha": vencimiento.isoformat(),
                    "enlace": f"/operaciones/{plan.id}",
                    "origen": "operaciones",
                })

    if _has(permissions, "automation.view"):
        failed_runs = (
            db.query(AutomationRun)
            .filter(AutomationRun.organization_id == org_id, AutomationRun.status == "FAILED")
            .order_by(AutomationRun.finished_at.desc().nullslast())
            .limit(5)
            .all()
        )
        for run in failed_runs:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "automatizacion_fallida",
                "titulo": f"Automatización fallida ({run.id[:8]})",
                "detalle": run.error,
                "fecha": run.finished_at.isoformat() if run.finished_at else None,
                "enlace": f"/automatizaciones/{run.automation_id}/ejecuciones",
                "origen": "automatizaciones",
            })

    if _has(permissions, "oportunidades.view"):
        crit = (
            db.query(Opportunity)
            .filter(
                Opportunity.organization_id == org_id,
                Opportunity.estado == "PENDIENTE_APROBACION",
            )
            .order_by(Opportunity.prioridad_score.desc().nullslast())
            .limit(5)
            .all()
        )
        for opp in crit:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "oportunidad_critica",
                "titulo": opp.titulo,
                "fecha": opp.fecha_deteccion.isoformat() if opp.fecha_deteccion else None,
                "enlace": f"/oportunidades/{opp.id}",
                "origen": "oportunidades",
            })

    if _has(permissions, "finops.view"):
        from app.finops_models import FinOpsBudget

        budgets = db.query(FinOpsBudget).filter(FinOpsBudget.organization_id == org_id, FinOpsBudget.active.is_(True)).all()
        for b in budgets:
            spent = finops_service.budget_spent_for_scope(db, b)
            state = finops_service.budget_state(spent, b.amount_limit)
            if state in ("Cerca del límite", "Límite alcanzado", "Atención"):
                prio += 1
                items.append({
                    "prioridad": prio,
                    "tipo": "presupuesto_ia",
                    "titulo": f"Presupuesto {b.name}: {state}",
                    "enlace": "/costos-valor",
                    "origen": "finops",
                })

    if _has(permissions, "linea_base.view"):
        from app.baseline_models import LineaBaseMedicion

        pendientes_impacto = (
            db.query(LineaBaseMedicion)
            .filter(
                LineaBaseMedicion.organization_id == org_id,
                LineaBaseMedicion.estado == "REGISTRADA",
            )
            .order_by(LineaBaseMedicion.created_at.desc())
            .limit(5)
            .all()
        )
        for med in pendientes_impacto:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "impacto_pendiente_validacion",
                "titulo": f"Medición pendiente de validación ({med.id[:8]})",
                "fecha": med.created_at.isoformat() if med.created_at else None,
                "enlace": f"/lineas-base/{med.linea_base_id}",
                "origen": "impacto",
            })

    if _has(permissions, "diagnosticos.view"):
        from app.diagnostic_models import Diagnostic

        diag_prio = (
            db.query(Diagnostic)
            .filter(
                Diagnostic.organization_id == org_id,
                Diagnostic.estado.in_(["GENERADO", "VALIDADO"]),
            )
            .order_by(Diagnostic.prioridad_score.desc().nullslast())
            .limit(5)
            .all()
        )
        for d in diag_prio:
            if d.prioridad_score and float(d.prioridad_score) >= 0.7:
                prio += 1
                items.append({
                    "prioridad": prio,
                    "tipo": "diagnostico_prioritario",
                    "titulo": d.resumen or d.codigo,
                    "fecha": d.created_at.isoformat() if d.created_at else None,
                    "enlace": f"/diagnosticos/{d.id}",
                    "origen": "diagnostico",
                })

    if _has(permissions, "oportunidades.view"):
        from app.opportunity_models import ProactiveSignal

        errores_senal = (
            db.query(ProactiveSignal)
            .filter(
                ProactiveSignal.organization_id == org_id,
                ProactiveSignal.estado_procesamiento.in_(["RECHAZADA", "DUPLICADA"]),
            )
            .order_by(ProactiveSignal.created_at.desc())
            .limit(3)
            .all()
        )
        for sig in errores_senal:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "senal_ingesta",
                "titulo": f"Señal {sig.estado_procesamiento.lower()}: {sig.tipo}",
                "detalle": sig.rejection_reason,
                "fecha": sig.created_at.isoformat() if sig.created_at else None,
                "enlace": f"/senales/{sig.id}",
                "origen": "senales",
            })

    if _has(permissions, "inteligencia_externa.view"):
        from app.external_intelligence_enums import RelevanceLevel
        from app.external_models import ExternalSignalExtension
        from app.opportunity_models import ProactiveSignal

        pendientes_ext = (
            db.query(ExternalSignalExtension, ProactiveSignal)
            .join(ProactiveSignal, ProactiveSignal.id == ExternalSignalExtension.signal_id)
            .filter(
                ExternalSignalExtension.organization_id == org_id,
                ExternalSignalExtension.validated_at.is_(None),
                ExternalSignalExtension.relevance.in_(
                    (RelevanceLevel.RELEVANTE, RelevanceLevel.POSIBLEMENTE_RELEVANTE)
                ),
            )
            .order_by(ExternalSignalExtension.captured_at.desc())
            .limit(3)
            .all()
        )
        for ext, sig in pendientes_ext:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "senal_externa_pendiente",
                "severidad": "MEDIA",
                "titulo": f"Señal externa sin validar: {sig.tipo or 'externa'}",
                "detalle": ext.hecho_observado,
                "fecha": ext.captured_at.isoformat() if ext.captured_at else None,
                "enlace": f"/inteligencia-externa/senales/{ext.signal_id}",
                "origen": "inteligencia_externa",
            })

        riesgos_ext = (
            db.query(ExternalSignalExtension, ProactiveSignal)
            .join(ProactiveSignal, ProactiveSignal.id == ExternalSignalExtension.signal_id)
            .filter(
                ExternalSignalExtension.organization_id == org_id,
                ExternalSignalExtension.is_risk.is_(True),
                ExternalSignalExtension.validated_at.is_(None),
            )
            .order_by(ExternalSignalExtension.captured_at.desc())
            .limit(3)
            .all()
        )
        for ext, sig in riesgos_ext:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "riesgo_externo",
                "severidad": "ALTA",
                "titulo": f"Riesgo externo: {ext.risk_type or sig.tipo or 'sin tipo'}",
                "detalle": ext.hecho_observado,
                "fecha": ext.captured_at.isoformat() if ext.captured_at else None,
                "enlace": f"/inteligencia-externa/senales/{ext.signal_id}",
                "origen": "inteligencia_externa",
            })

    if _has(permissions, "notification.view"):
        alerts = (
            db.query(Notification)
            .filter(Notification.organization_id == org_id, Notification.status == "NEW", Notification.severity.in_(["HIGH", "CRITICAL"]))
            .order_by(Notification.created_at.desc())
            .limit(5)
            .all()
        )
        for n in alerts:
            prio += 1
            items.append({
                "prioridad": prio,
                "tipo": "alerta",
                "titulo": n.title,
                "detalle": n.message,
                "fecha": n.created_at.isoformat() if n.created_at else None,
                "enlace": "/notificaciones",
                "origen": "notificaciones",
            })

    items.sort(key=lambda x: x["prioridad"])
    return items[:20]


def _finops_section(db: Session, org_id: str, *, period_start: datetime | None) -> dict[str, Any]:
    dash = finops_service.dashboard_summary(db, org_id, period_start=period_start, period_end=_utcnow())
    from app.finops_models import FinOpsBudget

    budgets = []
    for b in db.query(FinOpsBudget).filter(FinOpsBudget.organization_id == org_id, FinOpsBudget.active.is_(True)).all():
        spent = finops_service.budget_spent_for_scope(db, b)
        pct = float((spent / b.amount_limit) * 100) if b.amount_limit else None
        budgets.append({
            "id": b.id,
            "nombre": b.name,
            "limite": float(b.amount_limit),
            "consumido": float(spent),
            "porcentaje": round(pct, 2) if pct is not None else None,
            "estado": finops_service.budget_state(spent, b.amount_limit),
        })
    tokens = (
        db.query(func.coalesce(func.sum(LlmInferenceLog.tokens_total), 0))
        .filter(LlmInferenceLog.organization_id == org_id)
        .scalar()
    )
    if period_start:
        tokens = (
            db.query(func.coalesce(func.sum(LlmInferenceLog.tokens_total), 0))
            .filter(LlmInferenceLog.organization_id == org_id, LlmInferenceLog.created_at >= period_start)
            .scalar()
        )
    return {
        "disponible": True,
        "dashboard": dash,
        "presupuestos": budgets,
        "tokens_periodo": int(tokens or 0),
        "enlace": "/costos-valor",
    }


def _llm_section(db: Session, org_id: str) -> dict[str, Any]:
    providers = db.query(LlmProviderConfig).filter(LlmProviderConfig.organization_id == org_id).all()
    since = _utcnow() - timedelta(hours=24)
    errors = (
        db.query(LlmInferenceLog.provider, func.count())
        .filter(LlmInferenceLog.organization_id == org_id, LlmInferenceLog.status != "OK", LlmInferenceLog.created_at >= since)
        .group_by(LlmInferenceLog.provider)
        .all()
    )
    err_map = {p: c for p, c in errors}
    latency_rows = (
        db.query(LlmInferenceLog.provider, func.avg(LlmInferenceLog.latency_ms))
        .filter(
            LlmInferenceLog.organization_id == org_id,
            LlmInferenceLog.created_at >= since,
            LlmInferenceLog.latency_ms.isnot(None),
        )
        .group_by(LlmInferenceLog.provider)
        .all()
    )
    lat_map = {p: int(avg) for p, avg in latency_rows if avg is not None}
    tokens_rows = (
        db.query(LlmInferenceLog.provider, func.coalesce(func.sum(LlmInferenceLog.tokens_total), 0))
        .filter(LlmInferenceLog.organization_id == org_id, LlmInferenceLog.created_at >= since)
        .group_by(LlmInferenceLog.provider)
        .all()
    )
    tok_map = {p: int(t or 0) for p, t in tokens_rows}
    items = []
    for p in providers:
        items.append({
            "id": p.id,
            "nombre": p.name,
            "proveedor": p.provider_type,
            "modelo": p.model_default,
            "habilitado": p.is_enabled,
            "errores_24h": err_map.get(p.provider_type, 0),
            "latencia_media_ms": lat_map.get(p.provider_type),
            "tokens_24h": tok_map.get(p.provider_type, 0),
            "estado": "DEGRADADO" if err_map.get(p.provider_type, 0) > 0 else ("ACTIVO" if p.is_enabled else "INACTIVO"),
            "enlace": "/administracion/proveedores-ia",
        })
    return {
        "disponible": len(items) > 0,
        "proveedores": items,
        "total": len(items),
        "degradados": sum(1 for i in items if i["errores_24h"] > 0),
        "enlace": "/administracion/proveedores-ia",
    }


def _audit_section(db: Session, org_id: str, limit: int = 8) -> list[dict[str, Any]]:
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    user_ids = {r.user_id for r in rows if r.user_id}
    actors: dict[str, str] = {}
    if user_ids:
        actors = {
            u.id: u.username
            for u in db.query(User).filter(User.id.in_(user_ids)).all()
        }
    return [
        {
            "id": r.id,
            "accion": r.action,
            "detalle": r.detail,
            "actor": actors.get(r.user_id) if r.user_id else None,
            "modulo": r.action.split(".")[0] if r.action and "." in r.action else r.action,
            "fecha": r.created_at.isoformat() if r.created_at else None,
            "enlace": "/auditoria",
        }
        for r in rows
    ]


def _fetch_module_adapters(
    db: Session,
    org_id: str,
    *,
    permissions: set[str],
    period_start: datetime | None,
    adapter_instances: list[Any],
    proceso: str | None = None,
    estado: str | None = None,
) -> dict[str, Any]:
    modulos: dict[str, Any] = {}
    for adapter in adapter_instances:
        try:
            modulos[adapter.modulo] = adapter.fetch(
                db,
                org_id,
                permissions=permissions,
                period_start=period_start,
                proceso=proceso,
                estado=estado,
            )
        except Exception:
            db.rollback()
            modulos[adapter.modulo] = {
                "disponible": False,
                "estado": "NO DISPONIBLE",
                "modulo": adapter.modulo,
                "bloque": getattr(adapter, "bloque", ""),
            }
    return modulos


def _cadena_ejecutiva(db: Session, org_id: str, permissions: set[str], *, period_start: datetime | None) -> list[dict[str, Any]]:
    """Representación conceptual de la cadena ejecutiva con enlaces a módulos origen."""
    if not _has(permissions, "oportunidades.view"):
        return []
    from app.baseline_models import LineaBase
    from app.diagnostic_models import DiagnosticOpportunityLink
    from app.opportunity_models import Opportunity, ProactiveSignal
    from app.valuation_models import OpportunityValuation

    opp_q = db.query(Opportunity).filter(
        Opportunity.organization_id == org_id,
        Opportunity.estado.in_(["EN_SEGUIMIENTO", "MATERIALIZADA", "EN_EJECUCION", "CERRADA"]),
    )
    if period_start:
        opp_q = opp_q.filter(Opportunity.updated_at >= period_start)
    opportunities = opp_q.order_by(Opportunity.updated_at.desc().nullslast()).limit(5).all()
    chains: list[dict[str, Any]] = []
    for opp in opportunities:
        etapas: list[dict[str, Any]] = []
        if opp.signal_id and _has(permissions, "oportunidades.view"):
            sig = db.query(ProactiveSignal).filter(ProactiveSignal.id == opp.signal_id).first()
            if sig:
                etapas.append({"etapa": "SEÑAL", "id": sig.id, "enlace": f"/senales/{sig.id}"})
        if _has(permissions, "diagnosticos.view"):
            link = (
                db.query(DiagnosticOpportunityLink)
                .filter(
                    DiagnosticOpportunityLink.organization_id == org_id,
                    DiagnosticOpportunityLink.opportunity_id == opp.id,
                )
                .first()
            )
            if link:
                etapas.append({"etapa": "DIAGNÓSTICO", "id": link.diagnostic_id, "enlace": f"/diagnosticos/{link.diagnostic_id}"})
        etapas.append({"etapa": "OPORTUNIDAD", "id": opp.id, "enlace": f"/oportunidades/{opp.id}"})
        if opp.work_plan_id and _has(permissions, "operations.view"):
            etapas.append({"etapa": "EJECUCIÓN", "id": opp.work_plan_id, "enlace": f"/ejecuciones/{opp.work_plan_id}"})
        if opp.estado in ("MATERIALIZADA", "CERRADA"):
            etapas.append({"etapa": "RESULTADO", "id": opp.id, "enlace": f"/oportunidades/{opp.id}"})
        if _has(permissions, "linea_base.view"):
            lb = (
                db.query(LineaBase)
                .filter(LineaBase.organization_id == org_id, LineaBase.opportunity_id == opp.id)
                .first()
            )
            if lb:
                etapas.append({"etapa": "MEDICIÓN", "id": lb.id, "enlace": f"/lineas-base/{lb.id}"})
                etapas.append({"etapa": "IMPACTO", "id": lb.id, "enlace": f"/lineas-base/{lb.id}"})
        if _has(permissions, "valoracion.view"):
            val = (
                db.query(OpportunityValuation)
                .filter(OpportunityValuation.organization_id == org_id, OpportunityValuation.opportunity_id == opp.id)
                .first()
            )
            if val:
                etapas.append({"etapa": "VALOR", "id": val.id, "enlace": f"/oportunidades/{opp.id}"})
        if _has(permissions, "finops.view") and opp.id:
            etapas.append({"etapa": "COSTO", "id": opp.id, "enlace": "/costos-valor"})
        if len(etapas) >= 2:
            chains.append({
                "oportunidad_id": opp.id,
                "titulo": opp.titulo,
                "estado": opp.estado,
                "etapas": etapas,
            })
    return chains


def _build_indicators(ctx: dict[str, Any], permissions: set[str]) -> list[dict[str, Any]]:
    indicators: list[dict[str, Any]] = []
    for defn in EXECUTIVE_INDICATOR_DEFS:
        if not _has(permissions, defn["permiso"]):
            indicators.append({
                "id": defn["id"],
                "label": defn["label"],
                "valor": None,
                "disponible": False,
                "estado": "Sin permiso",
                "enlace": defn["enlace"],
            })
            continue
        value = ctx.get(defn["id"])
        indicators.append({
            "id": defn["id"],
            "label": defn["label"],
            "valor": value,
            "disponible": value is not None,
            "estado": None if value is not None else "Sin información disponible",
            "enlace": defn["enlace"],
        })
    return indicators


def get_executive_summary(
    db: Session,
    user: User,
    *,
    periodo: str | None = "mtd",
    employee_id: str | None = None,
    proceso: str | None = None,
    estado: str | None = None,
    organization_id: str | None = None,
) -> dict[str, Any]:
    org_id = organization_id or user.organization_id
    permissions = user_permissions(user, db)
    period_start = _period_start(periodo)

    employees = _employees_section(db, org_id, employee_id=employee_id) if _has(permissions, "employee.view") else None
    ops_summary = operations_center.get_summary(db, org_id) if _has(permissions, "operations.view") else None

    automations_active = None
    if _has(permissions, "automation.view"):
        automations_active = (
            db.query(func.count(Automation.id))
            .filter(Automation.organization_id == org_id, Automation.status == "ACTIVE")
            .scalar()
            or 0
        )

    notifications_unread = None
    if _has(permissions, "notification.view"):
        notifications_unread = (
            db.query(func.count(Notification.id))
            .filter(Notification.organization_id == org_id, Notification.status == "NEW")
            .scalar()
            or 0
        )

    opp_summary = proactive_service.business_summary(db, org_id) if _has(permissions, "oportunidades.view") else None
    finops = _finops_section(db, org_id, period_start=period_start) if _has(permissions, "finops.view") else None

    organizations_active = None
    if _has(permissions, "platform.organization.view"):
        from app.models import Organization
        from app.tenant_scope import ORG_STATUS_INACTIVE

        organizations_active = (
            db.query(func.count(Organization.id))
            .filter(Organization.status != ORG_STATUS_INACTIVE)
            .scalar()
            or 0
        )

    ctx = {
        "organizations_active": organizations_active,
        "employees_active": employees["activos"] if employees else None,
        "plans_active": (ops_summary or {}).get("running", 0) + (ops_summary or {}).get("pending", 0) if ops_summary else None,
        "executions_running": (ops_summary or {}).get("running") if ops_summary else None,
        "approvals_pending": (
            (db.query(func.count(ApprovalRequest.id)).filter(ApprovalRequest.organization_id == org_id, ApprovalRequest.status == "PENDING").scalar() or 0)
            + (opp_summary or {}).get("pendientes_aprobacion", 0)
            if _has(permissions, "operations.view") or _has(permissions, "oportunidades.view")
            else None
        ),
        "automations_active": automations_active,
        "notifications_unread": notifications_unread,
        "opportunities_open": opp_summary.get("oportunidades_detectadas") if opp_summary else None,
        "potential_value": opp_summary.get("valor_potencial_total") if opp_summary else None,
        "materialized_value": opp_summary.get("valor_materializado_total") if opp_summary else None,
        "verified_value": None,
        "estimated_value": None,
        "realized_value": None,
        "ai_consumption": finops["dashboard"].get("execution_count") if finops else None,
        "ai_cost": finops["dashboard"].get("total_cost_label") if finops else None,
        "tco_total": None,
        "implementations_active": None,
        "milestones_at_risk": None,
        "failed_executions": (ops_summary or {}).get("error") if ops_summary else None,
    }

    recent_events = []
    if _has(permissions, "operations.view"):
        events = (
            db.query(WorkEvent)
            .join(WorkPlan, WorkEvent.work_plan_id == WorkPlan.id)
            .filter(WorkPlan.organization_id == org_id)
            .order_by(WorkEvent.created_at.desc())
            .limit(8)
            .all()
        )
        recent_events = [
            {
                "id": e.id,
                "tipo": e.event_type,
                "plan_id": e.work_plan_id,
                "fecha": e.created_at.isoformat() if e.created_at else None,
                "enlace": f"/ejecuciones/{e.work_plan_id}" if e.work_plan_id else None,
            }
            for e in events
        ]

    adapter_instances = [
        adapters.OportunidadesAdapter(),
        adapters.ImpactoAdapter(),
        adapters.FinOpsExtendidoAdapter(),
        adapters.ValorRetornoAdapter(),
        adapters.ComercialResumenAdapter(),
        adapters.DiagnosticoAdapter(),
        adapters.DiagnosticoExplicacionAdapter(),
        adapters.SenalesAdapter(),
        adapters.InteligenciaExternaAdapter(),
        adapters.AprendizajeAdapter(),
        adapters.OptimizacionAdapter(),
        adapters.TcoAdapter(),
        adapters.ImplementacionAdapter(),
        adapters.MultiproveedorAdapter(),
        adapters.Mb07PlanificadorAdapter(),
        adapters.Mb11ComunicacionesAdapter(),
        adapters.Mb12MesaAyudaAdapter(),
        adapters.AuditorEmpleadosAdapter(),
        adapters.MiTrabajoAdapter(),
        adapters.ContinuidadAdapter(),
    ]
    modulos = _fetch_module_adapters(
        db,
        org_id,
        permissions=permissions,
        period_start=period_start,
        adapter_instances=adapter_instances,
        proceso=proceso,
        estado=estado,
    )

    ie_mod = modulos.get("inteligencia_externa") or {}
    ctx["external_sources_active"] = ie_mod.get("fuentes_activas") if ie_mod.get("disponible") else None
    ctx["external_signals_pending"] = ie_mod.get("sin_validar") if ie_mod.get("disponible") else None
    ctx["external_risks_open"] = ie_mod.get("riesgos_abiertos") if ie_mod.get("disponible") else None

    vr_mod = modulos.get("valor_retorno") or {}
    com_mod = modulos.get("comercial") or {}
    if vr_mod.get("disponible"):
        ctx["verified_value"] = vr_mod.get("valor_verificado")
        ctx["estimated_value"] = vr_mod.get("valor_estimado")
        ctx["realized_value"] = vr_mod.get("valor_realizado")
        if ctx["potential_value"] is None:
            ctx["potential_value"] = vr_mod.get("valor_potencial")
    elif com_mod.get("disponible"):
        ctx["verified_value"] = com_mod.get("valor_verificado")
        ctx["estimated_value"] = com_mod.get("valor_estimado")
        ctx["realized_value"] = com_mod.get("valor_realizado")
        if ctx["potential_value"] is None:
            ctx["potential_value"] = com_mod.get("valor_potencial")

    tco_mod = modulos.get("tco") or {}
    if tco_mod.get("disponible"):
        ctx["tco_total"] = tco_mod.get("inversion_total")

    impl_mod = modulos.get("implementacion") or {}
    if impl_mod.get("disponible"):
        ctx["implementations_active"] = impl_mod.get("proyectos_activos")
        ctx["milestones_at_risk"] = impl_mod.get("hitos_en_riesgo")

    valor_consolidado = {
        "verificado": ctx.get("verified_value"),
        "estimado": ctx.get("estimated_value"),
        "potencial": ctx.get("potential_value"),
        "realizado": ctx.get("realized_value"),
        "materializado": ctx.get("materialized_value"),
        "roi_porcentaje": vr_mod.get("retorno_porcentaje") if vr_mod.get("disponible") else None,
        "payback_meses": com_mod.get("payback_promedio_meses") if com_mod.get("disponible") else None,
        "nota_potencial": adapters.SEMANTICA_VALOR["nota_potencial"],
        "semantica": adapters.SEMANTICA_VALOR,
    }

    return {
        "generated_at": _utcnow().isoformat(),
        "organization_id": org_id,
        "filtros": {
            "periodo": periodo,
            "employee_id": employee_id,
            "proceso": proceso,
            "estado": estado,
        },
        "semantica": SEMANTICA_CONTRATO,
        "secciones": [
            {"id": "resumen", "label": "Resumen"},
            {"id": "valor", "label": "Valor"},
            {"id": "operacion", "label": "Operación"},
            {"id": "ia_costos", "label": "IA y costos"},
            {"id": "implementacion", "label": "Implementación"},
            {"id": "salud", "label": "Salud"},
        ],
        "resumen_ejecutivo": {
            "indicadores": _build_indicators(ctx, permissions),
            "operaciones": ops_summary,
            "valor": valor_consolidado,
        },
        "atencion_requerida": _atencion_requerida(db, org_id, permissions) if _has(permissions, "control_center.view") else [],
        "empleados_ia": employees,
        "oportunidades": modulos.get("oportunidades"),
        "linea_base": modulos.get("impacto"),
        "impacto": modulos.get("impacto"),
        "finops": finops,
        "finops_extendido": modulos.get("finops_extendido"),
        "valor_retorno": modulos.get("valor_retorno"),
        "comercial": modulos.get("comercial"),
        "valor_consolidado": valor_consolidado,
        "diagnostico": modulos.get("diagnostico"),
        "explicacion": modulos.get("explicacion"),
        "senales": modulos.get("senales"),
        "inteligencia_externa": modulos.get("inteligencia_externa"),
        "aprendizaje": modulos.get("aprendizaje"),
        "optimizacion": modulos.get("optimizacion"),
        "tco": modulos.get("tco"),
        "implementacion": modulos.get("implementacion"),
        "multiproveedor": modulos.get("multiproveedor"),
        "mb07_planificador": modulos.get("mb07_planificador"),
        "mb11_comunicaciones": modulos.get("mb11_comunicaciones"),
        "mb12_soporte": modulos.get("mb12_soporte"),
        "auditor_empleados": modulos.get("auditor_empleados"),
        "mi_trabajo": modulos.get("mi_trabajo"),
        "continuidad": modulos.get("continuidad"),
        "cadena_ejecutiva": _cadena_ejecutiva(db, org_id, permissions, period_start=period_start),
        "salud_plataforma": build_health_report(include_schedulers=True) if _has(permissions, "control_center.view") else None,
        "auditoria_reciente": _audit_section(db, org_id) if _has(permissions, "audit.view") else None,
        "llm": _llm_section(db, org_id) if _has(permissions, "llm.view") else None,
        "actividad_reciente": recent_events,
        "integraciones_futuras": INTEGRACIONES_FUTURAS,
    }


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    if not requested_org_id or requested_org_id == user.organization_id:
        return user.organization_id
    check_permission(user, "platform.organization.view", db)
    from app.models import Organization

    org = db.query(Organization).filter(Organization.id == requested_org_id).first()
    if not org:
        raise ValueError("Organización no encontrada")
    return org.id
