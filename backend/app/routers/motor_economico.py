"""API — Motor Económico EIAAX (facade FinOps, sin segundo FinOps)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_economic_motor import (
    CostEntryOut,
    CostRegisterIn,
    EntityViewOut,
    PriceRecommendIn,
    PrivateEconomyIn,
    ValueEntryOut,
    ValueRegisterIn,
)
from app.services import economic_motor_service as svc

router = APIRouter(prefix="/api/motor-economico", tags=["Motor Económico"])


def _org(db: Session, user: User, organization_id: str | None) -> str:
    try:
        return svc.resolve_organization_id(db, user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/vista-entidad", response_model=EntityViewOut)
def vista_entidad(
    organization_id: str | None = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    org_id = _org(db, user, organization_id)
    return svc.entity_view_summary(db, org_id, period_days=period_days)


@router.get("/indicadores")
def indicadores(
    organization_id: str | None = Query(None),
    period_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.view", db)
    org_id = _org(db, user, organization_id)
    return svc.build_indicators(db, org_id, period_days=period_days)


@router.post("/costos", response_model=CostEntryOut)
def registrar_costo(
    body: CostRegisterIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        row = svc.register_cost(db, user, organization_id=org_id, **body.model_dump())
        db.commit()
        db.refresh(row)
    except (ValueError, Exception) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CostEntryOut(
        id=row.id,
        organization_id=row.organization_id,
        amount=float(row.amount),
        currency=row.currency,
        cost_class=row.cost_class,
        amount_kind=row.amount_kind,
        cost_source=row.cost_source,
        scope_type=row.scope_type,
        finops_record_id=row.finops_record_id,
    )


@router.post("/valores", response_model=ValueEntryOut)
def registrar_valor(
    body: ValueRegisterIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.manage", db)
    org_id = _org(db, user, organization_id)
    try:
        row = svc.register_value(db, user, organization_id=org_id, **body.model_dump())
        db.commit()
        db.refresh(row)
    except (ValueError, Exception) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ValueEntryOut(
        id=row.id,
        organization_id=row.organization_id,
        amount=float(row.amount),
        currency=row.currency,
        value_type=row.value_type,
        value_nature=row.value_nature,
        scope_type=row.scope_type,
        finops_value_id=row.finops_value_id,
    )


@router.get("/economia-privada")
def obtener_economia_privada(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.economy.private", db)
    org_id = _org(db, user, organization_id)
    row = svc.get_private_economy(db, org_id)
    return svc.private_economy_to_dict(row) or {"organization_id": org_id, "empty": True}


@router.put("/economia-privada")
def guardar_economia_privada(
    body: PrivateEconomyIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.economy.private", db)
    org_id = _org(db, user, organization_id)
    row = svc.save_private_economy(db, user, org_id, body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(row)
    return svc.private_economy_to_dict(row)


@router.post("/precio-recomendado")
def precio_recomendado(
    body: PriceRecommendIn,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.economy.recommend", db)
    org_id = _org(db, user, organization_id)
    result = svc.recommend_price(db, user, org_id, **body.model_dump())
    db.commit()
    return result


@router.post("/sincronizar-finops")
def sincronizar_finops(
    organization_id: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "finops.manage", db)
    org_id = _org(db, user, organization_id)
    created = svc.backfill_costs_from_finops(db, org_id, limit=limit)
    db.commit()
    return {"organization_id": org_id, "entries_created": created}
