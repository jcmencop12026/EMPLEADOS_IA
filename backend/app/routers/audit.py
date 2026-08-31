from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.empresa_audit_labels import etiqueta_accion, sanitizar_detalle
from app.models import AuditLog, User
from app.permissions import require_permission

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
def list_audit_logs(
    user: User = Depends(require_permission("audit.view")),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    accion: str | None = None,
    user_id: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
):
    q = db.query(AuditLog).filter(AuditLog.organization_id == user.organization_id)
    if accion:
        q = q.filter(AuditLog.action.contains(accion))
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if desde:
        q = q.filter(AuditLog.created_at >= desde)
    if hasta:
        q = q.filter(AuditLog.created_at <= hasta)
    rows = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    usuarios: dict[str, str] = {}
    result = []
    for r in rows:
        if r.user_id and r.user_id not in usuarios:
            u = db.get(User, r.user_id)
            usuarios[r.user_id] = u.username if u else r.user_id
        result.append(
            {
                "id": r.id,
                "action": r.action,
                "accion_etiqueta": etiqueta_accion(r.action),
                "detail": sanitizar_detalle(r.detail),
                "user_id": r.user_id,
                "usuario": usuarios.get(r.user_id) if r.user_id else None,
                "organization_id": r.organization_id,
                "created_at": r.created_at,
            }
        )
    return result
