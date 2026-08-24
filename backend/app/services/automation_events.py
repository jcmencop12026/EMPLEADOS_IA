"""Suscriptor del bus de eventos para disparar automatizaciones INTERNAL_EVENT (CURSOR-810)."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.events.bus import EventMessage, subscribe
from app.automation_models import AutomationRun

logger = logging.getLogger(__name__)

_LOOP_GUARD = "_automation_loop_guard"


def _should_ignore_event(event: EventMessage, db: Session) -> bool:
    payload = event.payload or {}
    if payload.get(_LOOP_GUARD):
        return True
    if event.event_type.startswith("automation."):
        return True
    if event.work_plan_id:
        linked = (
            db.query(AutomationRun.id)
            .filter(AutomationRun.work_plan_id == event.work_plan_id)
            .first()
        )
        if linked:
            return True
    return False


def _on_domain_event(event: EventMessage, db: Session) -> None:
    if _should_ignore_event(event, db):
        return
    from app.services.automation_service import trigger_internal_event

    try:
        trigger_internal_event(
            db,
            org_id=event.organization_id,
            event_type=event.event_type,
            payload=event.payload,
            user_id=event.user_id,
        )
    except Exception:
        logger.exception("Automation event handler failed for %s", event.event_type)


def register_automation_event_handlers() -> None:
    subscribe(_on_domain_event)


def automation_loop_guard_payload(extra: dict | None = None) -> dict:
  """Marca eventos originados por automatizaciones para evitar bucles."""
  data = dict(extra or {})
  data[_LOOP_GUARD] = True
  return data
