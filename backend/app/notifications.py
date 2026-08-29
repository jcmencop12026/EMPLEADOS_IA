"""Motor de notificaciones y alertas — CODEX-820."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.events.bus import EventMessage, subscribe
from app.models import AlertRule, Notification
from app.notification_recipients import validate_notification_recipient

logger = logging.getLogger(__name__)

SUPPORTED_EVENTS = {
    "EMPLOYEE_CREATED", "EMPLOYEE_CERTIFIED", "EMPLOYEE_ACTIVATED",
    "EXECUTION_STARTED", "EXECUTION_SUCCEEDED", "EXECUTION_FAILED",
    "APPROVAL_REQUIRED", "APPROVAL_APPROVED", "APPROVAL_REJECTED",
    "TOOL_DENIED", "TENANT_SECURITY_EVENT", "FINOPS_LIMIT_REACHED", "SYSTEM_ERROR",
    "AUTOMATION_FAILED", "AUTOMATION_COMPLETED",
    "SUPPORT_CASE_ASSIGNED", "SUPPORT_CASE_STATUS", "SUPPORT_CASE_RESOLVED",
    "SUPPORT_CASE_COMMENT", "SUPPORT_SLA_WARNING",
}

EVENT_ALIASES = {
    "approval.required": "APPROVAL_REQUIRED",
    "task.started": "EXECUTION_STARTED",
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


def normalize_event_type(event_type: str, payload: dict[str, Any] | None = None) -> str:
    body = payload or {}
    raw_type = str(event_type)
    if raw_type == "approval.completed":
        return "APPROVAL_APPROVED" if body.get("decision") == "approve" else "APPROVAL_REJECTED"
    return EVENT_ALIASES.get(raw_type, raw_type.upper())


def resolve_event_id(
    event_type: str,
    organization_id: str,
    source_id: str | None,
    payload: dict[str, Any] | None,
    *,
    rule_id: str | None = None,
) -> str:
    body = payload or {}
    explicit = body.get("event_id")
    if explicit:
        return str(explicit)
    stable = "|".join(
        [
            str(event_type),
            str(organization_id),
            str(source_id or ""),
            str(rule_id or ""),
            str(body.get("correlation_id") or ""),
            str(body.get("approval_id") or ""),
            str(body.get("kind") or ""),
        ]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def build_idempotency_key(
    *,
    event_id: str,
    rule_id: str | None,
    recipient_user_id: str | None,
    notification_type: str,
) -> str:
    return f"{event_id}|{rule_id or '-'}|{recipient_user_id or '-'}|{notification_type}"


def _delivery_channel(notification: Notification) -> str:
    channel = notification.channel or "IN_APP"
    notification.channel = channel
    return channel


def _persist_notification(
    db: Session,
    *,
    organization_id: str,
    event_id: str,
    rule_id: str | None,
    notification: Notification,
) -> Notification | None:
    notification.event_id = event_id
    notification.rule_id = rule_id
    notification.idempotency_key = build_idempotency_key(
        event_id=event_id,
        rule_id=rule_id,
        recipient_user_id=notification.recipient_user_id,
        notification_type=notification.type,
    )
    if not validate_notification_recipient(
        db,
        organization_id=organization_id,
        recipient_user_id=notification.recipient_user_id,
    ):
        return None
    existing = (
        db.query(Notification)
        .filter(
            Notification.organization_id == organization_id,
            Notification.idempotency_key == notification.idempotency_key,
        )
        .first()
    )
    if existing:
        return existing
    channel = _delivery_channel(notification)
    try:
        with db.begin_nested():
            CHANNELS[channel].deliver(notification, db)
            db.flush()
    except IntegrityError:
        return (
            db.query(Notification)
            .filter(
                Notification.organization_id == organization_id,
                Notification.idempotency_key == notification.idempotency_key,
            )
            .first()
        )
    return notification


def emit_event(
    event_type: str,
    organization_id: str,
    source_type: str,
    source_id: str | None,
    payload: dict[str, Any] | None,
    db: Session,
    *,
    commit: bool = True,
    event_id: str | None = None,
) -> list[Notification]:
    body = payload or {}
    normalized = normalize_event_type(event_type, body)
    resolved_event_id = event_id or resolve_event_id(
        normalized, organization_id, source_id, body
    )
    rules = db.query(AlertRule).filter(
        AlertRule.organization_id == organization_id,
        AlertRule.event_type == normalized,
        AlertRule.enabled.is_(True),
    ).all()
    created: list[Notification] = []
    matched_rules = 0
    denied_recipient = False
    for rule in rules:
        if not _matches(rule, body):
            continue
        matched_rules += 1
        if not validate_notification_recipient(
            db,
            organization_id=organization_id,
            recipient_user_id=rule.recipient_user_id,
        ):
            denied_recipient = True
            continue
        notification = Notification(
            organization_id=organization_id,
            type=body.get("notification_type", "WARNING"),
            severity=rule.severity,
            title=body.get("title", rule.name),
            message=body.get("message", f"Evento {normalized}"),
            source_type=source_type,
            source_id=source_id,
            recipient_user_id=rule.recipient_user_id,
            recipient_role=rule.recipient_role,
            channel=rule.channel,
            metadata_json=json.dumps(body, ensure_ascii=False),
        )
        persisted = _persist_notification(
            db,
            organization_id=organization_id,
            event_id=resolved_event_id,
            rule_id=rule.id,
            notification=notification,
        )
        if persisted:
            created.append(persisted)
    if (
        not created
        and normalized in DEFAULTS
        and not denied_recipient
        and matched_rules == 0
    ):
        notification_type, severity, title = DEFAULTS[normalized]
        recipient_user_id = body.get("recipient_user_id")
        notification = Notification(
            organization_id=organization_id,
            type=notification_type,
            severity=severity,
            title=body.get("title", title),
            message=body.get("message", f"Evento {normalized}"),
            source_type=source_type,
            source_id=source_id,
            recipient_user_id=recipient_user_id,
            recipient_role=body.get("recipient_role"),
            channel="IN_APP",
            metadata_json=json.dumps(body, ensure_ascii=False),
        )
        persisted = _persist_notification(
            db,
            organization_id=organization_id,
            event_id=resolved_event_id,
            rule_id=None,
            notification=notification,
        )
        if persisted:
            created.append(persisted)
    if commit:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            keys = [item.idempotency_key for item in created if item.idempotency_key]
            created = (
                db.query(Notification)
                .filter(
                    Notification.organization_id == organization_id,
                    Notification.idempotency_key.in_(keys),
                )
                .all()
                if keys
                else []
            )
    return created


def _event_subscriber(event: EventMessage, db: Session) -> None:
    payload = dict(event.payload or {})
    if payload.get("employee_id"):
        source_type, source_id = "employee", payload["employee_id"]
    else:
        source_type, source_id = "work_plan", event.work_plan_id or event.task_id
    event_id = resolve_event_id(
        str(event.event_type),
        event.organization_id,
        source_id,
        payload,
    )
    payload.setdefault("event_id", event_id)
    emit_event(
        str(event.event_type),
        event.organization_id,
        source_type,
        source_id,
        payload,
        db,
        commit=False,
        event_id=event_id,
    )


subscribe(_event_subscriber)
