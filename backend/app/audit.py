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
    db.add(
        AuditLog(
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            detail=detail,
        )
    )
    db.commit()
