import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.events.subscriber_session import SubscriberSession
from app.orchestration_models import WorkEvent


@dataclass
class EventMessage:
    event_type: str
    organization_id: str
    work_plan_id: str | None = None
    task_id: str | None = None
    payload: dict[str, Any] | None = None
    user_id: str | None = None


_subscribers: list[Callable[[EventMessage, Session], None]] = []
logger = logging.getLogger(__name__)


def subscribe(handler: Callable[[EventMessage, Session], None]) -> None:
    _subscribers.append(handler)


def _audit_subscriber(event: EventMessage, db: Session) -> None:
    write_audit(
        db,
        action=event.event_type,
        organization_id=event.organization_id,
        user_id=event.user_id,
        detail=json.dumps(event.payload or {}, ensure_ascii=False)[:4000],
        commit=False,
    )


def _persist_subscriber(event: EventMessage, db: Session) -> None:
    from app.services.execution_guard import current_fence_token

    db.add(
        WorkEvent(
            organization_id=event.organization_id,
            work_plan_id=event.work_plan_id,
            task_id=event.task_id,
            event_type=event.event_type,
            payload_json=json.dumps(event.payload or {}, ensure_ascii=False),
        )
    )
    # El commit lo gestiona publish() vía SAVEPOINT; no commitear aquí.



subscribe(_audit_subscriber)
subscribe(_persist_subscriber)


def publish(event: EventMessage, db: Session) -> None:
    for handler in _subscribers:
        try:
            # A SAVEPOINT isolates optional subscribers from the domain transaction.
            # Subscribers reciben sesión sin commit/rollback para no escapar del SAVEPOINT.
            with db.begin_nested():
                handler(event, SubscriberSession(db))
                db.flush()
        except Exception as exc:  # noqa: BLE001 - subscriber isolation is intentional
            handler_name = getattr(handler, "__qualname__", repr(handler))
            logger.exception("Event subscriber %s failed for %s", handler_name, event.event_type)
            try:
                with db.begin_nested():
                    write_audit(
                        db,
                        action="event.subscriber_failed",
                        organization_id=event.organization_id,
                        user_id=event.user_id,
                        detail=json.dumps(
                            {
                                "event_type": str(event.event_type),
                                "subscriber": handler_name,
                                "error": str(exc),
                            },
                            ensure_ascii=False,
                        )[:4000],
                        commit=False,
                    )
                    db.flush()
            except Exception:  # keep logging available even if audit persistence fails
                logger.exception("Could not audit subscriber failure for %s", event.event_type)
