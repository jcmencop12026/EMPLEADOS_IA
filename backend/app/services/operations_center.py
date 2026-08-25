"""Centro de Operaciones — OPERACIONES-940."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.enums import WorkPlanPriority
from app.models import User
from app.orchestration_models import AIEmployee, ApprovalRequest, Capability, EmployeeTask, FinOpsRecord, Tool, WorkEvent, WorkPlan
from app.services.operations_labels import (
    APPROVAL_LABELS,
    EVENT_LABELS,
    PRIORITY_ORDER,
    SUMMARY_BUCKETS,
    display_status,
    due_state,
    due_state_label,
    is_due_soon,
    is_overdue,
    normalize_priority,
    priority_label,
    task_progress,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _username(db: Session, user_id: str | None) -> str | None:
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.username if user else None


def _employee_name(db: Session, employee_id: str | None) -> str | None:
    if not employee_id:
        return None
    employee = db.query(AIEmployee).filter(AIEmployee.id == employee_id).first()
    return employee.name if employee else None


def _process_name(db: Session, plan: WorkPlan) -> str | None:
    if plan.capability_id:
        cap = db.query(Capability).filter(Capability.id == plan.capability_id).first()
        if cap:
            return cap.name
    if plan.tool_id:
        tool = db.query(Tool).filter(Tool.id == plan.tool_id).first()
        if tool:
            return tool.name
    return None


def _latest_activity(db: Session, plan_id: str) -> datetime | None:
    event = (
        db.query(WorkEvent)
        .filter(WorkEvent.work_plan_id == plan_id)
        .order_by(WorkEvent.created_at.desc())
        .first()
    )
    return event.created_at if event else None


def _pending_approvals(db: Session, plan_id: str) -> int:
    return (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.work_plan_id == plan_id, ApprovalRequest.status == "PENDING")
        .count()
    )


def _allowed_actions(plan: WorkPlan) -> list[str]:
    actions: list[str] = ["ver"]
    if plan.status in {"CREATED", "READY", "PLANNING", "WAITING_DATA"}:
        actions.append("iniciar")
    if plan.status in {"RUNNING", "PARTIAL"}:
        actions.extend(["pausar", "cancelar"])
    if plan.status == "WAITING_DATA":
        actions.append("reanudar")
    if plan.status not in {"COMPLETED", "CANCELLED", "FAILED"}:
        actions.append("cancelar")
    if plan.status not in {"COMPLETED", "CANCELLED"}:
        actions.append("reasignar")
    return sorted(set(actions))


def _operation_item(db: Session, plan: WorkPlan) -> dict[str, Any]:
    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).all()
    done, total = task_progress(tasks)
    progress = f"{done}/{total}" if total else "0/0"
    last_activity = _latest_activity(db, plan.id) or plan.completed_at or plan.started_at or plan.created_at
    return {
        "id": plan.id,
        "trabajo": plan.objective or plan.request[:120],
        "proceso": _process_name(db, plan),
        "responsable": _username(db, plan.user_id),
        "empleado_ia": _employee_name(db, plan.employee_id),
        "prioridad": priority_label(plan.prioridad),
        "prioridad_codigo": plan.prioridad or WorkPlanPriority.MEDIA.value,
        "estado": display_status(plan.status),
        "estado_codigo": plan.status,
        "progreso": progress,
        "aprobaciones_pendientes": _pending_approvals(db, plan.id),
        "inicio": plan.started_at or plan.created_at,
        "vencimiento": plan.vencimiento,
        "vencimiento_estado": due_state_label(plan),
        "vencimiento_codigo": due_state(plan),
        "ultima_actividad": last_activity,
        "resultado": plan.summary or (plan.error if plan.status == "FAILED" else None),
        "approval_status": APPROVAL_LABELS.get(plan.approval_status, plan.approval_status),
        "confidence": plan.confidence,
        "correlation_id": plan.correlation_id,
        "employee_id": plan.employee_id,
        "acciones": _allowed_actions(plan),
    }


def get_summary(db: Session, organization_id: str) -> dict[str, int]:
    rows = db.query(WorkPlan).filter(WorkPlan.organization_id == organization_id).all()
    now = _utcnow()
    summary = {key: 0 for key in SUMMARY_BUCKETS}
    for plan in rows:
        for bucket, statuses in SUMMARY_BUCKETS.items():
            if bucket in {"overdue", "due_soon"}:
                continue
            if plan.status in statuses:
                summary[bucket] += 1
        if plan.approval_status == "PENDING" and plan.status not in SUMMARY_BUCKETS["approval"]:
            summary["approval"] += 1
        if is_overdue(plan, now):
            summary["overdue"] += 1
        elif is_due_soon(plan, now):
            summary["due_soon"] += 1
    return summary


def list_operations(
    db: Session,
    organization_id: str,
    *,
    search: str | None = None,
    status: str | None = None,
    employee_id: str | None = None,
    prioridad: str | None = None,
    proceso: str | None = None,
    bucket: str | None = None,
    vencimiento_filtro: str | None = None,
    orden: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.query(WorkPlan).filter(WorkPlan.organization_id == organization_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (WorkPlan.objective.ilike(pattern)) | (WorkPlan.request.ilike(pattern)) | (WorkPlan.summary.ilike(pattern))
        )
    if status:
        query = query.filter(WorkPlan.status == status.upper())
    if employee_id:
        query = query.filter(WorkPlan.employee_id == employee_id)
    if prioridad:
        try:
            code = normalize_priority(prioridad)
            query = query.filter(WorkPlan.prioridad == code)
        except ValueError:
            return []
    if date_from:
        query = query.filter(WorkPlan.created_at >= date_from)
    if date_to:
        query = query.filter(WorkPlan.created_at <= date_to)

    if orden == "prioridad":
        rows = query.all()
        rows.sort(key=lambda p: (PRIORITY_ORDER.get(p.prioridad or "MEDIA", 99), p.created_at), reverse=False)
        rows = rows[:limit]
    elif orden == "vencimiento":
        rows = query.order_by(WorkPlan.vencimiento.asc().nullslast(), WorkPlan.created_at.desc()).limit(limit).all()
    else:
        rows = query.order_by(WorkPlan.created_at.desc()).limit(limit).all()

    items = [_operation_item(db, row) for row in rows]
    now = _utcnow()

    if bucket and bucket in SUMMARY_BUCKETS:
        if bucket == "overdue":
            items = [item for item, row in zip(items, rows) if is_overdue(row, now)]
        elif bucket == "due_soon":
            items = [item for item, row in zip(items, rows) if is_due_soon(row, now)]
        else:
            statuses = SUMMARY_BUCKETS[bucket]
            items = [
                item
                for item, row in zip(items, rows)
                if row.status in statuses or (bucket == "approval" and row.approval_status == "PENDING")
            ]
    if proceso:
        items = [item for item in items if item.get("proceso") and proceso.lower() in item["proceso"].lower()]
    if vencimiento_filtro:
        items = [item for item in items if item.get("vencimiento_codigo") == vencimiento_filtro]
    return items


def get_plan(db: Session, organization_id: str, plan_id: str) -> WorkPlan | None:
    return (
        db.query(WorkPlan)
        .filter(WorkPlan.id == plan_id, WorkPlan.organization_id == organization_id)
        .first()
    )


def get_operation_detail(db: Session, organization_id: str, plan_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    payload = _operation_item(db, plan)
    finops = db.query(FinOpsRecord).filter(FinOpsRecord.work_plan_id == plan.id).all()
    payload.update(
        {
            "objective": plan.objective,
            "summary": plan.summary,
            "error": plan.error,
            "costo_metadata": {
                "duracion_total_ms": sum(r.duration_ms or 0 for r in finops),
                "costo_total": sum(r.cost or 0 for r in finops),
                "registros": len(finops),
            },
        }
    )
    return payload


def list_operation_tasks(db: Session, organization_id: str, plan_id: str) -> list[dict[str, Any]]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).order_by(EmployeeTask.sequence).all()
    output = []
    for task in tasks:
        result = None
        if task.outputs_json:
            try:
                payload = json.loads(task.outputs_json)
                result = payload.get("summary") or str(payload)[:200]
            except json.JSONDecodeError:
                result = task.outputs_json[:200]
        output.append(
            {
                "id": task.id,
                "titulo": task.title,
                "responsable": _employee_name(db, task.employee_id),
                "estado": display_status(task.status),
                "estado_codigo": task.status,
                "prioridad": priority_label(plan.prioridad),
                "dependencia": str(task.sequence - 1) if task.sequence > 1 else None,
                "inicio": task.started_at,
                "fin": task.completed_at,
                "resultado": result,
                "error": task.error,
                "executor_type": task.executor_type,
            }
        )
    return output


def list_operation_executions(db: Session, organization_id: str, plan_id: str) -> list[dict[str, Any]]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).order_by(EmployeeTask.sequence).all()
    executions = []
    for task in tasks:
        duration = None
        if task.started_at and task.completed_at:
            duration = int((task.completed_at - task.started_at).total_seconds() * 1000)
        executions.append(
            {
                "id": task.id,
                "inicio": task.started_at,
                "fin": task.completed_at,
                "duracion_ms": duration,
                "estado": display_status(task.status),
                "estado_codigo": task.status,
                "empleado_ia": _employee_name(db, task.employee_id),
                "resultado": task.outputs_json[:200] if task.outputs_json else None,
                "error": task.error,
            }
        )
    if plan.started_at:
        plan_duration = None
        end = plan.completed_at or _utcnow()
        if plan.started_at:
            plan_duration = int((end - plan.started_at).total_seconds() * 1000)
        executions.insert(
            0,
            {
                "id": plan.id,
                "inicio": plan.started_at,
                "fin": plan.completed_at,
                "duracion_ms": plan_duration,
                "estado": display_status(plan.status),
                "estado_codigo": plan.status,
                "empleado_ia": _employee_name(db, plan.employee_id),
                "resultado": plan.summary,
                "error": plan.error,
            },
        )
    return executions


def list_operation_approvals(db: Session, organization_id: str, plan_id: str) -> list[dict[str, Any]]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    rows = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.work_plan_id == plan.id, ApprovalRequest.organization_id == organization_id)
        .order_by(ApprovalRequest.created_at.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "estado": APPROVAL_LABELS.get(row.status, row.status),
            "estado_codigo": row.status,
            "accion": row.action,
            "responsable": row.employee_name,
            "fecha": row.created_at,
            "comentario": row.decision_comment,
        }
        for row in rows
    ]


def get_operation_results(db: Session, organization_id: str, plan_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    result = json.loads(plan.result_json) if plan.result_json else None
    references = []
    if result and isinstance(result, dict):
        if result.get("findings"):
            references.append(f"{len(result['findings'])} hallazgos")
        if result.get("evidence"):
            references.append("evidencia adjunta")
    return {
        "resumen": plan.summary,
        "resultado": result,
        "fecha": plan.completed_at or plan.started_at,
        "referencias": references,
        "estado": display_status(plan.status),
    }


def list_operation_activity(db: Session, organization_id: str, plan_id: str) -> list[dict[str, Any]]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    rows = (
        db.query(WorkEvent)
        .filter(WorkEvent.work_plan_id == plan.id, WorkEvent.organization_id == organization_id)
        .order_by(WorkEvent.created_at.desc())
        .all()
    )
    activity = []
    for row in rows:
        detail = None
        if row.payload_json:
            try:
                detail = json.dumps(json.loads(row.payload_json), ensure_ascii=False)[:300]
            except json.JSONDecodeError:
                detail = row.payload_json[:300]
        activity.append(
            {
                "id": row.id,
                "tipo": row.event_type,
                "etiqueta": EVENT_LABELS.get(row.event_type, row.event_type),
                "fecha": row.created_at,
                "detalle": detail,
            }
        )
    return activity


def cancel_operation(db: Session, *, organization_id: str, plan_id: str, user_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    if plan.status in {"COMPLETED", "CANCELLED"}:
        raise ValueError("No es posible cancelar la operación en su estado actual.")
    plan.status = "CANCELLED"
    plan.completed_at = _utcnow()
    db.query(EmployeeTask).filter(
        EmployeeTask.work_plan_id == plan.id,
        EmployeeTask.status.not_in(["COMPLETED", "CANCELLED"]),
    ).update({"status": "CANCELLED"}, synchronize_session=False)
    db.add(
        WorkEvent(
            organization_id=organization_id,
            work_plan_id=plan.id,
            event_type="work.cancelled",
            payload_json=json.dumps({"by": user_id}),
        )
    )
    db.commit()
    db.refresh(plan)
    return get_operation_detail(db, organization_id, plan_id)


def pause_operation(db: Session, *, organization_id: str, plan_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    if plan.status not in {"RUNNING", "PARTIAL"}:
        raise ValueError("No es posible pausar la operación en su estado actual.")
    plan.status = "WAITING_DATA"
    db.commit()
    db.refresh(plan)
    return get_operation_detail(db, organization_id, plan_id)


def resume_operation(db: Session, *, organization_id: str, plan_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    if plan.status != "WAITING_DATA":
        raise ValueError("No es posible reanudar la operación en su estado actual.")
    plan.status = "RUNNING"
    db.commit()
    db.refresh(plan)
    return get_operation_detail(db, organization_id, plan_id)


def reassign_operation(db: Session, *, organization_id: str, plan_id: str, employee_id: str) -> dict[str, Any]:
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    employee = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == organization_id)
        .first()
    )
    if not employee:
        raise LookupError("Empleado IA no encontrado.")
    plan.employee_id = employee_id
    db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).update(
        {"employee_id": employee_id}, synchronize_session=False
    )
    db.commit()
    db.refresh(plan)
    return get_operation_detail(db, organization_id, plan_id)


def update_operation(
    db: Session,
    *,
    organization_id: str,
    plan_id: str,
    prioridad: str | None = None,
    vencimiento: datetime | None = None,
    employee_id: str | None = None,
    sin_vencimiento: bool = False,
) -> dict[str, Any]:
    if employee_id:
        return reassign_operation(db, organization_id=organization_id, plan_id=plan_id, employee_id=employee_id)
    plan = get_plan(db, organization_id, plan_id)
    if not plan:
        raise LookupError("La operación no existe o no está disponible.")
    if prioridad is not None:
        plan.prioridad = normalize_priority(prioridad)
    if sin_vencimiento:
        plan.vencimiento = None
    elif vencimiento is not None:
        plan.vencimiento = vencimiento
    db.commit()
    db.refresh(plan)
    return get_operation_detail(db, organization_id, plan_id)
