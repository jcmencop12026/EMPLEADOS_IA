from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, User
from app.permissions import require_permission
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    user: User = Depends(require_permission("audit.view")),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return rows
