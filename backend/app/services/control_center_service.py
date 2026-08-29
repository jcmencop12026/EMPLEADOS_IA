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
    {"id": "employees_active", "label": "Empleados IA activos", "permiso": "employee.view", "enlace": "/directorio"},
    {"id": "plans_active", "label": "Planes activos", "permiso": "operations.view", "enlace": "/operaciones"},
    {"id": "executions_running", "label": "Ejecuciones en curso", "permiso": "operations.view", "enlace": "/ejecuciones"},
    {"id": "approvals_pending", "label": "Aprobaciones pendientes", "permiso": "operations.view", "enlace": "/aprobaciones"},
    {"id": "automations_active", "label": "Automatizaciones activas", "permiso": "automation.view", "enlace": "/automatizaciones"},
    {"id": "notifications_unread", "label": "Notificaciones sin leer", "permiso": "notification.view", "enlace": "/notificaciones"},
    {"id": "opportunities_open", "label": "Oportunidades abiertas", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "expected_value", "label": "Valor potencial", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "materialized_value", "label": "Valor materializado", "permiso": "oportunidades.view", "enlace": "/oportunidades"},
    {"id": "ai_consumption", "label": "Consumo IA (periodo)", "permiso": "finops.view", "enlace": "/costos-valor"},
    {"id": "ai_cost", "label": "Costo IA (periodo)", "permiso": "finops.view", "enlace": "/costos-valor"},
    {"id": "failed_executions", "label": "Ejecuciones fallidas", "permiso": "operations.view", "enlace": "/ejecuciones"},
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
        last_activity = max(filter(None, [last_wp, last_llm, emp.updated_at]), default=None)
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
            if plan.vencimiento and plan.vencimiento < now:
                prio += 1
                items.append({
                    "prioridad": prio,
                    "tipo": "tarea_vencida",
                    "titulo": plan.objective or "Plan vencido",
                    "fecha": plan.vencimiento.isoformat(),
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
    items = []
    for p in providers:
        items.append({
            "id": p.id,
            "nombre": p.name,
            "proveedor": p.provider_type,
            "habilitado": p.is_enabled,
            "errores_24h": err_map.get(p.provider_type, 0),
            "enlace": "/administracion/proveedores-ia",
        })
    return {"proveedores": items, "total": len(items), "degradados": sum(1 for i in items if i["errores_24h"] > 0)}


def _audit_section(db: Session, org_id: str, limit: int = 8) -> list[dict[str, Any]]:
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "accion": r.action,
            "detalle": r.detail,
            "fecha": r.created_at.isoformat() if r.created_at else None,
            "enlace": "/auditoria",
        }
        for r in rows
    ]


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

    ctx = {
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
        "expected_value": opp_summary.get("valor_potencial_total") if opp_summary else None,
        "materialized_value": opp_summary.get("valor_materializado_total") if opp_summary else None,
        "ai_consumption": finops["dashboard"].get("execution_count") if finops else None,
        "ai_cost": finops["dashboard"].get("total_cost_label") if finops else None,
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
        adapters.DiagnosticoAdapter(),
        adapters.SenalesAdapter(),
    ]
    modulos = {a.modulo: a.fetch(db, org_id, permissions=permissions) for a in adapter_instances}

    return {
        "generated_at": _utcnow().isoformat(),
        "organization_id": org_id,
        "filtros": {
            "periodo": periodo,
            "employee_id": employee_id,
            "proceso": proceso,
            "estado": estado,
        },
        "resumen_ejecutivo": {
            "indicadores": _build_indicators(ctx, permissions),
            "operaciones": ops_summary,
        },
        "atencion_requerida": _atencion_requerida(db, org_id, permissions) if _has(permissions, "control_center.view") else [],
        "empleados_ia": employees,
        "oportunidades": modulos.get("oportunidades"),
        "impacto": modulos.get("impacto"),
        "finops": finops,
        "finops_extendido": modulos.get("finops_extendido"),
        "valor_retorno": modulos.get("valor_retorno"),
        "diagnostico": modulos.get("diagnostico"),
        "senales": modulos.get("senales"),
        "salud_plataforma": build_health_report(include_schedulers=True) if _has(permissions, "control_center.view") else None,
        "auditoria_reciente": _audit_section(db, org_id) if _has(permissions, "audit.view") else None,
        "llm": _llm_section(db, org_id) if _has(permissions, "llm.view") else None,
        "actividad_reciente": recent_events,
        "integraciones_futuras": {
            "1100": "UI oportunidades — rama cursor/1100-cierre-operativo-oportunidades",
            "1110": "FinOps extendido — integrar endpoints bloque 1110",
            "1120": "Señales/ingesta — completar con bloque 1120",
            "1200": "Línea base/impacto — rama cursor/1200-linea-base-impacto",
            "1210": "Valor/retorno — motor económico bloque 1210",
            "1220": "Diagnóstico ejecutivo — bloque 1220",
        },
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
