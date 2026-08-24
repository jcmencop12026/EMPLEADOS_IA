from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    action: str,
    organization_id: str | None = None,
    user_id: str | None = None,
    detail: str | None = None,
) -> None:
    from app.services.execution_guard import current_fence_token

    db.add(
        AuditLog(
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            detail=detail,
        )
    )
    if current_fence_token() is None:
        db.commit()
