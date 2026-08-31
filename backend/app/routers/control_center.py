"""API — Centro de Control ejecutivo (Bloque 1230)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import control_center_service as svc

router = APIRouter(prefix="/api/centro-control", tags=["Centro de Control"])


@router.get("/resumen-ejecutivo")
def get_executive_summary(
    periodo: str | None = Query("mtd", description="mtd | 7d | 30d"),
    employee_id: str | None = None,
    proceso: str | None = None,
    estado: str | None = None,
    organization_id: str | None = Query(None, description="Solo SuperAdmin/plataforma"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("control_center.view")),
):
    try:
        org_id = svc.resolve_organization_id(db, user, organization_id)
        return svc.get_executive_summary(
            db,
            user,
            periodo=periodo,
            employee_id=employee_id,
            proceso=proceso,
            estado=estado,
            organization_id=org_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/indicadores-config")
def get_indicator_config(
    user: User = Depends(require_permission("control_center.view")),
):
    return {"indicadores": svc.EXECUTIVE_INDICATOR_DEFS}


@router.get("/operacional")
def get_operational_summary(
    periodo: str | None = Query("mtd", description="mtd | 7d | 30d"),
    employee_id: str | None = None,
    proceso: str | None = None,
    estado: str | None = None,
    organization_id: str | None = Query(None, description="Solo SuperAdmin/plataforma"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("control_center.view")),
):
    from app.services import operational_control_service as ops_ctrl

    try:
        org_id = svc.resolve_organization_id(db, user, organization_id)
        return ops_ctrl.get_operational_summary(
            db,
            user,
            org_id,
            periodo=periodo,
            employee_id=employee_id,
            proceso=proceso,
            estado=estado,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ejecuciones/{plan_id}/detalle-operacional")
def get_execution_operational_detail(
    plan_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("control_center.view")),
):
    from app.services import operational_control_service as ops_ctrl

    try:
        org_id = svc.resolve_organization_id(db, user, organization_id)
        detail = ops_ctrl.get_execution_operational_detail(db, org_id, plan_id)
        if detail.get("not_found"):
            raise HTTPException(status_code=404, detail=detail.get("mensaje", "No encontrado"))
        return detail
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
