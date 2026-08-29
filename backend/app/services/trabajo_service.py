"""Bandeja unificada de trabajo humano — agregación sobre fuentes existentes."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.automation_models import AutomationRun
from app.continuidad_models import ContinuidadAlerta
from app.finops_models import FinOpsBudget
from app.models import Notification, Organization, User
from app.opportunity_models import Opportunity
from app.orchestration_models import ApprovalRequest, WorkPlan
from app.permissions import user_permissions
from app.services import control_center_service as cc_svc
from app.services import finops_service
from app.services import integration_service as integ_svc
from app.services import support_service as support_svc
from app.support_enums import ESTADOS_ABIERTOS
from app.support_models import SupportCase

SUPPORT_NOTIFICATION_TYPES = frozenset(
    {
        "SUPPORT_CASE_ASSIGNED",
        "SUPPORT_CASE_STATUS",
        "SUPPORT_CASE_RESOLVED",
        "SUPPORT_CASE_COMMENT",
        "SUPPORT_SLA_WARNING",
    }
)

TRABAJO_VIEW_PERMISSIONS = frozenset(
    {
        "operations.view",
        "notification.view",
        "oportunidades.view",
        "continuidad.view",
        "integraciones.view",
        "finops.view",
        "automation.view",
        "linea_base.view",
        "diagnosticos.view",
        "support.view",
        "support.create",
        "support.assign",
    }
)

PRIORITY_ORDER = {"CRITICA": 4, "CRITICAL": 4, "ALTA": 3, "HIGH": 3, "MEDIA": 2, "MEDIUM": 2, "BAJA": 1, "LOW": 1}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _has(permissions: set[str], code: str) -> bool:
    return code in permissions


def _priority_label_and_order(raw: str | None) -> tuple[str, int]:
    key = (raw or "MEDIA").upper()
    return key, PRIORITY_ORDER.get(key, 2)


def _presentation_state(
    tipo: str,
    estado_dominio: str,
    *,
    vencida: bool = False,
) -> str:
    if vencida:
        return "VENCIDA"
    upper = (estado_dominio or "").upper()
    if tipo in ("aprobacion", "oportunidad_aprobacion") or upper in (
        "PENDING",
        "PENDIENTE_APROBACION",
        "WAITING_APPROVAL",
    ):
        return "REQUIERE_APROBACION"
    if upper in ("RUNNING", "PLANNING", "PARTIAL", "EN_EJECUCION", "EN_CURSO", "EN_SEGUIMIENTO"):
        return "EN_CURSO"
    if upper in ("COMPLETED", "READ", "ACKNOWLEDGED", "RESUELTA", "APROBADA"):
        return "COMPLETADA"
    if upper in ("FAILED", "RECHAZADA", "DUPLICADA", "CANCELLED", "DISMISSED", "DESCARTADA"):
        return "FALLIDA"
    if upper in ("NEW", "PENDIENTE", "REGISTRADA", "CREATED", "READY"):
        return "PENDIENTE"
    return "PENDIENTE"


def _age_hours(created_at: datetime | None) -> float | None:
    if not created_at:
        return None
    delta = _utcnow() - _ensure_aware(created_at)
    return round(delta.total_seconds() / 3600, 2)


def _action(
    codigo: str,
    etiqueta: str,
    permiso: str | None = None,
    href: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "codigo": codigo,
        "etiqueta": etiqueta,
        "permiso": permiso,
        "href": href,
        "payload": payload,
    }


def _trazabilidad_link(correlation_id: str | None, modulo: str) -> str | None:
    if not correlation_id:
        return None
    if modulo == "integraciones":
        return f"/integraciones/trazabilidad?cid={correlation_id}"
    return f"/integraciones/trazabilidad?cid={correlation_id}"


def _has_support_access(permissions: set[str]) -> bool:
    return any(
        _has(permissions, code)
        for code in ("support.view", "support.create", "support.assign", "support.admin")
    )


def _support_case_visible(case: SupportCase, user: User, permissions: set[str]) -> bool:
    if case.estado not in ESTADOS_ABIERTOS:
        return False
    can_assign = _has(permissions, "support.assign") or _has(permissions, "support.admin")
    if case.responsable_id == user.id:
        return True
    if case.estado == "PENDIENTE_USUARIO" and case.solicitante_id == user.id:
        return True
    if case.estado == "NUEVO" and not case.responsable_id and can_assign:
        return True
    return False


def _support_trabajo_tipo(case: SupportCase, sla_estado: str) -> str:
    if sla_estado == "VENCIDO":
        return "soporte_sla_vencido"
    if sla_estado == "PROXIMO":
        return "soporte_sla_riesgo"
    if case.estado == "NUEVO" and not case.responsable_id:
        return "soporte_asignacion"
    return "soporte_caso"


def _support_presentation(case: SupportCase, sla_estado: str, *, vencida: bool) -> str:
    if vencida or sla_estado == "VENCIDO":
        return "VENCIDA"
    if case.estado in ("EN_PROCESO", "ASIGNADO", "PENDIENTE_TERCERO"):
        return "EN_CURSO"
    return "PENDIENTE"


def _sla_remaining_minutes(fecha_limite: datetime | None, now: datetime) -> float | None:
    if not fecha_limite:
        return None
    delta = _ensure_aware(fecha_limite) - now
    return round(delta.total_seconds() / 60, 1)


def _support_requires_action(case: SupportCase, user: User) -> bool:
    if case.estado == "PENDIENTE_USUARIO" and case.solicitante_id == user.id:
        return True
    if case.responsable_id == user.id:
        return case.estado != "PENDIENTE_TERCERO"
    if case.estado == "NUEVO" and not case.responsable_id:
        return True
    return False


def _notification_visible_query(db: Session, user: User) -> Any:
    query = db.query(Notification).filter(Notification.organization_id == user.organization_id)
    perms = user_permissions(user, db)
    if "notification.manage" not in perms:
        query = query.filter(
            or_(Notification.recipient_user_id.is_(None), Notification.recipient_user_id == user.id),
            or_(Notification.recipient_role.is_(None), Notification.recipient_role == user.role),
        )
    return query


def _notification_requires_action(row: Notification) -> bool:
    if row.status != "NEW":
        return False
    action_types = {
        "APPROVAL_REQUIRED",
        "TASK_FAILED",
        "SECURITY",
        "WARNING",
        "ERROR",
        "SYSTEM",
    }
    return row.type in action_types or row.severity in ("HIGH", "CRITICAL")


def can_access_trabajo(user: User, db: Session) -> bool:
    perms = user_permissions(user, db)
    return any(p in perms for p in TRABAJO_VIEW_PERMISSIONS)


def collect_items(
    db: Session,
    user: User,
    org_id: str,
    permissions: set[str],
    *,
    organization_name: str | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pending_approval_ids: set[str] = set()
    pending_opp_ids: set[str] = set()
    pending_support_case_ids: set[str] = set()
    pending_support_correlation_ids: set[str] = set()
    now = _utcnow()

    if _has(permissions, "operations.view"):
        approvals = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.organization_id == org_id, ApprovalRequest.status == "PENDING")
            .order_by(ApprovalRequest.created_at.desc())
            .limit(100)
            .all()
        )
        for ap in approvals:
            pending_approval_ids.add(ap.id)
            prio_label, prio_order = _priority_label_and_order("ALTA")
            acciones = [
                _action("aprobar", "Aprobar", "operations.approve", payload={"approval_id": ap.id, "decision": "approve"}),
                _action("rechazar", "Rechazar", "operations.approve", payload={"approval_id": ap.id, "decision": "reject"}),
                _action("ver", "Ver ejecución", "operations.view", href=f"/ejecuciones/{ap.work_plan_id}"),
            ]
            plan = db.query(WorkPlan).filter(WorkPlan.id == ap.work_plan_id).first()
            corr = plan.correlation_id if plan else None
            items.append(
                {
                    "id": f"aprobacion:{ap.id}",
                    "source_id": ap.id,
                    "tipo": "aprobacion",
                    "asunto": ap.action or "Aprobación pendiente",
                    "modulo": "operaciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": ap.status,
                    "estado_presentacion": _presentation_state("aprobacion", ap.status),
                    "responsable_id": ap.requested_by,
                    "responsable_nombre": None,
                    "created_at": ap.created_at,
                    "fecha_limite": None,
                    "antiguedad_horas": _age_hours(ap.created_at),
                    "vencida": False,
                    "correlation_id": corr,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "RECOMENDACION",
                    "detalle": ap.reason,
                    "enlace": "/aprobaciones",
                    "trazabilidad_enlace": _trazabilidad_link(corr, "operaciones"),
                    "acciones": acciones,
                    "metadata": {"work_plan_id": ap.work_plan_id, "task_id": ap.task_id},
                }
            )

        failed_plans = (
            db.query(WorkPlan)
            .filter(WorkPlan.organization_id == org_id, WorkPlan.status == "FAILED")
            .order_by(WorkPlan.completed_at.desc().nullslast(), WorkPlan.created_at.desc())
            .limit(50)
            .all()
        )
        for plan in failed_plans:
            prio_label, prio_order = _priority_label_and_order(plan.prioridad)
            items.append(
                {
                    "id": f"ejecucion_fallida:{plan.id}",
                    "source_id": plan.id,
                    "tipo": "ejecucion_fallida",
                    "asunto": plan.objective or plan.summary or "Ejecución fallida",
                    "modulo": "operaciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": plan.status,
                    "estado_presentacion": _presentation_state("ejecucion_fallida", plan.status),
                    "responsable_id": plan.user_id,
                    "responsable_nombre": None,
                    "created_at": plan.completed_at or plan.created_at,
                    "fecha_limite": plan.vencimiento,
                    "antiguedad_horas": _age_hours(plan.completed_at or plan.created_at),
                    "vencida": False,
                    "correlation_id": plan.correlation_id,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": plan.error,
                    "enlace": f"/ejecuciones/{plan.id}",
                    "trazabilidad_enlace": _trazabilidad_link(plan.correlation_id, "operaciones"),
                    "acciones": [_action("ver", "Ver detalle", "operations.view", href=f"/ejecuciones/{plan.id}")],
                    "metadata": {"work_plan_id": plan.id},
                }
            )

        overdue_plans = (
            db.query(WorkPlan)
            .filter(
                WorkPlan.organization_id == org_id,
                WorkPlan.status.notin_(["COMPLETED", "CANCELLED", "FAILED"]),
                WorkPlan.vencimiento.isnot(None),
                WorkPlan.vencimiento < now,
            )
            .order_by(WorkPlan.vencimiento.asc())
            .limit(50)
            .all()
        )
        for plan in overdue_plans:
            prio_label, prio_order = _priority_label_and_order(plan.prioridad or "ALTA")
            items.append(
                {
                    "id": f"tarea_vencida:{plan.id}",
                    "source_id": plan.id,
                    "tipo": "tarea_vencida",
                    "asunto": plan.objective or "Plan vencido",
                    "modulo": "operaciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": plan.status,
                    "estado_presentacion": "VENCIDA",
                    "responsable_id": plan.user_id,
                    "responsable_nombre": None,
                    "created_at": plan.created_at,
                    "fecha_limite": plan.vencimiento,
                    "antiguedad_horas": _age_hours(plan.created_at),
                    "vencida": True,
                    "correlation_id": plan.correlation_id,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": plan.summary,
                    "enlace": f"/operaciones/{plan.id}",
                    "trazabilidad_enlace": _trazabilidad_link(plan.correlation_id, "operaciones"),
                    "acciones": [_action("ver", "Ver plan", "operations.view", href=f"/operaciones/{plan.id}")],
                    "metadata": {"work_plan_id": plan.id},
                }
            )

    if _has(permissions, "automation.view"):
        failed_runs = (
            db.query(AutomationRun)
            .filter(AutomationRun.organization_id == org_id, AutomationRun.status == "FAILED")
            .order_by(AutomationRun.finished_at.desc().nullslast())
            .limit(30)
            .all()
        )
        for run in failed_runs:
            prio_label, prio_order = _priority_label_and_order("ALTA")
            items.append(
                {
                    "id": f"automatizacion_fallida:{run.id}",
                    "source_id": run.id,
                    "tipo": "automatizacion_fallida",
                    "asunto": f"Automatización fallida ({run.id[:8]})",
                    "modulo": "automatizaciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": run.status,
                    "estado_presentacion": _presentation_state("automatizacion_fallida", run.status),
                    "responsable_id": None,
                    "responsable_nombre": None,
                    "created_at": run.finished_at or run.created_at,
                    "fecha_limite": None,
                    "antiguedad_horas": _age_hours(run.finished_at or run.created_at),
                    "vencida": False,
                    "correlation_id": None,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": run.error,
                    "enlace": f"/automatizaciones/{run.automation_id}/ejecuciones",
                    "trazabilidad_enlace": None,
                    "acciones": [
                        _action(
                            "ver",
                            "Ver ejecuciones",
                            "automation.view",
                            href=f"/automatizaciones/{run.automation_id}/ejecuciones",
                        )
                    ],
                    "metadata": {"automation_id": run.automation_id, "work_plan_id": run.work_plan_id},
                }
            )

    if _has(permissions, "oportunidades.view"):
        opps = (
            db.query(Opportunity)
            .filter(Opportunity.organization_id == org_id, Opportunity.estado == "PENDIENTE_APROBACION")
            .order_by(Opportunity.prioridad_score.desc().nullslast(), Opportunity.created_at.desc())
            .limit(50)
            .all()
        )
        for opp in opps:
            pending_opp_ids.add(opp.id)
            urg = opp.urgencia or "MEDIA"
            prio_label, prio_order = _priority_label_and_order(urg)
            acciones = [
                _action("aprobar", "Aprobar", "oportunidades.approve", payload={"opportunity_id": opp.id, "aprobado": True}),
                _action("rechazar", "Rechazar", "oportunidades.approve", payload={"opportunity_id": opp.id, "aprobado": False}),
                _action("ver", "Ver oportunidad", "oportunidades.view", href=f"/oportunidades/{opp.id}"),
            ]
            items.append(
                {
                    "id": f"oportunidad_aprobacion:{opp.id}",
                    "source_id": opp.id,
                    "tipo": "oportunidad_aprobacion",
                    "asunto": opp.titulo,
                    "modulo": "oportunidades",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": opp.estado,
                    "estado_presentacion": _presentation_state("oportunidad_aprobacion", opp.estado),
                    "responsable_id": opp.responsable_id,
                    "responsable_nombre": None,
                    "created_at": opp.fecha_deteccion or opp.created_at,
                    "fecha_limite": None,
                    "antiguedad_horas": _age_hours(opp.fecha_deteccion or opp.created_at),
                    "vencida": False,
                    "correlation_id": opp.correlation_id,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "RECOMENDACION",
                    "detalle": opp.descripcion,
                    "enlace": f"/oportunidades/{opp.id}",
                    "trazabilidad_enlace": _trazabilidad_link(opp.correlation_id, "oportunidades"),
                    "acciones": acciones,
                    "metadata": {"opportunity_id": opp.id, "codigo": opp.codigo},
                }
            )

    if _has(permissions, "continuidad.view"):
        alertas = (
            db.query(ContinuidadAlerta)
            .filter(ContinuidadAlerta.organization_id == org_id, ContinuidadAlerta.resuelta.is_(False))
            .order_by(ContinuidadAlerta.created_at.desc())
            .limit(50)
            .all()
        )
        for alerta in alertas:
            prio_label, prio_order = _priority_label_and_order(alerta.severidad)
            items.append(
                {
                    "id": f"alerta_continuidad:{alerta.id}",
                    "source_id": alerta.id,
                    "tipo": "alerta_continuidad",
                    "asunto": alerta.tipo.replace("_", " "),
                    "modulo": "continuidad",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": "PENDIENTE",
                    "estado_presentacion": "PENDIENTE",
                    "responsable_id": None,
                    "responsable_nombre": None,
                    "created_at": alerta.created_at,
                    "fecha_limite": None,
                    "antiguedad_horas": _age_hours(alerta.created_at),
                    "vencida": False,
                    "correlation_id": None,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": alerta.mensaje,
                    "enlace": "/continuidad",
                    "trazabilidad_enlace": None,
                    "acciones": [_action("ver", "Ver continuidad", "continuidad.view", href="/continuidad")],
                    "metadata": {"entidad_ref": alerta.entidad_ref},
                }
            )

    if _has(permissions, "integraciones.view"):
        try:
            overview = integ_svc.list_connectors_overview(db, org_id)
        except Exception:
            overview = []
        for conn in overview:
            health = conn.get("health") or {}
            if not health.get("circuit_open"):
                continue
            prio_label, prio_order = _priority_label_and_order("ALTA")
            corr = None
            ultima = conn.get("ultima_ejecucion")
            if ultima and isinstance(ultima, dict):
                corr = ultima.get("correlation_id")
            items.append(
                {
                    "id": f"integracion_degradada:{conn['id']}",
                    "source_id": conn["id"],
                    "tipo": "integracion_degradada",
                    "asunto": f"Integración degradada: {conn.get('name', conn.get('code', ''))}",
                    "modulo": "integraciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": conn.get("status") or "DEGRADADO",
                    "estado_presentacion": "PENDIENTE",
                    "responsable_id": None,
                    "responsable_nombre": None,
                    "created_at": None,
                    "fecha_limite": None,
                    "antiguedad_horas": None,
                    "vencida": False,
                    "correlation_id": corr,
                    "requires_action": True,
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": health.get("last_error_message") or conn.get("last_error_message"),
                    "enlace": f"/integraciones/{conn['id']}",
                    "trazabilidad_enlace": _trazabilidad_link(corr, "integraciones"),
                    "acciones": [
                        _action("ver", "Ver conector", "integraciones.view", href=f"/integraciones/{conn['id']}")
                    ],
                    "metadata": {"connector_id": conn["id"]},
                }
            )

    if _has(permissions, "finops.view"):
        budgets = db.query(FinOpsBudget).filter(FinOpsBudget.organization_id == org_id, FinOpsBudget.active.is_(True)).all()
        for budget in budgets:
            spent = finops_service.budget_spent_for_scope(db, budget)
            state = finops_service.budget_state(spent, budget.amount_limit)
            if state not in ("Cerca del límite", "Límite alcanzado", "Atención"):
                continue
            prio_label, prio_order = (
                ("CRITICA", 4) if state == "Límite alcanzado" else ("ALTA", 3)
            )
            items.append(
                {
                    "id": f"presupuesto_ia:{budget.id}",
                    "source_id": budget.id,
                    "tipo": "presupuesto_ia",
                    "asunto": f"Presupuesto {budget.name}: {state}",
                    "modulo": "finops",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": state,
                    "estado_presentacion": "PENDIENTE",
                    "responsable_id": None,
                    "responsable_nombre": None,
                    "created_at": budget.created_at,
                    "fecha_limite": None,
                    "antiguedad_horas": None,
                    "vencida": False,
                    "correlation_id": None,
                    "requires_action": state != "Atención",
                    "informativa": state == "Atención",
                    "semantic_kind": "INFERENCIA",
                    "detalle": f"Consumido {float(spent):.2f} / {float(budget.amount_limit):.2f}",
                    "enlace": "/costos-valor",
                    "trazabilidad_enlace": None,
                    "acciones": [_action("ver", "Ver costos", "finops.view", href="/costos-valor")],
                    "metadata": {"budget_id": budget.id},
                }
            )

    if _has_support_access(permissions):
        support_rows = (
            db.query(SupportCase)
            .filter(
                SupportCase.organization_id == org_id,
                SupportCase.estado.in_(list(ESTADOS_ABIERTOS)),
            )
            .order_by(SupportCase.created_at.desc())
            .limit(200)
            .all()
        )
        for case in support_rows:
            if not _support_case_visible(case, user, permissions):
                continue
            sla_estado = support_svc.compute_sla_estado(case, now)
            fecha_limite = case.resolucion_limite or case.fecha_limite
            vencida = sla_estado == "VENCIDO"
            tipo_item = _support_trabajo_tipo(case, sla_estado)
            prio_label, prio_order = _priority_label_and_order(case.prioridad)
            asunto_safe = support_svc.sanitize_text(case.asunto)
            detalle_safe = support_svc.sanitize_text(case.descripcion)
            pending_support_case_ids.add(case.id)
            if case.correlation_id:
                pending_support_correlation_ids.add(case.correlation_id)
            items.append(
                {
                    "id": f"{tipo_item}:{case.id}",
                    "source_id": case.id,
                    "tipo": tipo_item,
                    "asunto": asunto_safe,
                    "modulo": "soporte",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": case.estado,
                    "estado_presentacion": _support_presentation(case, sla_estado, vencida=vencida),
                    "responsable_id": case.responsable_id,
                    "responsable_nombre": None,
                    "created_at": case.created_at,
                    "fecha_limite": fecha_limite,
                    "antiguedad_horas": _age_hours(case.created_at),
                    "vencida": vencida,
                    "correlation_id": case.correlation_id,
                    "requires_action": _support_requires_action(case, user),
                    "informativa": False,
                    "semantic_kind": "HECHO",
                    "detalle": detalle_safe[:300] if detalle_safe else None,
                    "enlace": f"/soporte/casos/{case.id}",
                    "trazabilidad_enlace": _trazabilidad_link(case.correlation_id, "soporte"),
                    "acciones": [
                        _action("ver", "Abrir caso", None, href=f"/soporte/casos/{case.id}"),
                    ],
                    "metadata": {
                        "origen": "Mesa de Ayuda",
                        "case_id": case.id,
                        "case_numero": case.numero,
                        "case_tipo": case.tipo,
                        "sla_estado": sla_estado,
                        "sla_restante_minutos": _sla_remaining_minutes(fecha_limite, now),
                        "support_estado": case.estado,
                    },
                }
            )

    if _has(permissions, "notification.view"):
        notifications = (
            _notification_visible_query(db, user)
            .filter(Notification.status == "NEW")
            .order_by(Notification.created_at.desc())
            .limit(100)
            .all()
        )
        for n in notifications:
            meta = json.loads(n.metadata_json) if n.metadata_json else {}
            approval_id = str(meta.get("approval_id") or "")
            if n.type == "APPROVAL_REQUIRED" and approval_id and approval_id in pending_approval_ids:
                continue
            if n.source_type == "opportunity" and n.source_id and n.source_id in pending_opp_ids:
                continue
            if n.source_type == "support_case" and n.source_id and n.source_id in pending_support_case_ids:
                continue
            if n.type in SUPPORT_NOTIFICATION_TYPES:
                case_id = str(meta.get("case_id") or n.source_id or "")
                if case_id and case_id in pending_support_case_ids:
                    continue
            corr = meta.get("correlation_id") or n.event_id
            if corr and corr in pending_support_correlation_ids:
                if n.source_type == "support_case" or n.type in SUPPORT_NOTIFICATION_TYPES:
                    continue
            requires = _notification_requires_action(n)
            prio_label, prio_order = _priority_label_and_order(n.severity)
            href = "/notificaciones"
            if n.type == "APPROVAL_REQUIRED" and n.source_id:
                href = f"/ejecuciones/{n.source_id}"
            items.append(
                {
                    "id": f"notificacion:{n.id}",
                    "source_id": n.id,
                    "tipo": "notificacion",
                    "asunto": n.title,
                    "modulo": "notificaciones",
                    "organization_id": org_id,
                    "organization_name": organization_name,
                    "prioridad": prio_label,
                    "prioridad_orden": prio_order,
                    "estado_dominio": n.status,
                    "estado_presentacion": _presentation_state("notificacion", n.status),
                    "responsable_id": n.recipient_user_id,
                    "responsable_nombre": None,
                    "created_at": n.created_at,
                    "fecha_limite": n.expires_at,
                    "antiguedad_horas": _age_hours(n.created_at),
                    "vencida": bool(n.expires_at and _ensure_aware(n.expires_at) < now),
                    "correlation_id": meta.get("correlation_id") or n.event_id,
                    "requires_action": requires,
                    "informativa": not requires,
                    "semantic_kind": "HECHO" if n.type in ("SECURITY", "TASK_FAILED") else None,
                    "detalle": n.message,
                    "enlace": href,
                    "trazabilidad_enlace": _trazabilidad_link(meta.get("correlation_id") or n.event_id, "notificaciones"),
                    "acciones": [
                        _action("leer", "Marcar leída", "notification.view", payload={"notification_id": n.id, "action": "read"}),
                        _action("atender", "Atender", "notification.acknowledge", payload={"notification_id": n.id, "action": "acknowledge"}),
                        _action("ver", "Ver notificación", "notification.view", href="/notificaciones"),
                    ],
                    "metadata": {
                        "notification_type": n.type,
                        "source_type": n.source_type,
                        "source_id": n.source_id,
                        **meta,
                    },
                }
            )

    user_ids = {i["responsable_id"] for i in items if i.get("responsable_id")}
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        name_map = {u.id: u.full_name or u.username for u in users}
        for item in items:
            rid = item.get("responsable_id")
            if rid and rid in name_map:
                item["responsable_nombre"] = name_map[rid]

    return items


def _serialize_item(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    for key in ("created_at", "fecha_limite"):
        val = out.get(key)
        if isinstance(val, datetime):
            out[key] = val.isoformat()
    return out


def filter_items(
    items: list[dict[str, Any]],
    *,
    q: str | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
    tipo: str | None = None,
    modulo: str | None = None,
    responsable_id: str | None = None,
    vencimiento: str | None = None,
    requires_action: bool | None = None,
    case_id: str | None = None,
    sort: str = "prioridad",
    sort_dir: str = "desc",
) -> list[dict[str, Any]]:
    rows = list(items)
    if q:
        needle = q.lower()
        rows = [
            r
            for r in rows
            if needle in f"{r.get('asunto', '')} {r.get('detalle', '')} {r.get('modulo', '')}".lower()
        ]
    if estado:
        rows = [r for r in rows if r.get("estado_presentacion") == estado.upper()]
    if prioridad:
        rows = [r for r in rows if (r.get("prioridad") or "").upper() == prioridad.upper()]
    if tipo:
        rows = [r for r in rows if r.get("tipo") == tipo]
    if modulo:
        rows = [r for r in rows if r.get("modulo") == modulo]
    if responsable_id:
        rows = [r for r in rows if r.get("responsable_id") == responsable_id]
    if case_id:
        rows = [
            r
            for r in rows
            if r.get("source_id") == case_id or (r.get("metadata") or {}).get("case_id") == case_id
        ]
    if requires_action is not None:
        rows = [r for r in rows if r.get("requires_action") == requires_action]
    if vencimiento == "vencida":
        rows = [r for r in rows if r.get("vencida")]
    elif vencimiento == "proxima":
        soon = _utcnow() + timedelta(days=3)
        rows = [
            r
            for r in rows
            if r.get("fecha_limite")
            and not r.get("vencida")
            and _ensure_aware(r["fecha_limite"]) <= soon
        ]
    elif vencimiento == "sin_limite":
        rows = [r for r in rows if not r.get("fecha_limite")]

    def sort_key(row: dict[str, Any]) -> Any:
        if sort == "created_at":
            return row.get("created_at") or ""
        if sort == "fecha_limite":
            return row.get("fecha_limite") or ""
        if sort == "asunto":
            return row.get("asunto") or ""
        return row.get("prioridad_orden", 0)

    reverse = sort_dir != "asc"
    if sort in ("created_at", "fecha_limite", "asunto"):
        rows.sort(key=sort_key, reverse=reverse)
    else:
        rows.sort(key=lambda r: (r.get("prioridad_orden", 0), r.get("created_at") or ""), reverse=reverse)
    return rows


def list_items(
    db: Session,
    user: User,
    *,
    organization_id: str | None = None,
    q: str | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
    tipo: str | None = None,
    modulo: str | None = None,
    responsable_id: str | None = None,
    vencimiento: str | None = None,
    requires_action: bool | None = None,
    case_id: str | None = None,
    sort: str = "prioridad",
    sort_dir: str = "desc",
    limit: int = 200,
) -> dict[str, Any]:
    org_id = cc_svc.resolve_organization_id(db, user, organization_id)
    permissions = set(user_permissions(user, db))
    org = db.query(Organization).filter(Organization.id == org_id).first()
    org_name = org.name if org else None
    raw = collect_items(db, user, org_id, permissions, organization_name=org_name)
    filtered = filter_items(
        raw,
        q=q,
        estado=estado,
        prioridad=prioridad,
        tipo=tipo,
        modulo=modulo,
        responsable_id=responsable_id,
        vencimiento=vencimiento,
        requires_action=requires_action,
        case_id=case_id,
        sort=sort,
        sort_dir=sort_dir,
    )
    limited = filtered[:limit]
    return {
        "items": [_serialize_item(i) for i in limited],
        "total": len(filtered),
        "filtros_aplicados": {
            "q": q,
            "estado": estado,
            "prioridad": prioridad,
            "tipo": tipo,
            "modulo": modulo,
            "responsable_id": responsable_id,
            "vencimiento": vencimiento,
            "requires_action": requires_action,
            "case_id": case_id,
            "sort": sort,
            "sort_dir": sort_dir,
            "organization_id": org_id,
        },
    }


def resumen(db: Session, user: User, *, organization_id: str | None = None) -> dict[str, Any]:
    org_id = cc_svc.resolve_organization_id(db, user, organization_id)
    permissions = set(user_permissions(user, db))
    org = db.query(Organization).filter(Organization.id == org_id).first()
    org_name = org.name if org else None
    raw = collect_items(db, user, org_id, permissions, organization_name=org_name)
    pendientes = sum(1 for i in raw if i.get("requires_action") and i.get("estado_presentacion") != "COMPLETADA")
    vencidas = sum(1 for i in raw if i.get("vencida") or i.get("estado_presentacion") == "VENCIDA")
    requieren_aprobacion = sum(
        1
        for i in raw
        if i.get("estado_presentacion") == "REQUIERE_APROBACION" or i.get("tipo") in ("aprobacion", "oportunidad_aprobacion")
    )
    return {
        "organization_id": org_id,
        "pendientes": pendientes,
        "vencidas": vencidas,
        "requieren_aprobacion": requieren_aprobacion,
        "total_visible": len(raw),
    }
