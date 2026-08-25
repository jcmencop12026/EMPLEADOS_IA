from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.enums import (
    ApprovalStatus,
    EmployeeLifecycleStatus,
    EmployeeStatus,
    EmployeeTaskStatus,
    ExecutorType,
    ToolPermission,
    WorkEventType,
    WorkPlanStatus,
)
from app.events.bus import EventMessage, publish
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    Capability,
    EmployeeCapability,
    EmployeeTask,
    EmployeeLimits,
    EmployeeToolGrant,
    FinOpsRecord,
    Tool,
    WorkPlan,
)
from app.tools import docint, rips


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _detect_route(request: str, context: dict[str, Any] | None) -> tuple[str, str]:
    text = request.lower()
    ctx = context or {}
    if ctx.get("tool") in ("rips", "docint"):
        return ctx["tool"], "salud"
    if "rips" in text:
        return "rips", "salud"
    if any(k in text for k in ("documento", "docint", "documentos")):
        return "docint", "salud"
    if ctx.get("rips") or ctx.get("data", {}).get("usuarios"):
        return "rips", "salud"
    if ctx.get("documents") or ctx.get("documentos"):
        return "docint", "salud"
    return "docint", "salud"


def _find_employee_for_capability(db: Session, org_id: str, capability_id: str) -> AIEmployee | None:
    links = (
        db.query(EmployeeCapability)
        .filter(EmployeeCapability.capability_id == capability_id)
        .all()
    )
    for link in links:
        employee = (
            db.query(AIEmployee)
            .filter(
                AIEmployee.id == link.employee_id,
                AIEmployee.organization_id == org_id,
                AIEmployee.is_active.is_(True),
                AIEmployee.lifecycle_status.in_([
                    EmployeeLifecycleStatus.ACTIVE,
                    EmployeeLifecycleStatus.PUBLISHED,
                ]),
            )
            .first()
        )
        if employee:
            return employee
    return None


def _tool_grant_for_employee(db: Session, employee_id: str | None, tool_id: str | None) -> EmployeeToolGrant | None:
    if not employee_id or not tool_id:
        return None
    return (
        db.query(EmployeeToolGrant)
        .filter(EmployeeToolGrant.employee_id == employee_id, EmployeeToolGrant.tool_id == tool_id)
        .first()
    )


def route_task(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    request: str,
    context: dict[str, Any] | None = None,
    auto_execute: bool = True,
) -> dict[str, Any]:
    correlation_id = str(uuid.uuid4())
    tool_code, _domain = _detect_route(request, context)

    plan = WorkPlan(
        organization_id=organization_id,
        user_id=user_id,
        correlation_id=correlation_id,
        request=request,
        objective=f"Analizar y reportar problemas ({tool_code.upper()})",
        status=WorkPlanStatus.PLANNING,
    )
    db.add(plan)
    db.flush()

    publish(
        EventMessage(
            event_type=WorkEventType.WORK_REQUESTED,
            organization_id=organization_id,
            work_plan_id=plan.id,
            user_id=user_id,
            payload={"request": request, "correlation_id": correlation_id},
        ),
        db,
    )

    capability = (
        db.query(Capability)
        .filter(Capability.organization_id == organization_id, Capability.code == tool_code, Capability.is_active.is_(True))
        .first()
    )
    if not capability:
        plan.status = WorkPlanStatus.FAILED
        plan.error = f"Capacidad no disponible: {tool_code}"
        db.commit()
        publish(
            EventMessage(
                event_type=WorkEventType.WORK_FAILED,
                organization_id=organization_id,
                work_plan_id=plan.id,
                user_id=user_id,
                payload={"error": plan.error},
            ),
            db,
        )
        return {"plan_id": plan.id, "status": plan.status, "error": plan.error}

    tool = (
        db.query(Tool)
        .filter(Tool.organization_id == organization_id, Tool.capability_id == capability.id, Tool.is_active.is_(True))
        .first()
    )
    employee = _find_employee_for_capability(db, organization_id, capability.id)

    plan.capability_id = capability.id
    plan.employee_id = employee.id if employee else None
    plan.tool_id = tool.id if tool else None
    plan.status = WorkPlanStatus.READY
    steps = [
        {"sequence": 1, "title": "Validar entrada", "executor_type": ExecutorType.RULE},
        {"sequence": 2, "title": f"Ejecutar {tool_code.upper()}", "executor_type": tool.executor_type if tool else ExecutorType.PYTHON},
        {"sequence": 3, "title": "Consolidar hallazgos", "executor_type": ExecutorType.RULE},
    ]
    plan.steps_json = json.dumps(steps, ensure_ascii=False)
    plan.dependencies_json = json.dumps([], ensure_ascii=False)

    publish(
        EventMessage(
            event_type=WorkEventType.WORK_PLANNED,
            organization_id=organization_id,
            work_plan_id=plan.id,
            user_id=user_id,
            payload={"capability": capability.code, "tool": tool.code if tool else None, "steps": steps},
        ),
        db,
    )

    task = EmployeeTask(
        organization_id=organization_id,
        work_plan_id=plan.id,
        employee_id=employee.id if employee else None,
        capability_id=capability.id,
        tool_id=tool.id if tool else None,
        sequence=1,
        title=f"Análisis {tool_code.upper()}",
        executor_type=tool.executor_type if tool else ExecutorType.PYTHON,
        status=EmployeeTaskStatus.READY,
        inputs_json=json.dumps(context or {}, ensure_ascii=False),
    )
    db.add(task)
    db.flush()

    if employee:
        employee.status = EmployeeStatus.PLANIFICANDO

    publish(
        EventMessage(
            event_type=WorkEventType.TASK_CREATED,
            organization_id=organization_id,
            work_plan_id=plan.id,
            task_id=task.id,
            user_id=user_id,
            payload={"title": task.title, "executor_type": task.executor_type},
        ),
        db,
    )
    db.commit()

    if auto_execute:
        return execute_plan(db, plan_id=plan.id, user_id=user_id)
    return {"plan_id": plan.id, "task_id": task.id, "status": plan.status}


def execute_plan(db: Session, *, plan_id: str, user_id: str) -> dict[str, Any]:
    plan = db.query(WorkPlan).filter(WorkPlan.id == plan_id).first()
    if not plan:
        return {"error": "Plan no encontrado"}

    if plan.status == WorkPlanStatus.WAITING_APPROVAL:
        return {"plan_id": plan.id, "status": plan.status, "message": "Pendiente de aprobación humana"}

    plan.status = WorkPlanStatus.RUNNING
    plan.started_at = plan.started_at or _utcnow()
    db.commit()

    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).order_by(EmployeeTask.sequence).all()
    all_outputs: list[dict[str, Any]] = []

    for task in tasks:
        result = _execute_task(db, task=task, plan=plan, user_id=user_id)
        all_outputs.append(result)
        if result.get("status") in (EmployeeTaskStatus.FAILED, EmployeeTaskStatus.WAITING_APPROVAL):
            break

    db.refresh(plan)
    return _build_plan_response(db, plan)


def _execute_task(db: Session, *, task: EmployeeTask, plan: WorkPlan, user_id: str) -> dict[str, Any]:
    employee = db.query(AIEmployee).filter(AIEmployee.id == task.employee_id).first() if task.employee_id else None
    tool = db.query(Tool).filter(Tool.id == task.tool_id).first() if task.tool_id else None

    if employee:
        employee.status = EmployeeStatus.TRABAJANDO

    task.status = EmployeeTaskStatus.RUNNING
    task.started_at = _utcnow()
    db.commit()

    publish(
        EventMessage(
            event_type=WorkEventType.TASK_STARTED,
            organization_id=plan.organization_id,
            work_plan_id=plan.id,
            task_id=task.id,
            user_id=user_id,
            payload={"executor_type": task.executor_type},
        ),
        db,
    )

    start_ms = time.monotonic()
    try:
        if employee:
            limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == employee.id).first()
            spent_today = (
                db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0.0))
                .filter(
                    FinOpsRecord.organization_id == plan.organization_id,
                    FinOpsRecord.created_at >= _utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                )
                .scalar()
            ) or 0.0
            if limits and limits.daily_cost_limit is not None and spent_today >= limits.daily_cost_limit:
                publish(
                    EventMessage(
                        event_type="FINOPS_LIMIT_REACHED",
                        organization_id=plan.organization_id,
                        work_plan_id=plan.id,
                        task_id=task.id,
                        user_id=user_id,
                        payload={"employee_id": employee.id, "limit": limits.daily_cost_limit, "spent": spent_today},
                    ),
                    db,
                )
                raise PermissionError("Límite diario FinOps alcanzado")
        grant = _tool_grant_for_employee(db, task.employee_id, task.tool_id)
        if grant and grant.permission == ToolPermission.DENY:
            publish(
                EventMessage(
                    event_type="TOOL_DENIED",
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    task_id=task.id,
                    user_id=user_id,
                    payload={"employee_id": task.employee_id, "tool_id": task.tool_id},
                ),
                db,
            )
            raise PermissionError("Herramienta denegada para el empleado asignado")

        inputs = json.loads(task.inputs_json or "{}")
        inputs["request"] = plan.request
        output = _run_tool(tool.code if tool else "docint", inputs)
        duration_ms = int((time.monotonic() - start_ms) * 1000)

        task.outputs_json = json.dumps(output, ensure_ascii=False)
        task.confidence = output.get("confidence")
        requires_approval = (
            (tool and tool.requires_approval)
            or (grant and grant.permission == ToolPermission.REQUIRES_APPROVAL)
            or output.get("confidence", 1.0) < 0.7
        )

        if requires_approval:
            task.status = EmployeeTaskStatus.WAITING_APPROVAL
            task.approval_status = ApprovalStatus.PENDING
            plan.status = WorkPlanStatus.WAITING_APPROVAL
            plan.approval_status = ApprovalStatus.PENDING
            if employee:
                employee.status = EmployeeStatus.ESPERANDO_APROBACION

            approval = ApprovalRequest(
                organization_id=plan.organization_id,
                work_plan_id=plan.id,
                task_id=task.id,
                action=f"Publicar resultado {tool.code if tool else 'análisis'}",
                employee_name=employee.name if employee else None,
                reason="Confianza baja o herramienta de riesgo requiere revisión humana.",
                evidence_json=json.dumps(output.get("evidence", {}), ensure_ascii=False),
                impact=output.get("summary"),
                requested_by=user_id,
            )
            db.add(approval)
            db.flush()
            publish(
                EventMessage(
                    event_type=WorkEventType.APPROVAL_REQUIRED,
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    task_id=task.id,
                    user_id=user_id,
                    payload={"approval_id": approval.id, "reason": approval.reason},
                ),
                db,
            )
        else:
            task.status = EmployeeTaskStatus.COMPLETED
            task.approval_status = ApprovalStatus.NOT_REQUIRED
            task.completed_at = _utcnow()
            plan.status = WorkPlanStatus.COMPLETED
            plan.approval_status = ApprovalStatus.NOT_REQUIRED
            plan.result_json = task.outputs_json
            plan.summary = output.get("summary")
            plan.confidence = output.get("confidence")
            plan.completed_at = _utcnow()
            if employee:
                employee.status = EmployeeStatus.DISPONIBLE

            publish(
                EventMessage(
                    event_type=WorkEventType.TASK_COMPLETED,
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    task_id=task.id,
                    user_id=user_id,
                    payload={"summary": plan.summary, "confidence": plan.confidence},
                ),
                db,
            )
            publish(
                EventMessage(
                    event_type=WorkEventType.WORK_COMPLETED,
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    user_id=user_id,
                    payload={"summary": plan.summary},
                ),
                db,
            )

        db.add(
            FinOpsRecord(
                organization_id=plan.organization_id,
                work_plan_id=plan.id,
                task_id=task.id,
                model_name=employee.model_name if employee else None,
                provider=employee.model_provider if employee else "rule-engine",
                duration_ms=duration_ms,
            )
        )
        db.commit()
        return {"task_id": task.id, "status": task.status, "output": output}

    except Exception as exc:
        task.status = EmployeeTaskStatus.FAILED
        task.error = str(exc)
        task.completed_at = _utcnow()
        plan.status = WorkPlanStatus.FAILED
        plan.error = str(exc)
        if employee:
            employee.status = EmployeeStatus.ERROR
        db.commit()
        publish(
            EventMessage(
                event_type=WorkEventType.TASK_FAILED,
                organization_id=plan.organization_id,
                work_plan_id=plan.id,
                task_id=task.id,
                user_id=user_id,
                payload={"error": str(exc)},
            ),
            db,
        )
        publish(
            EventMessage(
                event_type=WorkEventType.WORK_FAILED,
                organization_id=plan.organization_id,
                work_plan_id=plan.id,
                user_id=user_id,
                payload={"error": str(exc)},
            ),
            db,
        )
        if not isinstance(exc, PermissionError):
            publish(
                EventMessage(
                    event_type="SYSTEM_ERROR",
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    task_id=task.id,
                    user_id=user_id,
                    payload={"error": str(exc)},
                ),
                db,
            )
        db.commit()
        return {"task_id": task.id, "status": task.status, "error": str(exc)}


def _run_tool(tool_code: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if tool_code == "rips":
        return rips.analyze_rips(inputs)
    return docint.analyze_documents(inputs)


def _build_plan_response(db: Session, plan: WorkPlan) -> dict[str, Any]:
    tasks = db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).all()
    result = json.loads(plan.result_json) if plan.result_json else None
    return {
        "plan_id": plan.id,
        "correlation_id": plan.correlation_id,
        "status": plan.status,
        "objective": plan.objective,
        "summary": plan.summary,
        "confidence": plan.confidence,
        "approval_status": plan.approval_status,
        "error": plan.error,
        "result": result,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "executor_type": t.executor_type,
                "confidence": t.confidence,
                "approval_status": t.approval_status,
            }
            for t in tasks
        ],
        "started_at": plan.started_at.isoformat() if plan.started_at else None,
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
    }


def decide_approval(
    db: Session,
    *,
    approval_id: str,
    organization_id: str,
    user_id: str,
    decision: str,
    comment: str | None = None,
) -> dict[str, Any]:
    approval = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.id == approval_id, ApprovalRequest.organization_id == organization_id)
        .first()
    )
    if not approval:
        return {"error": "Aprobación no encontrada"}
    if approval.status != "PENDING":
        return {"error": "Aprobación ya decidida"}

    plan = db.query(WorkPlan).filter(WorkPlan.id == approval.work_plan_id).first()
    task = db.query(EmployeeTask).filter(EmployeeTask.id == approval.task_id).first() if approval.task_id else None
    employee = db.query(AIEmployee).filter(AIEmployee.id == task.employee_id).first() if task and task.employee_id else None

    approval.decided_by = user_id
    approval.decided_at = _utcnow()
    approval.decision_comment = comment

    if decision == "approve":
        approval.status = "APPROVED"
        if task:
            task.status = EmployeeTaskStatus.COMPLETED
            task.approval_status = ApprovalStatus.APPROVED
            task.completed_at = _utcnow()
        if plan:
            plan.status = WorkPlanStatus.COMPLETED
            plan.approval_status = ApprovalStatus.APPROVED
            if task and task.outputs_json:
                plan.result_json = task.outputs_json
                output = json.loads(task.outputs_json)
                plan.summary = output.get("summary")
                plan.confidence = output.get("confidence")
            plan.completed_at = _utcnow()
        if employee:
            employee.status = EmployeeStatus.DISPONIBLE
    else:
        approval.status = "REJECTED"
        if task:
            task.status = EmployeeTaskStatus.FAILED
            task.approval_status = ApprovalStatus.REJECTED
        if plan:
            plan.status = WorkPlanStatus.FAILED
            plan.approval_status = ApprovalStatus.REJECTED
            plan.error = comment or "Rechazado por aprobador"
        if employee:
            employee.status = EmployeeStatus.DISPONIBLE

    publish(
        EventMessage(
            event_type=WorkEventType.APPROVAL_COMPLETED,
            organization_id=organization_id,
            work_plan_id=plan.id if plan else None,
            task_id=task.id if task else None,
            user_id=user_id,
            payload={"decision": decision, "approval_id": approval_id},
        ),
        db,
    )
    db.commit()
    if plan:
        return _build_plan_response(db, plan)
    return {"approval_id": approval_id, "status": approval.status}
