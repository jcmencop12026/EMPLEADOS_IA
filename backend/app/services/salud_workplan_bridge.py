"""Puente SALUD IpsActionPlan → WorkPlan + EmployeeTask (ENTREGA-002)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.enums import (
    EmployeeLifecycleStatus,
    EmployeeTaskStatus,
    ExecutorType,
    WorkEventType,
    WorkPlanPriority,
    WorkPlanStatus,
)
from app.events.bus import EventMessage, publish
from app.orchestration_models import AIEmployee, EmployeeTask, WorkPlan
from app.salud_models import IpsActionPlan, IpsAnalysis, IpsPropuesta

_ACTIVE_LIFECYCLE = {
    EmployeeLifecycleStatus.ACTIVE,
    EmployeeLifecycleStatus.PUBLISHED,
    EmployeeLifecycleStatus.CERTIFIED,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_propuesta_ids(propuesta_ids: list[str]) -> list[str]:
    return sorted(set(propuesta_ids))


def plan_task_propuesta_ids(plan: IpsActionPlan) -> list[str]:
    tasks = json.loads(plan.tasks_json or "[]")
    return sorted(t.get("propuesta_id") for t in tasks if t.get("propuesta_id"))


def find_idempotent_action_plan(
    db: Session,
    organization_id: str,
    analysis_id: str,
    propuesta_ids: list[str],
) -> IpsActionPlan | None:
    """Mismas propuestas + análisis + tenant → plan existente con WorkPlan."""
    target = set(normalize_propuesta_ids(propuesta_ids))
    if not target:
        return None
    plans = (
        db.query(IpsActionPlan)
        .filter(
            IpsActionPlan.organization_id == organization_id,
            IpsActionPlan.analysis_id == analysis_id,
            IpsActionPlan.work_plan_id.isnot(None),
        )
        .all()
    )
    for plan in plans:
        if set(plan_task_propuesta_ids(plan)) == target:
            return plan
    return None


def _map_prioridad(propuestas: list[IpsPropuesta]) -> str:
    best = WorkPlanPriority.MEDIA.value
    order = {
        WorkPlanPriority.BAJA.value: 0,
        WorkPlanPriority.MEDIA.value: 1,
        WorkPlanPriority.ALTA.value: 2,
        WorkPlanPriority.CRITICA.value: 3,
    }
    for p in propuestas:
        candidate = WorkPlanPriority.MEDIA.value
        if p.confianza and p.confianza.upper() in {"ALTA", "MUY_ALTA"}:
            candidate = WorkPlanPriority.ALTA.value
        if p.priority_score is not None and p.priority_score >= 8:
            candidate = WorkPlanPriority.CRITICA.value
        if order.get(candidate, 0) > order.get(best, 0):
            best = candidate
    return best


def _parse_plazo(plazo: str | None) -> datetime | None:
    if not plazo:
        return None
    text = plazo.strip().lower()
    days = re.search(r"(\d+)\s*d", text)
    if days:
        return _utcnow() + timedelta(days=int(days.group(1)))
    hours = re.search(r"(\d+)\s*h", text)
    if hours:
        return _utcnow() + timedelta(hours=int(hours.group(1)))
    return None


def _latest_vencimiento(propuestas: list[IpsPropuesta]) -> datetime | None:
    latest: datetime | None = None
    for p in propuestas:
        parsed = _parse_plazo(p.plazo)
        if parsed and (latest is None or parsed > latest):
            latest = parsed
    return latest


def resolve_unique_employee(db: Session, organization_id: str, responsable: str | None) -> str | None:
    """Asigna solo si hay coincidencia única con empleado activo del tenant."""
    if not responsable or not responsable.strip():
        return None
    needle = responsable.strip().lower()
    candidates = (
        db.query(AIEmployee)
        .filter(
            AIEmployee.organization_id == organization_id,
            AIEmployee.lifecycle_status.in_(tuple(_ACTIVE_LIFECYCLE)),
        )
        .all()
    )
    matches = [
        emp
        for emp in candidates
        if emp.name.lower() == needle or emp.code.lower() == needle
    ]
    if len(matches) != 1:
        return None
    return matches[0].id


def build_task_payload(propuesta: IpsPropuesta, task_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "origen": "SALUD",
        "analysis_id": propuesta.analysis_id,
        "action_plan_id": task_data.get("action_plan_id"),
        "hallazgo_id": propuesta.hallazgo_id,
        "propuesta_id": propuesta.id,
        "evidencia": propuesta.evidencia,
        "accion": propuesta.accion_propuesta,
        "responsable_sugerido": propuesta.responsable_sugerido,
        "indicador": propuesta.indicador_seguimiento,
        "meta": propuesta.meta,
        "confianza": propuesta.confianza,
        "plazo": propuesta.plazo,
    }


def bridge_action_plan_to_workplan(
    db: Session,
    *,
    action_plan: IpsActionPlan,
    analysis: IpsAnalysis,
    propuestas: list[IpsPropuesta],
    user_id: str,
) -> WorkPlan:
    if action_plan.work_plan_id:
        existing = (
            db.query(WorkPlan)
            .filter(
                WorkPlan.id == action_plan.work_plan_id,
                WorkPlan.organization_id == action_plan.organization_id,
            )
            .first()
        )
        if existing:
            return existing

    prioridad = _map_prioridad(propuestas)
    vencimiento = _latest_vencimiento(propuestas)
    objective = f"Plan de acción IPS — {analysis.ips_name}"
    request = analysis.request_text or objective

    work_plan = WorkPlan(
        organization_id=action_plan.organization_id,
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request=request[:4000],
        objective=objective,
        status=WorkPlanStatus.READY,
        prioridad=prioridad,
        vencimiento=vencimiento,
        summary=f"Origen SALUD · análisis {analysis.id}",
    )
    db.add(work_plan)
    db.flush()

    publish(
        EventMessage(
            event_type=WorkEventType.WORK_REQUESTED,
            organization_id=action_plan.organization_id,
            work_plan_id=work_plan.id,
            user_id=user_id,
            payload={
                "origen": "SALUD",
                "analysis_id": analysis.id,
                "action_plan_id": action_plan.id,
            },
        ),
        db,
    )

    tasks_data = json.loads(action_plan.tasks_json or "[]")
    propuesta_by_id = {p.id: p for p in propuestas}
    for i, task_data in enumerate(tasks_data):
        propuesta = propuesta_by_id.get(task_data.get("propuesta_id", ""))
        if not propuesta:
            continue
        task_data["action_plan_id"] = action_plan.id
        employee_id = resolve_unique_employee(
            db, action_plan.organization_id, propuesta.responsable_sugerido
        )
        task = EmployeeTask(
            organization_id=action_plan.organization_id,
            work_plan_id=work_plan.id,
            employee_id=employee_id,
            sequence=int(task_data.get("secuencia") or (i + 1)),
            title=task_data.get("titulo") or propuesta.problema,
            executor_type=ExecutorType.PYTHON,
            status=EmployeeTaskStatus.READY,
            inputs_json=json.dumps(build_task_payload(propuesta, task_data), ensure_ascii=False),
        )
        db.add(task)
        db.flush()
        publish(
            EventMessage(
                event_type=WorkEventType.TASK_CREATED,
                organization_id=action_plan.organization_id,
                work_plan_id=work_plan.id,
                task_id=task.id,
                user_id=user_id,
                payload={"origen": "SALUD", "propuesta_id": propuesta.id},
            ),
            db,
        )

    publish(
        EventMessage(
            event_type=WorkEventType.WORK_PLANNED,
            organization_id=action_plan.organization_id,
            work_plan_id=work_plan.id,
            user_id=user_id,
            payload={"origen": "SALUD", "tareas": len(tasks_data)},
        ),
        db,
    )

    action_plan.work_plan_id = work_plan.id
    if not analysis.work_plan_id:
        analysis.work_plan_id = work_plan.id
    db.commit()
    db.refresh(work_plan)
    return work_plan
