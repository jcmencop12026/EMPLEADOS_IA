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
    EmployeeKnowledgeSource,
    EmployeeTask,
    EmployeeToolGrant,
    EmployeeLimits,
    FinOpsRecord,
    KnowledgeSource,
    Tool,
    WorkPlan,
)
from app.services.execution_guard import (
    ExecutionCancelledError,
    commit_gated,
    require_execution_allowed,
)
from app.services.execution_workspace import current_worker_session
from app.services.authorization import (
    AuthorizationError,
    ExecutionDecision,
    assert_employee_has_capability,
    evaluate_tool_execution,
)
from app.services.llm_execution import run_llm_for_task, should_use_llm
from app.tools import docint, rips

_TOOL_EXECUTION_COUNTER = 0


def reset_tool_execution_counter() -> None:
    global _TOOL_EXECUTION_COUNTER
    _TOOL_EXECUTION_COUNTER = 0


def get_tool_execution_counter() -> int:
    return _TOOL_EXECUTION_COUNTER


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _detect_route(request: str, context: dict[str, Any] | None) -> tuple[str, str]:
    """Detecta ruta vía interfaz de dominio — G-01 (sin hardcode SALUD en coordinator)."""
    from app.services.domain_analysis import resolve_capability_code

    return resolve_capability_code(request, context)


def _find_employee_for_capability(db: Session, org_id: str, capability_id: str) -> AIEmployee | None:
    from app.services.salud_specialist_selection import score_employee_for_domain

    links = (
        db.query(EmployeeCapability)
        .filter(
            EmployeeCapability.capability_id == capability_id,
            EmployeeCapability.is_active.is_(True),
        )
        .all()
    )
    capability = db.query(Capability).filter(Capability.id == capability_id).first()
    domain = capability.code if capability else "estrategico"
    tool = (
        db.query(Tool)
        .filter(Tool.organization_id == org_id, Tool.capability_id == capability_id, Tool.is_active.is_(True))
        .first()
        if capability
        else None
    )

    candidates: list[tuple[float, AIEmployee]] = []
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
        if employee and tool:
            grant = (
                db.query(EmployeeToolGrant)
                .filter(
                    EmployeeToolGrant.employee_id == employee.id,
                    EmployeeToolGrant.tool_id == tool.id,
                )
                .first()
            )
            if not grant or grant.permission == ToolPermission.DENY:
                continue
        if employee:
            if domain.startswith("ips-") or domain == "rips":
                score_data = score_employee_for_domain(db, org_id, employee, domain.replace("ips-", ""))
                candidates.append((score_data["score"], employee))
            else:
                candidates.append((1.0, employee))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return None


def run_controlled_plan(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    employee_id: str,
    request: str,
    context: dict[str, Any] | None = None,
    capability_id: str | None = None,
    tool_id: str | None = None,
    knowledge_source_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Ejecuta un plan controlado para Test Lab con empleado/capability/tool explícitos."""
    correlation_id = str(uuid.uuid4())
    employee = db.query(AIEmployee).filter(
        AIEmployee.id == employee_id,
        AIEmployee.organization_id == organization_id,
    ).first()
    if not employee:
        return {"error": "Empleado no encontrado", "status": WorkPlanStatus.FAILED}

    capability: Capability | None = None
    tool: Tool | None = None

    if capability_id:
        capability = assert_employee_has_capability(
            db, org_id=organization_id, employee_id=employee.id, capability_id=capability_id,
        )
    elif tool_id:
        tool = db.query(Tool).filter(Tool.id == tool_id, Tool.organization_id == organization_id).first()
        if tool:
            capability = assert_employee_has_capability(
                db, org_id=organization_id, employee_id=employee.id, capability_id=tool.capability_id,
            )
    else:
        tool_code, _ = _detect_route(request, context)
        capability = (
            db.query(Capability)
            .filter(Capability.organization_id == organization_id, Capability.code == tool_code)
            .first()
        )
        if capability:
            assert_employee_has_capability(
                db, org_id=organization_id, employee_id=employee.id, capability_id=capability.id,
            )

    if tool_id:
        decision, tool, _ = evaluate_tool_execution(
            db,
            org_id=organization_id,
            employee_id=employee.id,
            tool_id=tool_id,
            capability_id=capability.id if capability else None,
            user_id=user_id,
        )
        if decision == ExecutionDecision.DENY:
            raise AuthorizationError("El empleado no tiene autorización para esta herramienta")
    elif capability and not tool:
        tool = (
            db.query(Tool)
            .filter(Tool.organization_id == organization_id, Tool.capability_id == capability.id, Tool.is_active.is_(True))
            .first()
        )
        if tool:
            decision, tool, _ = evaluate_tool_execution(
                db,
                org_id=organization_id,
                employee_id=employee.id,
                tool_id=tool.id,
                capability_id=capability.id,
                user_id=user_id,
            )
            if decision == ExecutionDecision.DENY:
                tool = None

    ctx = dict(context or {})
    if knowledge_source_ids:
        for kid in knowledge_source_ids:
            link = (
                db.query(EmployeeKnowledgeSource)
                .filter(
                    EmployeeKnowledgeSource.employee_id == employee.id,
                    EmployeeKnowledgeSource.knowledge_source_id == kid,
                    EmployeeKnowledgeSource.is_active.is_(True),
                )
                .first()
            )
            if not link:
                source = db.query(KnowledgeSource).filter(KnowledgeSource.id == kid).first()
                if not source or source.organization_id != organization_id:
                    raise AuthorizationError("Fuente de conocimiento no accesible")
                raise AuthorizationError("El empleado no tiene asignada esta fuente de conocimiento")
        ctx["knowledge_source_ids"] = knowledge_source_ids

    plan = WorkPlan(
        organization_id=organization_id,
        user_id=user_id,
        correlation_id=correlation_id,
        request=request,
        objective=f"Prueba controlada: {request[:120]}",
        status=WorkPlanStatus.PLANNING,
        capability_id=capability.id if capability else None,
        employee_id=employee.id,
        tool_id=tool.id if tool else None,
    )
    db.add(plan)
    db.flush()

    publish(
        EventMessage(
            event_type=WorkEventType.WORK_REQUESTED,
            organization_id=organization_id,
            work_plan_id=plan.id,
            user_id=user_id,
            payload={"request": request, "correlation_id": correlation_id, "test_lab": True},
        ),
        db,
    )

    plan.status = WorkPlanStatus.READY
    steps = [
        {"sequence": 1, "title": "Validar autorización", "executor_type": ExecutorType.RULE},
        {"sequence": 2, "title": f"Ejecutar {tool.code if tool else 'análisis'}", "executor_type": tool.executor_type if tool else ExecutorType.PYTHON},
        {"sequence": 3, "title": "Consolidar resultado", "executor_type": ExecutorType.RULE},
    ]
    plan.steps_json = json.dumps(steps, ensure_ascii=False)

    task = EmployeeTask(
        organization_id=organization_id,
        work_plan_id=plan.id,
        employee_id=employee.id,
        capability_id=capability.id if capability else None,
        tool_id=tool.id if tool else None,
        sequence=1,
        title=f"Test Lab {tool.code if tool else 'general'}",
        executor_type=tool.executor_type if tool else ExecutorType.PYTHON,
        status=EmployeeTaskStatus.READY,
        inputs_json=json.dumps(ctx, ensure_ascii=False),
    )
    db.add(task)
    commit_gated(db)
    return execute_plan(db, plan_id=plan.id, user_id=user_id)


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
        commit_gated(db)
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
    preferred_employee_id = (context or {}).get("employee_id")
    employee: AIEmployee | None = None
    if preferred_employee_id:
        employee = (
            db.query(AIEmployee)
            .filter(
                AIEmployee.id == preferred_employee_id,
                AIEmployee.organization_id == organization_id,
                AIEmployee.is_active.is_(True),
            )
            .first()
        )
    if not employee:
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
    commit_gated(db)

    if auto_execute:
        require_execution_allowed(db)
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
    commit_gated(db)

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
    commit_gated(db)

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
            from app.services.finops_service import assert_budget_allows_consumption

            try:
                assert_budget_allows_consumption(
                    db,
                    plan.organization_id,
                    employee_id=employee.id,
                    category="Modelo IA",
                )
            except PermissionError as exc:
                publish(
                    EventMessage(
                        event_type="FINOPS_LIMIT_REACHED",
                        organization_id=plan.organization_id,
                        work_plan_id=plan.id,
                        task_id=task.id,
                        user_id=user_id,
                        payload={
                            "employee_id": employee.id,
                            "reason": str(exc),
                            "policy": "Bloquear",
                        },
                    ),
                    db,
                )
                raise
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

        decision, tool, _capability = evaluate_tool_execution(
            db,
            org_id=plan.organization_id,
            employee_id=task.employee_id,
            tool_id=task.tool_id,
            capability_id=task.capability_id,
            user_id=user_id,
        )

        if decision == ExecutionDecision.DENY:
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
            raise AuthorizationError("Ejecución denegada por política de autorización")

        inputs = json.loads(task.inputs_json or "{}")
        inputs["request"] = plan.request
        require_execution_allowed(db)

        if decision == ExecutionDecision.REQUIRES_APPROVAL:
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
                action=f"Ejecutar {tool.code if tool else 'análisis'}",
                employee_name=employee.name if employee else None,
                reason="La política de capability/herramienta requiere aprobación humana antes de ejecutar.",
                evidence_json=None,
                impact=None,
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
            commit_gated(db)
            return {"task_id": task.id, "status": task.status}

        output = _run_execution(
            db,
            employee=employee,
            tool=tool,
            tool_code=tool.code if tool else "docint",
            inputs=inputs,
            plan=plan,
            task=task,
            user_id=user_id,
        )
        require_execution_allowed(db)
        if output.get("source") == "llm" and output.get("error"):
            raise RuntimeError(output.get("summary") or "Error de inferencia IA")
        duration_ms = int((time.monotonic() - start_ms) * 1000)

        task.outputs_json = json.dumps(output, ensure_ascii=False)
        task.confidence = output.get("confidence")

        if output.get("confidence", 1.0) < 0.7:
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
            commit_gated(db)
            return {"task_id": task.id, "status": task.status}

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

        if output.get("source") != "llm":
            from app.services.finops_service import resolve_opportunity_id

            opp_id = resolve_opportunity_id(
                db, plan.organization_id, work_plan_id=plan.id
            )
            db.add(
                FinOpsRecord(
                    organization_id=plan.organization_id,
                    work_plan_id=plan.id,
                    task_id=task.id,
                    opportunity_id=opp_id,
                    employee_id=employee.id if employee else None,
                    model_name=employee.model_name if employee else None,
                    provider=employee.model_provider if employee else "rule-engine",
                    duration_ms=duration_ms,
                )
            )
        commit_gated(db)
        return {"task_id": task.id, "status": task.status, "output": output}

    except ExecutionCancelledError:
        db.rollback()
        raise
    except (PermissionError, AuthorizationError) as exc:
        task.status = EmployeeTaskStatus.FAILED
        task.error = str(exc)
        task.completed_at = _utcnow()
        plan.status = WorkPlanStatus.FAILED
        plan.error = str(exc)
        if employee:
            employee.status = EmployeeStatus.ERROR
        commit_gated(db)
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
        db.commit()
        return {"task_id": task.id, "status": task.status, "error": str(exc)}
    except Exception as exc:
        task.status = EmployeeTaskStatus.FAILED
        task.error = str(exc)
        task.completed_at = _utcnow()
        plan.status = WorkPlanStatus.FAILED
        plan.error = str(exc)
        if employee:
            employee.status = EmployeeStatus.ERROR
        commit_gated(db)
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


def _run_execution(
    db: Session,
    *,
    employee: AIEmployee | None,
    tool: Tool | None,
    tool_code: str,
    inputs: dict[str, Any],
    plan: WorkPlan,
    task: EmployeeTask,
    user_id: str,
) -> dict[str, Any]:
    user_prompt = inputs.get("request") or inputs.get("prompt") or plan.request or ""
    context = inputs.get("context") or {}
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except json.JSONDecodeError:
            context = {}

    if should_use_llm(employee, tool.executor_type if tool else task.executor_type):
        return run_llm_for_task(
            db,
            organization_id=plan.organization_id,
            employee=employee,
            user_prompt=str(user_prompt),
            context=context,
            work_plan_id=plan.id,
            task_id=task.id,
            user_id=user_id,
            knowledge_source_ids=context.get("knowledge_source_ids"),
        )
    return _run_tool(tool_code, inputs)


def _run_tool(tool_code: str, inputs: dict[str, Any]) -> dict[str, Any]:
    global _TOOL_EXECUTION_COUNTER
    _TOOL_EXECUTION_COUNTER += 1
    require_execution_allowed(current_worker_session())
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
        if task and not task.outputs_json:
            tool_obj = db.query(Tool).filter(Tool.id == task.tool_id).first()
            inputs = json.loads(task.inputs_json or "{}")
            if plan:
                inputs["request"] = plan.request
            require_execution_allowed(db)
            start_ms = time.monotonic()
            output = _run_execution(
                db,
                employee=employee,
                tool=tool_obj,
                tool_code=tool_obj.code if tool_obj else "docint",
                inputs=inputs,
                plan=plan,
                task=task,
                user_id=user_id,
            )
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            task.outputs_json = json.dumps(output, ensure_ascii=False)
            task.confidence = output.get("confidence")
            if output.get("source") != "llm":
                db.add(
                    FinOpsRecord(
                        organization_id=organization_id,
                        work_plan_id=plan.id if plan else approval.work_plan_id,
                        task_id=task.id,
                        model_name=employee.model_name if employee else None,
                        provider=employee.model_provider if employee else "rule-engine",
                        duration_ms=duration_ms,
                    )
                )
        else:
            tasks = (
                db.query(EmployeeTask).filter(EmployeeTask.work_plan_id == plan.id).all()
                if plan
                else []
            )
            needs_execution = (
                plan
                and plan.status == WorkPlanStatus.WAITING_APPROVAL
                and (not tasks or any(t.status == EmployeeTaskStatus.READY for t in tasks))
            )
            if needs_execution:
                commit_gated(db)
                execute_plan(db, plan_id=plan.id, user_id=user_id)
                db.refresh(plan)
                from app.services.automation_service import sync_run_from_work_plan

                sync_run_from_work_plan(
                    db,
                    work_plan_id=plan.id,
                    plan_status=plan.status,
                    error=plan.error,
                )
                publish(
                    EventMessage(
                        event_type=WorkEventType.APPROVAL_COMPLETED,
                        organization_id=organization_id,
                        work_plan_id=plan.id,
                        task_id=task.id if task else None,
                        user_id=user_id,
                        payload={"decision": decision, "approval_id": approval_id},
                    ),
                    db,
                )
                return _build_plan_response(db, plan)
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

    commit_gated(db)
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
        from app.services.automation_service import sync_run_from_work_plan

        sync_run_from_work_plan(
            db,
            work_plan_id=plan.id,
            plan_status=plan.status,
            error=plan.error,
        )
        return _build_plan_response(db, plan)
    return {"approval_id": approval_id, "status": approval.status}
