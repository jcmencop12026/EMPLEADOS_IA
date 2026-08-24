"""Servicio de automatizaciones — CRUD, ejecución vía orquestador (CURSOR-810)."""
from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.automation_models import Automation, AutomationRun
from app.enums import (
    ApprovalStatus,
    AutomationRunStatus,
    AutomationStatus,
    AutomationTriggerType,
    WorkPlanStatus,
)
from app.orchestration_models import AIEmployee, ApprovalRequest, FinOpsRecord, WorkPlan
from app.schemas_automation import AutomationCreate, AutomationUpdate
from app.services.coordinator import execute_plan, route_task
from app.services.execution_guard import (
    ExecutionCancelledError,
    FenceToken,
    bind_fence_token,
    current_fence_token,
    get_fence_controller,
    invalidate_run_execution,
    register_fence,
    release_fence,
    require_execution_allowed,
    reset_fence_token,
)
from app.services.recurrence import compute_next_run, internal_event_occurrence_key, occurrence_key, parse_recurrence

MAX_RETRIES_LIMIT = 10
MAX_RETRY_DELAY_SECONDS = 300


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Fusiona patch sobre base preservando claves no enviadas en estructuras anidadas."""
    result = dict(base)
    for key, val in patch.items():
        if val is None:
            result[key] = None
        elif isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _dump_recurrence(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None
    if hasattr(data, "model_dump"):
        data = data.model_dump(exclude_none=True)
    return json.dumps(data, ensure_ascii=False)


def _load_recurrence(raw: str | None) -> dict[str, Any] | None:
    return parse_recurrence(raw) if raw else None


def _validate_employee_id(db: Session, *, org_id: str, employee_id: str | None) -> None:
    if not employee_id:
        return
    employee = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El empleado no pertenece a la organización o no existe",
        )


def _assert_employee_tenant(db: Session, automation: Automation) -> None:
    if not automation.employee_id:
        return
    employee = (
        db.query(AIEmployee)
        .filter(
            AIEmployee.id == automation.employee_id,
            AIEmployee.organization_id == automation.organization_id,
        )
        .first()
    )
    if not employee:
        raise ValueError("Empleado cross-tenant o inexistente — ejecución rechazada")


def _validate_retries(max_retries: int) -> None:
    if max_retries < 0 or max_retries > MAX_RETRIES_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"max_retries debe estar entre 0 y {MAX_RETRIES_LIMIT} (reintentos tras el intento inicial)",
        )


def _precheck_cost_limit(automation: Automation, workflow: dict[str, Any]) -> str | None:
    """Valida costo previo solo cuando existe estimación fiable en workflow."""
    if automation.max_cost_per_run is None:
        return None
    estimated = workflow.get("estimated_cost")
    if estimated is None:
        return None
    try:
        estimated_value = float(estimated)
    except (TypeError, ValueError):
        return None
    if estimated_value > automation.max_cost_per_run:
        return (
            f"Costo estimado ({estimated_value}) excede max_cost_per_run ({automation.max_cost_per_run})"
        )
    return None


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
    _validate_employee_id(db, org_id=org_id, employee_id=data.employee_id)
    _validate_retries(data.max_retries)
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
    if "employee_id" in payload:
        _validate_employee_id(db, org_id=automation.organization_id, employee_id=payload["employee_id"])
    if "max_retries" in payload and payload["max_retries"] is not None:
        _validate_retries(payload["max_retries"])
    if "recurrence" in payload:
        rec = payload.pop("recurrence")
        if rec is None:
            automation.recurrence_config_json = None
        else:
            existing = _load_recurrence(automation.recurrence_config_json) or {}
            rec_data = rec.model_dump(exclude_unset=True) if hasattr(rec, "model_dump") else dict(rec)
            automation.recurrence_config_json = _dump_recurrence(_deep_merge(existing, rec_data))
    if "workflow" in payload:
        wf = payload.pop("workflow")
        if wf is None:
            automation.workflow_config_json = None
        else:
            existing = json.loads(automation.workflow_config_json) if automation.workflow_config_json else {}
            automation.workflow_config_json = json.dumps(_deep_merge(existing, wf or {}), ensure_ascii=False)
    for key, val in payload.items():
        setattr(automation, key, val)
    automation.updated_at = _utcnow()
    refresh_next_run(db, automation)
    db.commit()
    db.refresh(automation)
    write_audit(
        db,
        action="automation.updated",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=automation.name,
    )
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
    write_audit(
        db,
        action="automation.activated",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=automation.name,
    )
    return automation


def pause_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    automation.status = AutomationStatus.PAUSED
    automation.next_run_at = None
    db.commit()
    db.refresh(automation)
    write_audit(
        db,
        action="automation.paused",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=automation.name,
    )
    return automation


def disable_automation(db: Session, automation: Automation, user_id: str) -> Automation:
    automation.status = AutomationStatus.DISABLED
    automation.next_run_at = None
    db.commit()
    db.refresh(automation)
    write_audit(
        db,
        action="automation.disabled",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=automation.name,
    )
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
    write_audit(
        db,
        action="automation.duplicated",
        organization_id=clone.organization_id,
        user_id=user_id,
        detail=clone.name,
    )
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


def _run_with_timeout(
    fn: Callable[[], dict[str, Any]],
    timeout_seconds: int | None,
) -> dict[str, Any]:
    if not timeout_seconds or timeout_seconds <= 0:
        return fn()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeout as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise TimeoutError(f"timeout_seconds excedido ({timeout_seconds}s)") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _create_pre_execution_approval(
    db: Session,
    *,
    automation: Automation,
    plan: WorkPlan,
    user_id: str,
    run: AutomationRun,
) -> None:
    approval = ApprovalRequest(
        organization_id=automation.organization_id,
        work_plan_id=plan.id,
        action=f"Aprobar automatización: {automation.name}",
        reason=automation.objective[:500],
        requested_by=user_id,
    )
    db.add(approval)
    plan.status = WorkPlanStatus.WAITING_APPROVAL
    plan.approval_status = ApprovalStatus.PENDING
    from app.services.execution_guard import commit_gated

    commit_gated(db)
    write_audit(
        db,
        action="automation.waiting_approval",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=f"{automation.name}:{plan.id}",
    )
    return approval.id


def _invoke_orchestration_isolated(
    *,
    automation_id: str,
    run_id: str,
    user_id: str,
    token: FenceToken,
    db_bind=None,
) -> dict[str, Any]:
    """Ejecuta orquestación en sesión aislada con fencing (thread-safe)."""
    from sqlalchemy.orm import sessionmaker as session_factory

    if db_bind is None:
        from app.database import SessionLocal

        worker_db = SessionLocal()
    else:
        worker_db = session_factory(autocommit=False, autoflush=False, bind=db_bind)()
    fence_ctx = bind_fence_token(token)
    try:
        automation = worker_db.query(Automation).filter(Automation.id == automation_id).first()
        run = worker_db.query(AutomationRun).filter(AutomationRun.id == run_id).first()
        if not automation or not run:
            raise RuntimeError("Automatización o ejecución no encontrada")
        run_generation = run.execution_generation
        worker_db.expunge(run)
        return _invoke_orchestration(
            worker_db,
            automation=automation,
            run_id=run_id,
            run_generation=run_generation,
            user_id=user_id,
        )
    finally:
        reset_fence_token(fence_ctx)
        worker_db.close()


def _invoke_orchestration(
    db: Session,
    *,
    automation: Automation,
    run_id: str,
    run_generation: int,
    user_id: str,
) -> dict[str, Any]:
    require_execution_allowed()

    workflow = json.loads(automation.workflow_config_json) if automation.workflow_config_json else {}
    context = dict(workflow)
    if automation.employee_id:
        context["employee_id"] = automation.employee_id
    context["automation_id"] = automation.id
    context["automation_run_id"] = run_id
    context["execution_generation"] = run_generation

    if automation.requires_approval:
        run = db.query(AutomationRun).filter(AutomationRun.id == run_id).first()
        if run and run.work_plan_id:
            plan = db.query(WorkPlan).filter(WorkPlan.id == run.work_plan_id).first()
            if plan and plan.status == WorkPlanStatus.WAITING_APPROVAL:
                return {"plan_id": plan.id, "status": plan.status}
            if plan and plan.approval_status == ApprovalStatus.APPROVED:
                require_execution_allowed()
                result = execute_plan(db, plan_id=plan.id, user_id=user_id)
                require_execution_allowed()
                return result
        require_execution_allowed()
        result = route_task(
            db,
            organization_id=automation.organization_id,
            user_id=user_id,
            request=automation.objective,
            context=context,
            auto_execute=False,
        )
        require_execution_allowed()
        plan = db.query(WorkPlan).filter(WorkPlan.id == result.get("plan_id")).first()
        if plan and run:
            approval_id = _create_pre_execution_approval(
                db, automation=automation, plan=plan, user_id=user_id, run=run
            )
            return {
                "plan_id": plan.id,
                "status": WorkPlanStatus.WAITING_APPROVAL,
                "approval_id": approval_id,
            }
        return result

    require_execution_allowed()
    result = route_task(
        db,
        organization_id=automation.organization_id,
        user_id=user_id,
        request=automation.objective,
        context=context,
        auto_execute=True,
    )
    require_execution_allowed()
    return result


def trigger_run(
    db: Session,
    *,
    automation: Automation,
    user_id: str,
    trigger_source: str,
    scheduled_for: datetime | None = None,
    occurrence_key_override: str | None = None,
) -> AutomationRun:
    when = scheduled_for or _utcnow()
    key = occurrence_key_override or occurrence_key(when)

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
        write_audit(
            db,
            action="automation.run_skipped",
            organization_id=automation.organization_id,
            user_id=user_id,
            detail=automation.name,
        )
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
    token: FenceToken | None = None,
) -> None:
    if token is not None:
        controller = get_fence_controller(token.run_id)
        if controller is None or not controller.verify(token):
            return
    db.refresh(run)
    if run.status != AutomationRunStatus.RUNNING:
        return
    if run.finished_at is not None:
        return

    plan_id = result.get("plan_id")
    run.work_plan_id = plan_id or run.work_plan_id
    run.result_reference_json = json.dumps(result, ensure_ascii=False, default=str)

    plan_status = result.get("status")
    if plan_status == WorkPlanStatus.WAITING_APPROVAL:
        run.status = AutomationRunStatus.WAITING_APPROVAL
        run.finished_at = None
    elif plan_status == WorkPlanStatus.COMPLETED:
        run.status = AutomationRunStatus.SUCCEEDED
    elif plan_status == WorkPlanStatus.READY:
        run.status = (
            AutomationRunStatus.WAITING_APPROVAL
            if automation.requires_approval
            else AutomationRunStatus.SUCCEEDED
        )
    elif plan_status == WorkPlanStatus.FAILED:
        run.status = AutomationRunStatus.FAILED
        run.error = result.get("error") or result.get("message")
    else:
        run.status = AutomationRunStatus.SUCCEEDED if not result.get("error") else AutomationRunStatus.FAILED
        if result.get("error"):
            run.error = str(result.get("error"))

    run.cost_reference = _sum_run_cost(db, run.work_plan_id)

    if token is not None:
        from sqlalchemy import update

        from app.automation_models import AutomationRun as RunModel

        values = {
            "work_plan_id": run.work_plan_id,
            "result_reference_json": run.result_reference_json,
            "status": run.status,
            "finished_at": run.finished_at,
            "error": run.error,
            "cost_reference": run.cost_reference,
        }
        rows = (
            db.execute(
                update(RunModel)
                .where(
                    RunModel.id == run.id,
                    RunModel.status == AutomationRunStatus.RUNNING,
                    RunModel.execution_generation == token.generation,
                )
                .values(**values)
            ).rowcount
        )
        if rows == 0:
            db.rollback()
            return
        db.commit()
        db.refresh(run)
        return
    db.commit()


def _execute_run(db: Session, *, automation: Automation, run: AutomationRun, user_id: str) -> AutomationRun:
    workflow = json.loads(automation.workflow_config_json) if automation.workflow_config_json else {}
    skip_reason = _precheck_cost_limit(automation, workflow)
    if skip_reason:
        run.status = AutomationRunStatus.SKIPPED
        run.error = skip_reason
        run.finished_at = _utcnow()
        db.commit()
        write_audit(
            db,
            action="automation.run_skipped",
            organization_id=automation.organization_id,
            user_id=user_id,
            detail=skip_reason,
        )
        return run

    try:
        _assert_employee_tenant(db, automation)
    except ValueError as exc:
        run.status = AutomationRunStatus.FAILED
        run.error = str(exc)
        run.finished_at = _utcnow()
        db.commit()
        write_audit(
            db,
            action="automation.failed",
            organization_id=automation.organization_id,
            user_id=user_id,
            detail=str(exc),
        )
        return run

    max_attempts = automation.max_retries + 1
    run.status = AutomationRunStatus.RUNNING
    run.started_at = run.started_at or _utcnow()
    run.execution_generation = 1
    db.commit()

    controller = register_fence(run.id, run.execution_generation)
    token = controller.snapshot()
    fence_ctx = bind_fence_token(token)
    timed_out = False
    try:
        while run.attempt <= max_attempts:
            try:
                result = _run_with_timeout(
                    lambda: _invoke_orchestration_isolated(
                        automation_id=automation.id,
                        run_id=run.id,
                        user_id=user_id,
                        token=token,
                        db_bind=db.get_bind(),
                    ),
                    automation.timeout_seconds,
                )
                if timed_out:
                    break
                db.refresh(run)
                if run.status == AutomationRunStatus.WAITING_APPROVAL:
                    return run
                if run.status != AutomationRunStatus.RUNNING:
                    break
                _apply_run_result(db, automation=automation, run=run, result=result, token=token)
            except TimeoutError as exc:
                timed_out = True
                invalidate_run_execution(db, run=run, token=token, error=str(exc))
                write_audit(
                    db,
                    action="automation.timeout",
                    organization_id=automation.organization_id,
                    user_id=user_id,
                    detail=f"{automation.name}:{run.id}",
                )
                break
            except ExecutionCancelledError as exc:
                timed_out = True
                invalidate_run_execution(db, run=run, token=token, error=str(exc))
                write_audit(
                    db,
                    action="automation.timeout",
                    organization_id=automation.organization_id,
                    user_id=user_id,
                    detail=f"{automation.name}:{run.id}",
                )
                break
            except Exception as exc:
                run.status = AutomationRunStatus.FAILED
                run.error = str(exc)

            if timed_out:
                break
            if run.status == AutomationRunStatus.WAITING_APPROVAL:
                break
            if run.status != AutomationRunStatus.FAILED:
                break
            if run.attempt >= max_attempts:
                break

            run.attempt += 1
            run.status = AutomationRunStatus.RUNNING
            run.error = None
            run.finished_at = None
            write_audit(
                db,
                action="automation.retry",
                organization_id=automation.organization_id,
                user_id=user_id,
                detail=f"{automation.name}:attempt={run.attempt}",
            )
            if automation.retry_delay_seconds > 0:
                delay = min(automation.retry_delay_seconds, MAX_RETRY_DELAY_SECONDS)
                time.sleep(delay)
            if token is not None:
                from sqlalchemy import update

                from app.automation_models import AutomationRun as RunModel

                rows = (
                    db.execute(
                        update(RunModel)
                        .where(
                            RunModel.id == run.id,
                            RunModel.execution_generation == token.generation,
                            RunModel.status == AutomationRunStatus.FAILED,
                        )
                        .values(
                            attempt=run.attempt,
                            status=AutomationRunStatus.RUNNING,
                            error=None,
                            finished_at=None,
                        )
                    ).rowcount
                )
                if rows == 0:
                    break
                db.commit()
                db.refresh(run)
            else:
                db.commit()
    finally:
        reset_fence_token(fence_ctx)
        release_fence(run.id)

    if timed_out:
        refresh_next_run(db, automation)
        db.commit()
        write_audit(
            db,
            action="automation.failed",
            organization_id=automation.organization_id,
            user_id=user_id,
            detail=f"{automation.name}:{run.status}",
        )
        return run

    if run.status != AutomationRunStatus.WAITING_APPROVAL:
        run.finished_at = _utcnow()
    automation.last_run_at = run.finished_at or _utcnow()
    refresh_next_run(db, automation)
    db.commit()
    db.refresh(run)

    if run.status == AutomationRunStatus.SUCCEEDED:
        audit_action = "automation.succeeded"
    elif run.status == AutomationRunStatus.WAITING_APPROVAL:
        audit_action = "automation.waiting_approval"
    elif run.status == AutomationRunStatus.SKIPPED:
        audit_action = "automation.run_skipped"
    else:
        audit_action = "automation.failed"
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
    if (
        run.finished_at
        and run.status == AutomationRunStatus.FAILED
        and plan_status == WorkPlanStatus.COMPLETED
        and run.error
        and "timeout" in run.error.lower()
    ):
        return run
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
    elif plan_status == WorkPlanStatus.CANCELLED:
        run.status = AutomationRunStatus.CANCELLED
        run.finished_at = _utcnow()
        run.error = error or "Cancelado"
    else:
        return run

    run.cost_reference = _sum_run_cost(db, work_plan_id)
    if automation:
        automation.last_run_at = run.finished_at
        refresh_next_run(db, automation)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        action="automation.succeeded" if run.status == AutomationRunStatus.SUCCEEDED else "automation.failed",
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
    idem_key = internal_event_occurrence_key(event_type, payload)
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
            occurrence_key_override=idem_key,
        )
        runs.append(run)
    return runs


def run_now(db: Session, automation: Automation, user_id: str) -> AutomationRun:
    write_audit(
        db,
        action="automation.run_now",
        organization_id=automation.organization_id,
        user_id=user_id,
        detail=automation.name,
    )
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
