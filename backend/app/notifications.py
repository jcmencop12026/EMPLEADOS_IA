import json
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.events.bus import EventMessage, subscribe
from app.models import AlertRule, Notification

SUPPORTED_EVENTS = {
    "EMPLOYEE_CREATED", "EMPLOYEE_CERTIFIED", "EMPLOYEE_ACTIVATED",
    "EXECUTION_STARTED", "EXECUTION_SUCCEEDED", "EXECUTION_FAILED",
    "APPROVAL_REQUIRED", "APPROVAL_APPROVED", "APPROVAL_REJECTED",
    "TOOL_DENIED", "TENANT_SECURITY_EVENT", "FINOPS_LIMIT_REACHED", "SYSTEM_ERROR",
    "AUTOMATION_FAILED", "AUTOMATION_COMPLETED",
}

EVENT_ALIASES = {
    "approval.required": "APPROVAL_REQUIRED",
    "approval.completed": "APPROVAL_APPROVED",
    "work.failed": "EXECUTION_FAILED",
    "task.failed": "EXECUTION_FAILED",
    "work.completed": "EXECUTION_SUCCEEDED",
    "employee.created": "EMPLOYEE_CREATED",
    "employee.certified": "EMPLOYEE_CERTIFIED",
    "employee.activated": "EMPLOYEE_ACTIVATED",
}

DEFAULTS = {
    "APPROVAL_REQUIRED": ("APPROVAL_REQUIRED", "HIGH", "Aprobación requerida"),
    "EXECUTION_FAILED": ("TASK_FAILED", "HIGH", "Ejecución fallida"),
    "TENANT_SECURITY_EVENT": ("SECURITY", "CRITICAL", "Evento de seguridad"),
    "TOOL_DENIED": ("SECURITY", "HIGH", "Herramienta denegada"),
    "FINOPS_LIMIT_REACHED": ("WARNING", "HIGH", "Límite FinOps alcanzado"),
    "SYSTEM_ERROR": ("SYSTEM", "CRITICAL", "Error del sistema"),
}


@dataclass
class NotificationEnvelope:
    event_type: str
    organization_id: str
    source_type: str
    source_id: str | None
    payload: dict[str, Any]


class NotificationChannel(Protocol):
    name: str
    def deliver(self, notification: Notification, db: Session) -> None: ...


class InAppChannel:
    name = "IN_APP"
    def deliver(self, notification: Notification, db: Session) -> None:
        db.add(notification)


CHANNELS: dict[str, NotificationChannel] = {"IN_APP": InAppChannel()}


def _matches(rule: AlertRule, payload: dict[str, Any]) -> bool:
    config = json.loads(rule.condition_json) if rule.condition_json else {}
    expected = config.get("match", config)
    return all(payload.get(key) == value for key, value in expected.items())


def emit_event(event_type: str, organization_id: str, source_type: str, source_id: str | None,
               payload: dict[str, Any] | None, db: Session) -> list[Notification]:
    normalized = EVENT_ALIASES.get(str(event_type), str(event_type).upper())
    body = payload or {}
    rules = db.query(AlertRule).filter(
        AlertRule.organization_id == organization_id,
        AlertRule.event_type == normalized,
        AlertRule.enabled.is_(True),
    ).all()
    created: list[Notification] = []
    for rule in rules:
        if not _matches(rule, body):
            continue
        notification = Notification(
            organization_id=organization_id, type=body.get("notification_type", "WARNING"),
            severity=rule.severity, title=body.get("title", rule.name),
            message=body.get("message", f"Evento {normalized}"), source_type=source_type,
            source_id=source_id, recipient_user_id=rule.recipient_user_id,
            recipient_role=rule.recipient_role, channel=rule.channel,
            metadata_json=json.dumps(body, ensure_ascii=False),
        )
        CHANNELS[rule.channel].deliver(notification, db)
        created.append(notification)
    if not created and normalized in DEFAULTS:
        notification_type, severity, title = DEFAULTS[normalized]
        notification = Notification(
            organization_id=organization_id, type=notification_type, severity=severity,
            title=body.get("title", title), message=body.get("message", f"Evento {normalized}"),
            source_type=source_type, source_id=source_id,
            recipient_user_id=body.get("recipient_user_id"), recipient_role=body.get("recipient_role"),
            metadata_json=json.dumps(body, ensure_ascii=False),
        )
        CHANNELS["IN_APP"].deliver(notification, db)
        created.append(notification)
    db.commit()
    return created


def _event_subscriber(event: EventMessage, db: Session) -> None:
    emit_event(str(event.event_type), event.organization_id, "work_plan",
               event.work_plan_id or event.task_id, event.payload, db)


subscribe(_event_subscriber)
