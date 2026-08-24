import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
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


def subscribe(handler: Callable[[EventMessage, Session], None]) -> None:
    _subscribers.append(handler)


def _audit_subscriber(event: EventMessage, db: Session) -> None:
    write_audit(
        db,
        action=event.event_type,
        organization_id=event.organization_id,
        user_id=event.user_id,
        detail=json.dumps(event.payload or {}, ensure_ascii=False)[:4000],
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
    if current_fence_token() is None:
        db.commit()


subscribe(_audit_subscriber)
subscribe(_persist_subscriber)


def publish(event: EventMessage, db: Session) -> None:
    for handler in _subscribers:
        handler(event, db)
