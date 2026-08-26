from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.schemas_automation import AutomationCreate, AutomationOut, AutomationRunOut, AutomationUpdate
from app.services import automation_service as svc

router = APIRouter(prefix="/api/automations", tags=["automations"])


@router.get("", response_model=list[AutomationOut])
def list_automations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.view", db)
    return [svc._serialize_automation(r) for r in svc.list_automations(db, user.organization_id)]


@router.post("", response_model=AutomationOut, status_code=status.HTTP_201_CREATED)
def create_automation(body: AutomationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.create", db)
    row = svc.create_automation(db, org_id=user.organization_id, user_id=user.id, data=body)
    return svc._serialize_automation(row)


@router.get("/{automation_id}", response_model=AutomationOut)
def get_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.view", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    return svc._serialize_automation(row)


@router.put("/{automation_id}", response_model=AutomationOut)
def update_automation(
    automation_id: str,
    body: AutomationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "automation.edit", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    updated = svc.update_automation(db, automation=row, user_id=user.id, data=body)
    return svc._serialize_automation(updated)


@router.post("/{automation_id}/activate", response_model=AutomationOut)
def activate_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.activate", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    return svc._serialize_automation(svc.activate_automation(db, row, user.id))


@router.post("/{automation_id}/pause", response_model=AutomationOut)
def pause_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.pause", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    return svc._serialize_automation(svc.pause_automation(db, row, user.id))


@router.post("/{automation_id}/disable", response_model=AutomationOut)
def disable_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.edit", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    return svc._serialize_automation(svc.disable_automation(db, row, user.id))


@router.post("/{automation_id}/duplicate", response_model=AutomationOut, status_code=status.HTTP_201_CREATED)
def duplicate_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.create", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    return svc._serialize_automation(svc.duplicate_automation(db, row, user.id))


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.delete", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    svc.delete_automation(db, row, user.id)
    return None


@router.post("/{automation_id}/run-now", response_model=AutomationRunOut)
def run_now(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.run", db)
    row = svc.get_automation(db, automation_id, user.organization_id)
    run = svc.run_now(db, row, user.id)
    return svc._serialize_run(run)


@router.get("/{automation_id}/runs", response_model=list[AutomationRunOut])
def list_runs(automation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.view_runs", db)
    svc.get_automation(db, automation_id, user.organization_id)
    return [svc._serialize_run(r) for r in svc.list_runs(db, automation_id, user.organization_id)]


runs_router = APIRouter(prefix="/api/automation-runs", tags=["automations"])


@runs_router.get("/{run_id}", response_model=AutomationRunOut)
def get_run(run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "automation.view_runs", db)
    return svc._serialize_run(svc.get_run(db, run_id, user.organization_id))
