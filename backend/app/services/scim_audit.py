"""Auditoría y métricas SCIM (1380)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.scim_models import ScimAuditLog, ScimMetrics


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def log_scim_audit(
    db: Session,
    *,
    organization_id: str,
    action: str,
    result: str,
    token_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    correlation_id: str | None = None,
) -> None:
    db.add(
        ScimAuditLog(
            organization_id=organization_id,
            token_id=token_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            detail=detail[:500] if detail else None,
            correlation_id=correlation_id,
        )
    )


def record_scim_metric(
    db: Session,
    organization_id: str,
    *,
    requests_delta: int = 0,
    errors_delta: int = 0,
    conflicts_delta: int = 0,
    rate_limited_delta: int = 0,
    users_provisioned_delta: int = 0,
    users_active_delta: int = 0,
    users_deactivated_delta: int = 0,
    latency_ms: int | None = None,
) -> None:
    row = db.query(ScimMetrics).filter(ScimMetrics.organization_id == organization_id).first()
    if not row:
        row = ScimMetrics(organization_id=organization_id)
        db.add(row)
        db.flush()
    row.requests_total += requests_delta
    row.errors_count += errors_delta
    row.conflicts_count += conflicts_delta
    row.rate_limited_count += rate_limited_delta
    row.users_provisioned += users_provisioned_delta
    row.users_active += users_active_delta
    row.users_deactivated += users_deactivated_delta
    if latency_ms is not None:
        row.last_latency_ms = latency_ms
    row.last_sync_at = _utcnow()


def get_metrics(db: Session, organization_id: str) -> dict:
    row = db.query(ScimMetrics).filter(ScimMetrics.organization_id == organization_id).first()
    if not row:
        return {
            "users_provisioned": 0, "users_active": 0, "users_deactivated": 0,
            "errors_count": 0, "conflicts_count": 0, "rate_limited_count": 0,
            "requests_total": 0, "last_sync_at": None, "last_latency_ms": None,
            "tokens_active": 0, "tokens_expired": 0,
        }
    from app.scim_models import ScimToken
    now = _utcnow()
    tokens = db.query(ScimToken).filter(ScimToken.organization_id == organization_id).all()
    active_tokens = sum(1 for t in tokens if not t.revoked_at and (not t.expires_at or t.expires_at > now))
    expired_tokens = sum(1 for t in tokens if t.expires_at and t.expires_at <= now)
    return {
        "users_provisioned": row.users_provisioned,
        "users_active": row.users_active,
        "users_deactivated": row.users_deactivated,
        "errors_count": row.errors_count,
        "conflicts_count": row.conflicts_count,
        "rate_limited_count": row.rate_limited_count,
        "requests_total": row.requests_total,
        "last_sync_at": row.last_sync_at.isoformat() if row.last_sync_at else None,
        "last_latency_ms": row.last_latency_ms,
        "tokens_active": active_tokens,
        "tokens_expired": expired_tokens,
    }


def list_audit(db: Session, organization_id: str, limit: int = 50) -> list[ScimAuditLog]:
    return (
        db.query(ScimAuditLog)
        .filter(ScimAuditLog.organization_id == organization_id)
        .order_by(ScimAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
