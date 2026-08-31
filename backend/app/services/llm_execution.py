"""Servicio de ejecución LLM integrado con coordinator, knowledge y FinOps."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gateway import gateway as llm_gateway
from app.gateway.prompt_builder import (
    assemble_messages,
    build_knowledge_context,
    build_system_instructions,
    trace_components,
)
from app.gateway.types import LlmMessage
from app.orchestration_models import (
    AIEmployee,
    EmployeeInstructions,
    EmployeeModelPolicy,
)
from app.services.finops_service import registrar_consumo
from app.services.llm_provider_service import update_inference_log_cost
from app.services.knowledge_retrieval import retrieve_knowledge


from app.gateway.providers import is_executable_llm_provider


def is_llm_provider(provider: str | None) -> bool:
    """Allowlist estricta — solo proveedores LLM ejecutables en V1."""
    return is_executable_llm_provider(provider)


def should_use_llm(
    employee: AIEmployee | None,
    tool_executor_type: str | None = None,
) -> bool:
    from app.enums import ExecutorType

    if tool_executor_type != ExecutorType.AI_AGENT:
        return False
    return True


def _load_policy(db: Session, employee_id: str) -> EmployeeModelPolicy | None:
    return (
        db.query(EmployeeModelPolicy)
        .filter(EmployeeModelPolicy.employee_id == employee_id)
        .first()
    )


def _load_instructions(db: Session, employee_id: str) -> EmployeeInstructions | None:
    return (
        db.query(EmployeeInstructions)
        .filter(EmployeeInstructions.employee_id == employee_id)
        .first()
    )


def run_llm_for_task(
    db: Session,
    *,
    organization_id: str,
    employee: AIEmployee | None,
    user_prompt: str,
    context: dict[str, Any] | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    user_id: str | None = None,
    knowledge_source_ids: list[str] | None = None,
    transport: Any | None = None,
) -> dict[str, Any]:
    context = context or {}
    employee_id = employee.id if employee else None
    policy = _load_policy(db, employee_id) if employee_id else None
    instructions = _load_instructions(db, employee_id) if employee_id else None

    preferred_provider = (
        policy.preferred_provider if policy and policy.preferred_provider
        else (employee.model_provider if employee else None)
    )
    explicit_preferred = bool(preferred_provider and str(preferred_provider).strip())
    preferred_model = (
        policy.preferred_model if policy and policy.preferred_model
        else (employee.model_name if employee else None)
    )
    fallback_model = policy.fallback_model if policy else None
    parameters: dict[str, Any] = {}
    if policy:
        if policy.temperature is not None:
            parameters["temperature"] = policy.temperature
        if policy.max_tokens is not None:
            parameters["max_tokens"] = policy.max_tokens
    timeout = policy.timeout_seconds if policy else None

    knowledge_chunks: list[dict[str, Any]] = []
    if knowledge_source_ids or context.get("include_knowledge"):
        query = user_prompt or context.get("request", "")
        knowledge_chunks = retrieve_knowledge(
            db,
            tenant_id=organization_id,
            query=query,
            limit=5,
            employee_id=employee_id,
        )

    system_text = build_system_instructions(instructions)
    knowledge_context = build_knowledge_context(knowledge_chunks)
    messages = assemble_messages(
        user_prompt=user_prompt,
        system_instructions=None,
        knowledge_context=knowledge_context,
    )

    trace_meta = trace_components(
        has_instructions=bool(system_text),
        knowledge_chunk_count=len(knowledge_chunks),
        user_prompt_length=len(user_prompt),
    )

    response = llm_gateway.complete(
        db,
        organization_id=organization_id,
        messages=messages,
        system_instructions=system_text,
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
        fallback_model=fallback_model,
        parameters=parameters,
        timeout_seconds=timeout,
        metadata=trace_meta,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        transport=transport,
        require_explicit_preferred=explicit_preferred,
    )

    finops_record = None
    finops_registration_failed = False
    if response.success:
        try:
            finops_record = registrar_consumo(
                db,
                organization_id=organization_id,
                user_id=user_id,
                employee_id=employee_id,
                work_plan_id=work_plan_id,
                task_id=task_id,
                execution_ref=response.trace_id,
                provider=response.provider,
                model_name=response.model,
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                duration_ms=response.latency_ms,
            )
            if finops_record and response.trace_id:
                update_inference_log_cost(
                    db,
                    organization_id,
                    response.trace_id,
                    cost=float(finops_record.cost) if finops_record.cost is not None else None,
                    currency=finops_record.currency,
                )
        except Exception as exc:
            finops_registration_failed = True
            write_audit(
                db,
                action="finops.registration.failed",
                organization_id=organization_id,
                user_id=user_id,
                detail=json.dumps(
                    {
                        "trace_id": response.trace_id,
                        "provider": response.provider,
                        "model": response.model,
                        "organization_id": organization_id,
                        "execution_ref": response.trace_id,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)[:500],
                    },
                    ensure_ascii=False,
                ),
            )

        write_audit(
            db,
            action="llm.inference.success",
            organization_id=organization_id,
            user_id=user_id,
            detail=json.dumps(
                {
                    "trace_id": response.trace_id,
                    "provider": response.provider,
                    "model": response.model,
                    "tokens_total": response.tokens_total,
                    "fallback_used": response.fallback_used,
                },
                ensure_ascii=False,
            ),
        )

        summary = (response.text or "")[:500]
        return {
            "summary": summary,
            "confidence": 0.85,
            "response": response.text,
            "source": "llm",
            "provider": response.provider,
            "model": response.model,
            "tokens_in": response.tokens_in,
            "tokens_out": response.tokens_out,
            "tokens_total": response.tokens_total,
            "latency_ms": response.latency_ms,
            "finish_reason": response.finish_reason,
            "trace_id": response.trace_id,
            "fallback_used": response.fallback_used,
            "initial_provider": response.initial_provider,
            "fallback_provider": response.fallback_provider,
            "cost": finops_record.cost if finops_record else None,
            "finops_registration_failed": finops_registration_failed,
            "evidence": {
                "knowledge_chunks": len(knowledge_chunks),
                "trace_components": trace_meta,
            },
        }

    error = response.error
    public_error = error.to_public_dict() if error else None
    public_initial_error = (
        response.initial_error.to_public_dict() if response.initial_error else None
    )
    write_audit(
        db,
        action="llm.inference.error",
        organization_id=organization_id,
        user_id=user_id,
        detail=json.dumps(
            {
                "trace_id": response.trace_id,
                "category": error.category if error else None,
                "message": error.message if error else None,
                "fallback_used": response.fallback_used,
            },
            ensure_ascii=False,
        ),
    )
    return {
        "summary": error.message if error else "Error de inferencia IA",
        "confidence": 0.0,
        "error": public_error,
        "source": "llm",
        "trace_id": response.trace_id,
        "fallback_used": response.fallback_used,
        "initial_error": public_initial_error,
    }
