from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.empresa_audit_labels import etiqueta_accion
from app.models import AuditLog, User
from app.permissions import require_permission
from app.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogOut])
def list_audit_logs(
    user: User = Depends(require_permission("audit.view")),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    accion: str | None = Query(None),
):
    q = db.query(AuditLog).filter(AuditLog.organization_id == user.organization_id)
    if accion:
        q = q.filter(AuditLog.action.contains(accion))
    rows = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        AuditLogOut(
            id=r.id,
            action=r.action,
            detail=r.detail,
            user_id=r.user_id,
            created_at=r.created_at,
            accion_etiqueta=etiqueta_accion(r.action),
        )
        for r in rows
    ]
