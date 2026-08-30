"""API — Bandeja unificada de trabajo humano."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.services import trabajo_service as svc

router = APIRouter(prefix="/api/trabajo", tags=["Trabajo humano"])


def _require_trabajo_access(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    if not svc.can_access_trabajo(user, db):
        raise HTTPException(status_code=403, detail="No tiene permisos para acceder a la bandeja de trabajo.")
    return user


@router.get("/items")
def list_trabajo_items(
    organization_id: str | None = Query(None, description="Solo SuperAdmin/plataforma"),
    q: str | None = None,
    estado: str | None = None,
    prioridad: str | None = None,
    tipo: str | None = None,
    modulo: str | None = None,
    responsable_id: str | None = None,
    employee_id: str | None = Query(None, description="Filtrar por empleado IA (metadata)"),
    vencimiento: str | None = Query(None, description="vencida | proxima | sin_limite"),
    requires_action: bool | None = None,
    case_id: str | None = Query(None, description="Filtrar por case_id de soporte"),
    sort: str = Query("prioridad", description="prioridad | created_at | fecha_limite | asunto"),
    sort_dir: str = Query("desc", description="asc | desc"),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(_require_trabajo_access),
):
    try:
        return svc.list_items(
            db,
            user,
            organization_id=organization_id,
            q=q,
            estado=estado,
            prioridad=prioridad,
            tipo=tipo,
            modulo=modulo,
            responsable_id=responsable_id,
            employee_id=employee_id,
            vencimiento=vencimiento,
            requires_action=requires_action,
            case_id=case_id,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/resumen")
def trabajo_resumen(
    organization_id: str | None = Query(None, description="Solo SuperAdmin/plataforma"),
    db: Session = Depends(get_db),
    user: User = Depends(_require_trabajo_access),
):
    try:
        return svc.resumen(db, user, organization_id=organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
