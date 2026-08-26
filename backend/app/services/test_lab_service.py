from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import TestLabEventType, TestLabStatus, WorkPlanStatus
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    Capability,
    EmployeeTestRun,
    FinOpsRecord,
    TestLabRun,
    Tool,
    WorkPlan,
)
from app.services.authorization import (
    AuthorizationError,
    assert_employee_has_capability,
    assert_employee_knowledge_access_batch,
    assert_employee_tool_authorized,
    get_employee,
)
from app.services.coordinator import run_controlled_plan


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _status_label(plan_status: str) -> str:
    mapping = {
        WorkPlanStatus.COMPLETED: TestLabStatus.COMPLETED,
        WorkPlanStatus.WAITING_APPROVAL: TestLabStatus.WAITING_APPROVAL,
        WorkPlanStatus.FAILED: TestLabStatus.FAILED,
        WorkPlanStatus.RUNNING: TestLabStatus.RUNNING,
    }
    return mapping.get(plan_status, TestLabStatus.FAILED)


def _run_out(run: TestLabRun, *, employee: AIEmployee | None = None, capability: Capability | None = None, tool: Tool | None = None) -> dict[str, Any]:
    return {
        "id": run.id,
        "employee_id": run.employee_id,
        "employee_name": employee.name if employee else None,
        "task_description": run.task_description,
        "status": run.status,
        "capability_id": run.capability_id,
        "capability_code": capability.code if capability else None,
        "tool_id": run.tool_id,
        "tool_code": tool.code if tool else None,
        "knowledge_source_ids": json.loads(run.knowledge_source_ids_json) if run.knowledge_source_ids_json else [],
        "work_plan_id": run.work_plan_id,
        "execution_id": run.work_plan_id,
        "result": json.loads(run.result_json) if run.result_json else None,
        "error_message": run.error_message,
        "duration_ms": run.duration_ms,
        "cost": run.cost,
        "cost_label": f"${run.cost:.4f}" if run.cost is not None else "No disponible",
        "tokens_in": run.tokens_in,
        "tokens_out": run.tokens_out,
        "approval_id": run.approval_id,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def list_test_runs(db: Session, org_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    runs = (
        db.query(TestLabRun)
        .filter(TestLabRun.organization_id == org_id)
        .order_by(TestLabRun.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for run in runs:
        employee = db.query(AIEmployee).filter(AIEmployee.id == run.employee_id).first()
        capability = db.query(Capability).filter(Capability.id == run.capability_id).first() if run.capability_id else None
        tool = db.query(Tool).filter(Tool.id == run.tool_id).first() if run.tool_id else None
        result.append(_run_out(run, employee=employee, capability=capability, tool=tool))
    return result


def get_test_run(db: Session, org_id: str, run_id: str) -> dict[str, Any] | None:
    run = db.query(TestLabRun).filter(TestLabRun.id == run_id, TestLabRun.organization_id == org_id).first()
    if not run:
        return None
    employee = db.query(AIEmployee).filter(AIEmployee.id == run.employee_id).first()
    capability = db.query(Capability).filter(Capability.id == run.capability_id).first() if run.capability_id else None
    tool = db.query(Tool).filter(Tool.id == run.tool_id).first() if run.tool_id else None
    return _run_out(run, employee=employee, capability=capability, tool=tool)


def execute_test_lab(
    db: Session,
    org_id: str,
    user_id: str,
    *,
    employee_id: str,
    task_description: str,
    context: dict[str, Any] | None = None,
    capability_id: str | None = None,
    tool_id: str | None = None,
    knowledge_source_ids: list[str] | None = None,
    auto_execute: bool = True,
) -> dict[str, Any]:
    start = time.monotonic()
    employee = get_employee(db, org_id, employee_id)
    run = TestLabRun(
        organization_id=org_id,
        user_id=user_id,
        employee_id=employee.id,
        capability_id=capability_id,
        tool_id=tool_id,
        knowledge_source_ids_json=json.dumps(knowledge_source_ids or []),
        task_description=task_description,
        context_json=json.dumps(context or {}, ensure_ascii=False),
        status=TestLabStatus.RUNNING,
    )
    db.add(run)
    db.flush()
    write_audit(
        db,
        action=TestLabEventType.STARTED,
        organization_id=org_id,
        user_id=user_id,
        detail=f"test_lab:{run.id}",
    )

    try:
        if capability_id:
            assert_employee_has_capability(db, org_id=org_id, employee_id=employee.id, capability_id=capability_id)
        if tool_id:
            assert_employee_tool_authorized(
                db,
                org_id=org_id,
                employee_id=employee.id,
                tool_id=tool_id,
                capability_id=capability_id,
                user_id=user_id,
            )
        if knowledge_source_ids:
            assert_employee_knowledge_access_batch(
                db, org_id=org_id, employee_id=employee.id, knowledge_source_ids=knowledge_source_ids,
            )

        if not auto_execute:
            run.status = TestLabStatus.BLOCKED
            run.error_message = "Ejecución bloqueada por configuración"
            run.completed_at = _utcnow()
            db.commit()
            return _run_out(run, employee=employee)

        plan_result = run_controlled_plan(
            db,
            organization_id=org_id,
            user_id=user_id,
            employee_id=employee.id,
            request=task_description,
            context=context,
            capability_id=capability_id,
            tool_id=tool_id,
            knowledge_source_ids=knowledge_source_ids,
        )

        run.work_plan_id = plan_result.get("plan_id")
        run.status = _status_label(plan_result.get("status", WorkPlanStatus.FAILED))
        run.result_json = json.dumps(plan_result, ensure_ascii=False)
        run.error_message = plan_result.get("error")
        run.duration_ms = int((time.monotonic() - start) * 1000)

        if run.work_plan_id:
            finops = (
                db.query(FinOpsRecord)
                .filter(FinOpsRecord.work_plan_id == run.work_plan_id)
                .order_by(FinOpsRecord.created_at.desc())
                .first()
            )
            if finops:
                run.cost = finops.cost
                run.tokens_in = finops.tokens_in
                run.tokens_out = finops.tokens_out

            if plan_result.get("status") == WorkPlanStatus.WAITING_APPROVAL:
                approval = (
                    db.query(ApprovalRequest)
                    .filter(ApprovalRequest.work_plan_id == run.work_plan_id)
                    .order_by(ApprovalRequest.created_at.desc())
                    .first()
                )
                if approval:
                    run.approval_id = approval.id

        run.completed_at = _utcnow()
        db.add(
            EmployeeTestRun(
                employee_id=employee.id,
                test_type="TEST_LAB",
                status="PASSED" if run.status == TestLabStatus.COMPLETED else "FAILED",
                input_json=run.context_json,
                actual_json=run.result_json,
                latency_ms=run.duration_ms,
                cost=run.cost,
                error=run.error_message,
            )
        )
        db.commit()
        event = TestLabEventType.COMPLETED if run.status == TestLabStatus.COMPLETED else TestLabEventType.FAILED
        write_audit(db, action=event, organization_id=org_id, user_id=user_id, detail=f"test_lab:{run.id}:{run.status}")

        capability = db.query(Capability).filter(Capability.id == capability_id).first() if capability_id else None
        tool = db.query(Tool).filter(Tool.id == tool_id).first() if tool_id else None
        return _run_out(run, employee=employee, capability=capability, tool=tool)

    except AuthorizationError as exc:
        run.status = TestLabStatus.BLOCKED
        run.error_message = str(exc)
        run.duration_ms = int((time.monotonic() - start) * 1000)
        run.completed_at = _utcnow()
        db.add(
            EmployeeTestRun(
                employee_id=employee.id,
                test_type="TEST_LAB",
                status="FAILED",
                input_json=run.context_json,
                error=str(exc),
                latency_ms=run.duration_ms,
            )
        )
        db.commit()
        write_audit(db, action=TestLabEventType.FAILED, organization_id=org_id, user_id=user_id, detail=str(exc))
        return _run_out(run, employee=employee)

    except Exception as exc:
        run.status = TestLabStatus.FAILED
        run.error_message = "Error al ejecutar la prueba"
        run.duration_ms = int((time.monotonic() - start) * 1000)
        run.completed_at = _utcnow()
        db.commit()
        write_audit(db, action=TestLabEventType.FAILED, organization_id=org_id, user_id=user_id, detail=str(exc)[:500])
        return _run_out(run, employee=employee)
