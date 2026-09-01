"""API — Centro de Control Estratégico/Empresa (V1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import strategic_control_service as svc

router = APIRouter(prefix="/api/centro-estrategico", tags=["Centro Estratégico"])


@router.get("/cockpit")
def get_cockpit(
    lectura: str = Query("resumen", description="resumen | gerencia | operacion | sistemas | financiero"),
    modo_comite: bool = Query(False, description="Modo comité — navegación entre lecturas"),
    organization_id: str | None = Query(None, description="Solo plataforma/SuperAdmin"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("strategic_control.view")),
):
    try:
        org_id = svc.resolve_organization_id(db, user, organization_id)
        return svc.get_cockpit(db, user, org_id, lectura=lectura, modo_comite=modo_comite)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/lecturas")
def get_lecturas_config(
    user: User = Depends(require_permission("strategic_control.view")),
):
    return {"lecturas": svc.LECTURAS, "semantica": svc.SEMANTICA_VALOR}
