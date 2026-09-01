"""API — Demo comercial ficticia EIAAX (V1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import demo_comercial_service as svc
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/demo-comercial", tags=["demo-comercial"])


@router.get("/manifest")
def get_manifest(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.get_manifest(db, user.organization_id)


@router.post("/semilla")
def seed_demo(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("evaluacion.manage")),
):
    try:
        result = svc.seed_demo_comercial(db, user.organization_id, user.id)
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/presentacion/{expediente_id}")
def get_presentacion(
    expediente_id: str,
    audiencia: str = Query("GERENCIA"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return svc.build_presentacion(
            db,
            user.organization_id,
            expediente_id,
            audiencia=audiencia,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/informes-periodicos")
def informes_periodicos(
    user: User = Depends(get_current_user),
):
    return {"plantillas": svc.informes_periodicos_plantillas()}
