"""API — Valoración económica y ROI por oportunidad (1210)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_valuation import (
    ExecutionCostIn,
    ExpectedValueIn,
    RealValueIn,
    ScenarioIn,
    ValuationCreateIn,
    ValuationOut,
    ValuationSummaryOut,
)
from app.services import valuation_service as svc
from app.valuation_enums import ScenarioType

router = APIRouter(prefix="/api/valoracion", tags=["Valoración económica"])


@router.get("/opportunities/{opportunity_id}", response_model=ValuationSummaryOut)
def get_valuation_summary(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.view", db)
    try:
        return svc.compute_economic_summary(db, user.organization_id, opportunity_id)
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/opportunities/{opportunity_id}/roi", response_model=ValuationSummaryOut)
def get_roi_summary(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.roi", db)
    try:
        return svc.compute_economic_summary(db, user.organization_id, opportunity_id)
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/opportunities/{opportunity_id}", response_model=ValuationOut)
def create_valuation(
    opportunity_id: str,
    body: ValuationCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.manage", db)
    try:
        row = svc.create_valuation(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            user_id=user.id,
            value_type=body.value_type,
            scope=body.scope,
            currency=body.currency,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ValuationOut(
        id=row.id,
        opportunity_id=row.opportunity_id,
        value_type=row.value_type,
        scope=row.scope,
        currency=row.currency,
        status=row.status,
        version=row.version,
        validated_at=row.validated_at,
        created_at=row.created_at,
    )


@router.put("/opportunities/{opportunity_id}/expected")
def update_expected(
    opportunity_id: str,
    body: ExpectedValueIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.manage", db)
    try:
        row = svc.update_expected(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            user_id=user.id,
            gross_value=body.gross_value,
            probability=body.probability,
            execution_cost_expected=body.execution_cost_expected,
            period_days=body.period_days,
            value_nature=body.value_nature,
            assumptions=body.assumptions,
            source=body.source,
            evidence=body.evidence,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return svc._serialize_expected(row)


@router.put("/opportunities/{opportunity_id}/scenarios/{scenario_type}")
def update_scenario(
    opportunity_id: str,
    scenario_type: str,
    body: ScenarioIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.manage", db)
    if scenario_type not in ScenarioType.ALL:
        raise HTTPException(status_code=400, detail="Tipo de escenario no válido.")
    try:
        row = svc.update_scenario(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            scenario_type=scenario_type,
            user_id=user.id,
            value_amount=body.value_amount,
            probability=body.probability,
            cost=body.cost,
            period_days=body.period_days,
            assumptions=body.assumptions,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return svc._serialize_scenario(row)


@router.post("/opportunities/{opportunity_id}/real")
def register_real_value(
    opportunity_id: str,
    body: RealValueIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.manage", db)
    try:
        row = svc.register_real_value(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            user_id=user.id,
            materialized_value=body.materialized_value,
            attributable_value=body.attributable_value,
            value_nature=body.value_nature,
            attribution_level=body.attribution_level,
            attribution_pct=body.attribution_pct,
            source=body.source,
            evidence=body.evidence,
            responsible_id=body.responsible_id,
            justification=body.justification,
            external_measurement_ref=body.external_measurement_ref,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return svc._serialize_real(row)


@router.post("/opportunities/{opportunity_id}/costs")
def register_execution_cost(
    opportunity_id: str,
    body: ExecutionCostIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.manage", db)
    try:
        row = svc.register_execution_cost(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            user_id=user.id,
            cost_type=body.cost_type,
            amount=body.amount,
            currency=body.currency,
            finops_record_id=body.finops_record_id,
            description=body.description,
            source=body.source,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return svc._serialize_cost(row)


@router.post("/opportunities/{opportunity_id}/validate", response_model=ValuationOut)
def validate_valuation(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "valoracion.validate", db)
    try:
        row = svc.validate_valuation(
            db,
            organization_id=user.organization_id,
            opportunity_id=opportunity_id,
            user_id=user.id,
        )
    except svc.ValuationValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ValuationOut(
        id=row.id,
        opportunity_id=row.opportunity_id,
        value_type=row.value_type,
        scope=row.scope,
        currency=row.currency,
        status=row.status,
        version=row.version,
        validated_at=row.validated_at,
        created_at=row.created_at,
    )
