"""Router — Modelo comercial basado en valor (1280)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_commercial import (
    CostCreate,
    FinalPriceRequest,
    ImportValuationRequest,
    PlanCreate,
    PriceSuggestRequest,
    ProposalCreate,
    ProposalSimulateRequest,
    ScenarioCreate,
    SimulateRequest,
    ValueComponentCreate,
)
from app.services import commercial_service as svc

router = APIRouter(prefix="/api/comercial", tags=["comercial"])


def _handle_validation(exc: svc.CommercialValidationError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/planes")
def list_plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    return [svc.plan_to_dict(p) for p in svc.list_plans(db, user.organization_id)]


@router.post("/planes", status_code=status.HTTP_201_CREATED)
def create_plan(body: PlanCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.manage_plans", db)
    org_id = body.organization_id or user.organization_id
    try:
        row = svc.create_plan(db, org_id, body.model_dump(), user.id)
        db.commit()
        return svc.plan_to_dict(row)
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.get("/planes/{plan_id}")
def get_plan_detail(plan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    return svc.plan_to_dict(svc.get_plan(db, user.organization_id, plan_id))


@router.get("/propuestas")
def list_proposals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    return svc.list_proposals(db, user.organization_id)


@router.post("/propuestas", status_code=status.HTTP_201_CREATED)
def create_proposal(body: ProposalCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.create", db)
    try:
        row = svc.create_proposal(db, user.organization_id, body.model_dump(exclude_none=True), user.id)
        db.commit()
        return svc.proposal_to_detail(db, user.organization_id, row.id)
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.get("/propuestas/{proposal_id}")
def get_proposal(proposal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    return svc.proposal_to_detail(db, user.organization_id, proposal_id)


@router.post("/propuestas/{proposal_id}/valores", status_code=status.HTTP_201_CREATED)
def add_value(proposal_id: str, body: ValueComponentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.create", db)
    try:
        row = svc.add_value_component(db, user.organization_id, proposal_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "valor_atribuible": float(row.valor_atribuible)}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/propuestas/{proposal_id}/escenarios", status_code=status.HTTP_201_CREATED)
def add_scenario(proposal_id: str, body: ScenarioCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.create", db)
    try:
        row = svc.add_scenario(db, user.organization_id, proposal_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "scenario_type": row.scenario_type}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/propuestas/{proposal_id}/costos", status_code=status.HTTP_201_CREATED)
def add_cost(proposal_id: str, body: CostCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.create", db)
    try:
        row = svc.add_cost(db, user.organization_id, proposal_id, body.model_dump(), user.id)
        db.commit()
        return {"id": row.id, "monto": float(row.monto)}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/propuestas/{proposal_id}/detectar-doble-conteo")
def detect_double_count(proposal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    alerts = svc.detect_double_count(db, user.organization_id, proposal_id)
    db.commit()
    return {"alertas": [{"id": a.id, "tipo": a.tipo, "mensaje": a.mensaje, "severidad": a.severidad} for a in alerts]}


@router.post("/propuestas/{proposal_id}/precio-sugerido")
def suggest_price(proposal_id: str, body: PriceSuggestRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.simulate", db)
    result = svc.suggest_price(db, user.organization_id, proposal_id, scenario_type=body.scenario_type)
    db.commit()
    return result


@router.post("/propuestas/{proposal_id}/precio-final")
def set_final_price(proposal_id: str, body: FinalPriceRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.approve", db)
    try:
        row = svc.set_final_price(db, user.organization_id, proposal_id, body.precio_final, body.justificacion, user.id)
        db.commit()
        return {"id": row.id, "precio_final": float(row.precio_final) if row.precio_final else None}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/propuestas/{proposal_id}/aprobar")
def approve_proposal(proposal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.approve", db)
    try:
        row = svc.approve_proposal(db, user.organization_id, proposal_id, user.id)
        db.commit()
        return {"id": row.id, "estado": row.estado}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.post("/propuestas/{proposal_id}/importar-valoracion", status_code=status.HTTP_201_CREATED)
def import_valuation(proposal_id: str, body: ImportValuationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.create", db)
    try:
        row = svc.import_from_valuation(db, user.organization_id, proposal_id, body.opportunity_id, user.id)
        db.commit()
        return {"id": row.id, "valor_atribuible": float(row.valor_atribuible)}
    except svc.CommercialValidationError as exc:
        db.rollback()
        raise _handle_validation(exc) from exc


@router.get("/propuestas/{proposal_id}/trazabilidad")
def get_traceability(proposal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.view", db)
    return svc.build_traceability(db, user.organization_id, proposal_id)


@router.post("/propuestas/{proposal_id}/simular")
def simulate_proposal(proposal_id: str, body: ProposalSimulateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.simulate", db)
    return svc.simulate_proposal(db, user.organization_id, proposal_id, body.model_dump(exclude_none=True))


@router.post("/simular")
def simulate(body: SimulateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_permission(user, "comercial.simulate", db)
    return svc.simulate_value(db, user.organization_id, body.model_dump())
