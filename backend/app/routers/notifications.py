import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.database import get_db
from app.deps import get_current_user
from app.models import AlertRule, Notification, User
from app.permissions import check_permission, user_permissions
from app.schemas_notifications import AlertRuleIn

notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])
rules_router = APIRouter(prefix="/api/alert-rules", tags=["alert-rules"])
ALLOWED_TRANSITIONS = {
    "NEW": {"READ", "ACKNOWLEDGED", "DISMISSED"},
    "READ": {"ACKNOWLEDGED", "DISMISSED"},
    "ACKNOWLEDGED": {"DISMISSED"},
    "DISMISSED": set(),
}


def _visible(query, user: User):
    query = query.filter(Notification.organization_id == user.organization_id)
    if "notification.manage" not in user_permissions(user):
        query = query.filter(
            or_(Notification.recipient_user_id.is_(None), Notification.recipient_user_id == user.id),
            or_(Notification.recipient_role.is_(None), Notification.recipient_role == user.role),
        )
    return query


def _notification_out(row: Notification) -> dict:
    return {
        "id": row.id, "organization_id": row.organization_id, "type": row.type,
        "severity": row.severity, "title": row.title, "message": row.message,
        "source_type": row.source_type, "source_id": row.source_id,
        "recipient_user_id": row.recipient_user_id, "recipient_role": row.recipient_role,
        "status": row.status, "channel": row.channel, "created_at": row.created_at,
        "read_at": row.read_at, "acknowledged_at": row.acknowledged_at,
        "expires_at": row.expires_at,
        "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
    }


def _get_notification(notification_id: str, db: Session, user: User) -> Notification:
    row = _visible(db.query(Notification).filter(Notification.id == notification_id), user).first()
    if not row:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return row


@notifications_router.get("")
def list_notifications(
    status_filter: str | None = Query(None, alias="status"), severity: str | None = None,
    type_filter: str | None = Query(None, alias="type"), user_id: str | None = None,
    date_from: datetime | None = None, date_to: datetime | None = None,
    search: str | None = None, sort: str = "desc", limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    check_permission(user, "notification.view")
    query = _visible(db.query(Notification), user)
    if status_filter: query = query.filter(Notification.status == status_filter.upper())
    if severity: query = query.filter(Notification.severity == severity.upper())
    if type_filter: query = query.filter(Notification.type == type_filter.upper())
    if user_id: query = query.filter(Notification.recipient_user_id == user_id)
    if date_from: query = query.filter(Notification.created_at >= date_from)
    if date_to: query = query.filter(Notification.created_at <= date_to)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Notification.title.ilike(pattern), Notification.message.ilike(pattern)))
    order = Notification.created_at.asc() if sort == "asc" else Notification.created_at.desc()
    return [_notification_out(row) for row in query.order_by(order).limit(limit).all()]


@notifications_router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "notification.view")
    count = _visible(db.query(Notification).filter(Notification.status == "NEW"), user).count()
    return {"count": count}


@notifications_router.get("/{notification_id}")
def get_notification(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "notification.view")
    return _notification_out(_get_notification(notification_id, db, user))


def _transition(notification_id: str, target: str, db: Session, user: User):
    permission = "notification.acknowledge" if target == "ACKNOWLEDGED" else "notification.view"
    if target == "READ": permission = "notification.view"
    check_permission(user, permission)
    row = _get_notification(notification_id, db, user)
    if target not in ALLOWED_TRANSITIONS.get(row.status, set()):
        raise HTTPException(status_code=409, detail=f"Transición inválida: {row.status} -> {target}")
    now = datetime.now(timezone.utc)
    row.status = target
    if target == "READ": row.read_at = row.read_at or now
    if target == "ACKNOWLEDGED":
        row.read_at = row.read_at or now
        row.acknowledged_at = now
    db.commit()
    write_audit(db, action=f"notification.{target.lower()}", organization_id=user.organization_id,
                user_id=user.id, detail=notification_id)
    return _notification_out(row)


@notifications_router.post("/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _transition(notification_id, "READ", db, user)


@notifications_router.post("/{notification_id}/acknowledge")
def acknowledge(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _transition(notification_id, "ACKNOWLEDGED", db, user)


@notifications_router.post("/{notification_id}/dismiss")
def dismiss(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _transition(notification_id, "DISMISSED", db, user)


def _validate_recipient_user(db: Session, org_id: str, recipient_user_id: str | None) -> None:
    if not recipient_user_id:
        return
    valid = (
        db.query(User)
        .filter(User.id == recipient_user_id, User.organization_id == org_id)
        .first()
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Destinatario inválido")


def _rule_out(row: AlertRule) -> dict:
    return {"id": row.id, "organization_id": row.organization_id, "name": row.name,
            "event_type": row.event_type, "condition": json.loads(row.condition_json) if row.condition_json else None,
            "severity": row.severity, "recipient_user_id": row.recipient_user_id,
            "recipient_role": row.recipient_role, "channel": row.channel, "enabled": row.enabled,
            "created_by": row.created_by, "created_at": row.created_at, "updated_at": row.updated_at}


def _get_rule(rule_id: str, db: Session, user: User) -> AlertRule:
    row = db.query(AlertRule).filter(AlertRule.id == rule_id, AlertRule.organization_id == user.organization_id).first()
    if not row: raise HTTPException(status_code=404, detail="Regla no encontrada")
    return row


@rules_router.get("")
def list_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "alert_rule.view")
    return [_rule_out(row) for row in db.query(AlertRule).filter(AlertRule.organization_id == user.organization_id).order_by(AlertRule.name).all()]


@rules_router.post("", status_code=status.HTTP_201_CREATED)
def create_rule(body: AlertRuleIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "alert_rule.manage")
    _validate_recipient_user(db, user.organization_id, body.recipient_user_id)
    row = AlertRule(organization_id=user.organization_id, created_by=user.id, name=body.name,
                    event_type=body.event_type.upper(), condition_json=json.dumps(body.condition) if body.condition else None,
                    severity=body.severity, recipient_user_id=body.recipient_user_id,
                    recipient_role=body.recipient_role, channel=body.channel, enabled=body.enabled)
    db.add(row); db.commit(); db.refresh(row)
    write_audit(db, action="alert_rule.created", organization_id=user.organization_id, user_id=user.id, detail=row.id)
    return _rule_out(row)


@rules_router.put("/{rule_id}")
def update_rule(rule_id: str, body: AlertRuleIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "alert_rule.manage")
    row = _get_rule(rule_id, db, user)
    _validate_recipient_user(db, user.organization_id, body.recipient_user_id)
    for key in ("name", "severity", "recipient_user_id", "recipient_role", "channel", "enabled"):
        setattr(row, key, getattr(body, key))
    row.event_type = body.event_type.upper(); row.condition_json = json.dumps(body.condition) if body.condition else None
    db.commit(); write_audit(db, action="alert_rule.updated", organization_id=user.organization_id, user_id=user.id, detail=row.id)
    return _rule_out(row)


def _toggle(rule_id: str, enabled: bool, db: Session, user: User):
    check_permission(user, "alert_rule.manage")
    row = _get_rule(rule_id, db, user); row.enabled = enabled; db.commit()
    write_audit(db, action=f"alert_rule.{'enabled' if enabled else 'disabled'}",
                organization_id=user.organization_id, user_id=user.id, detail=row.id)
    return _rule_out(row)


@rules_router.post("/{rule_id}/enable")
def enable_rule(rule_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _toggle(rule_id, True, db, user)


@rules_router.post("/{rule_id}/disable")
def disable_rule(rule_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _toggle(rule_id, False, db, user)
