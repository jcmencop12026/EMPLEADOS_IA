"""Suscriptor de eventos — Auditor Empleados IA."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.events.bus import EventMessage, subscribe
from app.models import User
from app.services.employee_audit_service import AUDIT_EVENT_GUARD, AUDIT_LOOP_EVENT_PREFIX, execute_audit, process_scheduled_audits

logger = logging.getLogger(__name__)

EVENT_TRIGGERS = frozenset(
    {
        "work.failed",
        "EXECUTION_FAILED",
        "FINOPS_LIMIT_REACHED",
        "employee.certification_failed",
        "AUTOMATION_FAILED",
        "approval.completed",
    }
)


def _should_skip(event: EventMessage) -> bool:
    payload = event.payload or {}
    if payload.get(AUDIT_EVENT_GUARD):
        return True
    if event.event_type == "employee.audit.scheduled":
        return False
    if event.event_type.startswith(AUDIT_LOOP_EVENT_PREFIX):
        return True
    return False


def _resolve_user(db: Session, org_id: str, user_id: str | None) -> User | None:
    if user_id:
        user = db.query(User).filter(User.id == user_id, User.organization_id == org_id).first()
        if user:
            return user
    return db.query(User).filter(User.organization_id == org_id, User.role == "admin").first()


def _on_domain_event(event: EventMessage, db: Session) -> None:
    if _should_skip(event):
        return
    if event.event_type == "employee.audit.scheduled":
        try:
            process_scheduled_audits(db)
        except Exception:
            logger.exception("Scheduled employee audit failed")
        return
    if event.event_type not in EVENT_TRIGGERS:
        return
    payload = event.payload or {}
    employee_id = payload.get("employee_id")
    if not employee_id and event.work_plan_id:
        from app.orchestration_models import WorkPlan

        plan = db.query(WorkPlan).filter(WorkPlan.id == event.work_plan_id).first()
        if plan:
            employee_id = plan.employee_id
    if not employee_id:
        return
    user = _resolve_user(db, event.organization_id, event.user_id)
    if not user:
        return
    try:
        execute_audit(
            db,
            user,
            organization_id=event.organization_id,
            employee_id=str(employee_id),
            trigger_type="EVENT",
            trigger_ref=event.event_type,
        )
    except Exception:
        logger.exception("Employee audit event handler failed for %s", event.event_type)


def register_employee_audit_event_handlers() -> None:
    subscribe(_on_domain_event)

