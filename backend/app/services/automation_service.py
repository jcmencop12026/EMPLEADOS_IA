"""Servicio de automatizaciones — CRUD, ejecución vía orquestador (CURSOR-810)."""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.automation_models import Automation, AutomationRun
from app.enums import AutomationRunStatus, AutomationStatus, AutomationTriggerType, WorkPlanStatus
from app.orchestration_models import FinOpsRecord, WorkPlan
from app.schemas_automation import AutomationCreate, AutomationUpdate
from app.services.coordinator import execute_plan, route_task
from app.services.recurrence import compute_next_run, occurrence_key, parse_recurrence


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dump_recurrence(data: dict[str, Any] | None) -> str | None:
    return json.dumps(data, ensure_ascii=False) if data else None


def _load_recurrence(raw: str | None) -> dict[str, Any] | None:
    return parse_recurrence(raw) if raw else None


def _serialize_automation(row: Automation) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "name": row.name,
        "description": row.description,
        "status": row.status,
        "trigger_type": row.trigger_type,
        "schedule_type": row.schedule_type,
        "timezone": row.timezone,
        "start_at": row.start_at,
        "end_at": row.end_at,
        "next_run_at": row.next_run_at,
        "last_run_at": row.last_run_at,
        "recurrence": _load_recurrence(row.recurrence_config_json),
        "objective": row.objective,
        "employee_id": row.employee_id,
        "workflow": json.loads(row.workflow_config_json) if row.workflow_config_json else None,
        "priority": row.priority,
        "max_retries": row.max_retries,
        "retry_delay_seconds": row.retry_delay_seconds,
        "timeout_seconds": row.timeout_seconds,
        "requires_approval": row.requires_approval,
        "max_cost_per_run": row.max_cost_per_run,
        "max_runs_per_day": row.max_runs_per_day,
        "missed_run_policy": row.missed_run_policy,
        "created_by_id": row.created_by_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _serialize_run(row: AutomationRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "automation_id": row.automation_id,
        "organization_id": row.organization_id,
        "occurrence_key": row.occurrence_key,
        "scheduled_for": row.scheduled_for,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "status": row.status,
        "work_plan_id": row.work_plan_id,
        "result_reference": json.loads(row.result_reference_json) if row.result_reference_json else None,
        "attempt": row.attempt,
        "error": row.error,
        "cost_reference": row.cost_reference,
        "trigger_source": row.trigger_source,
        "created_at": row.created_at,
    }


def refresh_next_run(db: Session, automation: Automation) -> None:
    if automation.status != AutomationStatus.ACTIVE:
        automation.next_run_at = None
        return
    if automation.trigger_type != AutomationTriggerType.SCHEDULE:
        automation.next_run_at = None
        return
    now = _utcnow()
    next_run = _as_utc(automation.next_run_at)
    if (
        next_run
        and next_run < now
        and automation.missed_run_policy == "SKIP"
    ):
        automation.next_run_at = compute_next_run(
            schedule_type=automation.schedule_type,
            tz_name=automation.timezone,
            start_at=automation.start_at,
            end_at=automation.end_at,
            recurrence_config=_load_recurrence(automation.recurrence_config_json),
            last_run_at=automation.last_run_at,
            after=now,
        )
        automation.next_run_at = _as_utc(automation.next_run_at)
        return
    automation.next_run_at = compute_next_run(
        schedule_type=automation.schedule_type,
        tz_name=automation.timezone,
        start_at=automation.start_at,
        end_at=automation.end_at,
        recurrence_config=_load_recurrence(automation.recurrence_config_json),
        last_run_at=automation.last_run_at,
        after=now,
    )
    automation.next_run_at = _as_utc(automation.next_run_at)


def create_automation(db: Session, *, org_id: str, user_id: str, data: AutomationCreate) -> Automation:
    row = Automation(
        organization_id=org_id,
        name=data.name,
        description=data.description,
        status=AutomationStatus.DRAFT,
        trigger_type=data.trigger_type,
        schedule_type=data.schedule_type,
        timezone=data.timezone,
        start_at=data.start_at,
        end_at=data.end_at,
        recurrence_config_json=_dump_recurrence(data.recurrence.model_dump() if data.recurrence else None),
        objective=data.objective,
        employee_id=data.employee_id,
        workflow_config_json=json.dumps(data.workflow or {}, ensure_ascii=False),
        priority=data.priority,
        max_retries=data.max_retries,
        retry_delay_seconds=data.retry_delay_seconds,
        timeout_seconds=data.timeout_seconds,
        requires_approval=data.requires_approval,
        max_cost_per_run=data.max_cost_per_run,
        max_runs_per_day=data.max_runs_per_day,
        missed_run_policy=data.missed_run_policy,
        created_by_id=user_id,
    )
    db.add(row)
    db.flush()
    refresh_next_run(db, row)
    db.commit()
    db.refresh(row)
    write_audit(db, action="automation.created", organization_id=org_id, user_id=user_id, detail=row.name)
    return row


def update_automation(db: Session, *, automation: Automation, user_id: str, data: AutomationUpdate) -> Automation:
    payload = data.model_dump(exclude_unset=True)
    if "recurrence" in payload:
        rec = payload.pop("recurrence")
        automation.recurrence_config_json = _dump_recurrence(rec)
    if "workflow" in payload:
        wf = payload.pop("workflow")
        automation.workflow_config_json = json.dumps(wf or {}, ensure_ascii=False)
    for key, val in payload.items():
        setattr(automation, key, val)
    automation.updated_at = _utcnow()
    refresh_next_run(db, automation)
    db.commit()
    db.refresh(automation)
    write_audit(db, action="automation.updated", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
    return automation


def get_automation(db: Session, automation_id: str, org_id: str) -> Automation:
    row = db.query(Automation).filter(Automation.id == automation_id, Automation.organization_id == org_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automatización no encontrada")
    return row


def list_automations(db: Session, org_id: str) -> list[Automation]:
    return (
        db.query(Automation)
        .filter(Automation.organization_id == org_id)
        .order_by(Automation.updated_at.desc())
        .all()
    )


def activate_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    automation.status = AutomationStatus.ACTIVE
    refresh_next_run(db, automation)
    db.commit()
    db.refresh(automation)
    write_audit(db, action="automation.activated", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
    return automation


def pause_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    automation.status = AutomationStatus.PAUSED
    automation.next_run_at = None
    db.commit()
    db.refresh(automation)
    write_audit(db, action="automation.paused", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
    return automation


def disable_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    automation.status = AutomationStatus.DISABLED
    automation.next_run_at = None
    db.commit()
    db.refresh(automation)
    write_audit(db, action="automation.disabled", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
    return automation


def delete_automation(db: Session, automation: Automation, user_id: str) -> None:
    org_id = automation.organization_id
    name = automation.name
    db.delete(automation)
    db.commit()
    write_audit(db, action="automation.deleted", organization_id=org_id, user_id=user_id, detail=name)


def duplicate_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    clone = Automation(
        organization_id=automation.organization_id,
        name=f"{automation.name} (copia)",
        description=automation.description,
        status=AutomationStatus.DRAFT,
        trigger_type=automation.trigger_type,
        schedule_type=automation.schedule_type,
        timezone=automation.timezone,
        start_at=automation.start_at,
        end_at=automation.end_at,
        recurrence_config_json=automation.recurrence_config_json,
        objective=automation.objective,
        employee_id=automation.employee_id,
        workflow_config_json=automation.workflow_config_json,
        priority=automation.priority,
        max_retries=automation.max_retries,
        retry_delay_seconds=automation.retry_delay_seconds,
        timeout_seconds=automation.timeout_seconds,
        requires_approval=automation.requires_approval,
        max_cost_per_run=automation.max_cost_per_run,
        max_runs_per_day=automation.max_runs_per_day,
        missed_run_policy=automation.missed_run_policy,
        created_by_id=user_id,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    write_audit(db, action="automation.duplicated", organization_id=clone.organization_id, user_id=user_id, detail=clone.name)
    return clone


def _runs_today_count(db: Session, automation_id: str) -> int:
    start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(func.count(AutomationRun.id))
        .filter(
            AutomationRun.automation_id == automation_id,
            AutomationRun.created_at >= start,
            AutomationRun.status.notin_([AutomationRunStatus.SKIPPED, AutomationRunStatus.CANCELLED]),
        )
        .scalar()
        or 0
    )


def _sum_run_cost(db: Session, work_plan_id: str | None) -> float | None:
    if not work_plan_id:
        return None
    total = (
        db.query(func.sum(FinOpsRecord.cost))
        .filter(FinOpsRecord.work_plan_id == work_plan_id)
        .scalar()
    )
    return float(total) if total is not None else None


def trigger_run(
    db: Session,
    *,
    automation: Automation,
    user_id: str,
    trigger_source: str,
    scheduled_for: datetime | None = None,
) -> AutomationRun:
    when = scheduled_for or _utcnow()
    key = occurrence_key(when)

    if automation.max_runs_per_day is not None and _runs_today_count(db, automation.id) >= automation.max_runs_per_day:
        skip_key = f"{key}-limit-{uuid.uuid4().hex[:8]}"
        run = AutomationRun(
            automation_id=automation.id,
            organization_id=automation.organization_id,
            occurrence_key=skip_key,
            scheduled_for=when,
            status=AutomationRunStatus.SKIPPED,
            error="max_runs_per_day excedido",
            trigger_source=trigger_source,
            finished_at=_utcnow(),
        )
        db.add(run)
        db.commit()
        write_audit(db, action="automation.run_skipped", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
        return run

    run = AutomationRun(
        automation_id=automation.id,
        organization_id=automation.organization_id,
        occurrence_key=key,
        scheduled_for=when,
        status=AutomationRunStatus.QUEUED,
        trigger_source=trigger_source,
    )
    db.add(run)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(AutomationRun)
            .filter(AutomationRun.automation_id == automation.id, AutomationRun.occurrence_key == key)
            .first()
        )
        if existing:
            return existing
        raise

    return _execute_run(db, automation=automation, run=run, user_id=user_id)


def _apply_run_result(
    db: Session,
    *,
    automation: Automation,
    run: AutomationRun,
    result: dict[str, Any],
) -> None:
    plan_id = result.get("plan_id")
    run.work_plan_id = plan_id
    run.result_reference_json = json.dumps(result, ensure_ascii=False, default=str)

    plan_status = result.get("status")
    if plan_status == WorkPlanStatus.WAITING_APPROVAL:
        run.status = AutomationRunStatus.WAITING_APPROVAL
        run.finished_at = None
    elif plan_status in (WorkPlanStatus.COMPLETED, WorkPlanStatus.READY):
        run.status = AutomationRunStatus.SUCCEEDED
    elif plan_status == WorkPlanStatus.FAILED:
        run.status = AutomationRunStatus.FAILED
        run.error = result.get("error") or result.get("message")
    else:
        run.status = AutomationRunStatus.SUCCEEDED if not result.get("error") else AutomationRunStatus.FAILED
        if result.get("error"):
            run.error = str(result.get("error"))

    run.cost_reference = _sum_run_cost(db, plan_id)
    if automation.max_cost_per_run is not None and run.cost_reference is not None:
        if run.cost_reference > automation.max_cost_per_run:
            run.status = AutomationRunStatus.SKIPPED
            run.error = "max_cost_per_run excedido"


def _execute_run(db: Session, *, automation: Automation, run: AutomationRun, user_id: str) -> AutomationRun:
    run.status = AutomationRunStatus.RUNNING
    run.started_at = run.started_at or _utcnow()
    db.commit()

    workflow = json.loads(automation.workflow_config_json) if automation.workflow_config_json else {}
    context = dict(workflow)
    if automation.employee_id:
        context["employee_id"] = automation.employee_id
    context["automation_id"] = automation.id
    context["automation_run_id"] = run.id

    max_attempts = automation.max_retries + 1
    while run.attempt <= max_attempts:
        try:
            if run.work_plan_id and automation.requires_approval:
                result = execute_plan(db, plan_id=run.work_plan_id, user_id=user_id)
            else:
                result = route_task(
                    db,
                    organization_id=automation.organization_id,
                    user_id=user_id,
                    request=automation.objective,
                    context=context,
                    auto_execute=not automation.requires_approval,
                )
            _apply_run_result(db, automation=automation, run=run, result=result)
        except Exception as exc:
            run.status = AutomationRunStatus.FAILED
            run.error = str(exc)

        if run.status == AutomationRunStatus.WAITING_APPROVAL:
            break
        if run.status != AutomationRunStatus.FAILED or run.attempt >= max_attempts:
            break

        run.attempt += 1
        write_audit(
            db,
            action="automation.run_retry",
            organization_id=automation.organization_id,
            user_id=user_id,
            detail=f"{automation.name}:attempt={run.attempt}",
        )
        if automation.retry_delay_seconds > 0:
            time.sleep(min(automation.retry_delay_seconds, 1))
        db.commit()

    if run.status != AutomationRunStatus.WAITING_APPROVAL:
        run.finished_at = _utcnow()
    automation.last_run_at = run.finished_at or _utcnow()
    refresh_next_run(db, automation)
    db.commit()
    db.refresh(run)

    if run.status == AutomationRunStatus.SUCCEEDED:
        audit_action = "automation.run_completed"
    elif run.status == AutomationRunStatus.WAITING_APPROVAL:
        audit_action = "automation.run_waiting_approval"
    elif run.status == AutomationRunStatus.SKIPPED:
        audit_action = "automation.run_skipped"
    else:
        audit_action = "automation.run_failed"
    write_audit(
        db,
        action=audit_action,
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=f"{automation.name}:{run.status}",
    )
    return run


def sync_run_from_work_plan(db: Session, *, work_plan_id: str, plan_status: str, error: str | None = None) -> AutomationRun | None:
    run = db.query(AutomationRun).filter(AutomationRun.work_plan_id == work_plan_id).first()
    if not run:
        return None
    automation = db.query(Automation).filter(Automation.id == run.automation_id).first()
    if plan_status == WorkPlanStatus.COMPLETED:
        run.status = AutomationRunStatus.SUCCEEDED
        run.finished_at = _utcnow()
        run.error = None
    elif plan_status == WorkPlanStatus.FAILED:
        run.status = AutomationRunStatus.FAILED
        run.finished_at = _utcnow()
        run.error = error or run.error
    elif plan_status == WorkPlanStatus.WAITING_APPROVAL:
        run.status = AutomationRunStatus.WAITING_APPROVAL
        return run
    else:
        return run

    run.cost_reference = _sum_run_cost(db, work_plan_id)
    if automation and automation.max_cost_per_run is not None and run.cost_reference is not None:
        if run.cost_reference > automation.max_cost_per_run:
            run.status = AutomationRunStatus.SKIPPED
            run.error = "max_cost_per_run excedido"

    if automation:
        automation.last_run_at = run.finished_at
        refresh_next_run(db, automation)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        action="automation.run_completed" if run.status == AutomationRunStatus.SUCCEEDED else "automation.run_failed",
        organization_id=run.organization_id,
        user_id=None,
        detail=f"plan:{work_plan_id}:{run.status}",
    )
    return run


def trigger_internal_event(
    db: Session,
    *,
    org_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> list[AutomationRun]:
    rows = (
        db.query(Automation)
        .filter(
            Automation.organization_id == org_id,
            Automation.status == AutomationStatus.ACTIVE,
            Automation.trigger_type == AutomationTriggerType.INTERNAL_EVENT,
        )
        .all()
    )
    runs: list[AutomationRun] = []
    for automation in rows:
        cfg = _load_recurrence(automation.recurrence_config_json) or {}
        if cfg.get("event_type") and cfg.get("event_type") != event_type:
            continue
        actor = user_id or automation.created_by_id
        run = trigger_run(
            db,
            automation=automation,
            user_id=actor,
            trigger_source=AutomationTriggerType.INTERNAL_EVENT,
        )
        runs.append(run)
    return runs


def run_now(db: Session, automation: Automation, user_id: str) -> AutomationRun:
    write_audit(db, action="automation.run_manual", organization_id=automation.organization_id, user_id=user_id, detail=automation.name)
    return trigger_run(db, automation=automation, user_id=user_id, trigger_source=AutomationTriggerType.MANUAL)


def get_run(db: Session, run_id: str, org_id: str) -> AutomationRun:
    row = db.query(AutomationRun).filter(AutomationRun.id == run_id, AutomationRun.organization_id == org_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejecución no encontrada")
    return row


def list_runs(db: Session, automation_id: str, org_id: str) -> list[AutomationRun]:
    return (
        db.query(AutomationRun)
        .filter(AutomationRun.automation_id == automation_id, AutomationRun.organization_id == org_id)
        .order_by(AutomationRun.scheduled_for.desc())
        .limit(200)
        .all()
    )


def recalculate_all_active(db: Session) -> int:
    rows = db.query(Automation).filter(Automation.status == AutomationStatus.ACTIVE).all()
    for row in rows:
        refresh_next_run(db, row)
    db.commit()
    return len(rows)
