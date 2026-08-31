"""Métricas reales por empleado para auditoría determinística."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.employee_audit_models import EmployeeAuditPolicy
from app.experience_models import EmployeeExperienceRecord
from app.knowledge_models import EmployeeKnowledgeGrant
from app.llm_models import LlmInferenceLog
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    EmployeeLimits,
    EmployeeTestRun,
    FinOpsRecord,
    WorkPlan,
)

DEFAULT_THRESHOLDS: dict[str, dict[str, float]] = {
    "error_rate": {"advertencia": 0.15, "critico": 0.35},
    "latency_ms_avg": {"advertencia": 8000.0, "critico": 20000.0},
    "cost_ratio_daily": {"advertencia": 0.8, "critico": 1.0},
    "tokens_total": {"advertencia": 200000.0, "critico": 500000.0},
    "success_rate": {"advertencia": 0.7, "critico": 0.5},
    "failed_executions": {"advertencia": 2.0, "critico": 5.0},
    "approval_reject_rate": {"advertencia": 0.3, "critico": 0.5},
    "failed_tests": {"advertencia": 1.0, "critico": 3.0},
}

DEFAULT_METRICS_ACTIVE = [
    "executions",
    "errors",
    "latency",
    "tokens",
    "cost",
    "success_rate",
    "approvals",
    "tests",
    "knowledge_grants",
    "experience",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(raw: str | None) -> Any:
    import json

    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def default_thresholds() -> dict[str, dict[str, float]]:
    return {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}


def default_metrics_active() -> list[str]:
    return list(DEFAULT_METRICS_ACTIVE)


def merge_thresholds(policy: EmployeeAuditPolicy | None) -> dict[str, dict[str, float]]:
    base = default_thresholds()
    if policy and policy.thresholds_json:
        custom = _parse_json(policy.thresholds_json) or {}
        for key, levels in custom.items():
            if isinstance(levels, dict):
                base[key] = {**base.get(key, {}), **{k: float(v) for k, v in levels.items()}}
    return base


def metrics_active_for(policy: EmployeeAuditPolicy | None) -> list[str]:
    if policy and policy.metrics_active_json:
        raw = _parse_json(policy.metrics_active_json)
        if isinstance(raw, list):
            return [str(x) for x in raw]
    return default_metrics_active()


def collect_employee_metrics(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    window_days: int = 7,
) -> dict[str, Any]:
    """Agrega métricas observables en ventana — sin inferir exactitud."""
    now = _utcnow()
    since = now - timedelta(days=window_days)
    emp = (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )
    if not emp:
        return {"error": "Empleado no encontrado"}

    plans = (
        db.query(WorkPlan)
        .filter(
            WorkPlan.organization_id == org_id,
            WorkPlan.employee_id == employee_id,
            WorkPlan.created_at >= since,
        )
        .all()
    )
    total_exec = len(plans)
    failed_exec = sum(1 for p in plans if p.status == "FAILED")
    completed_exec = sum(1 for p in plans if p.status == "COMPLETED")
    success_rate = (completed_exec / total_exec) if total_exec else None
    error_rate = (failed_exec / total_exec) if total_exec else 0.0

    llm_rows = (
        db.query(LlmInferenceLog)
        .filter(
            LlmInferenceLog.organization_id == org_id,
            LlmInferenceLog.employee_id == employee_id,
            LlmInferenceLog.created_at >= since,
        )
        .all()
    )
    tokens_total = sum((r.tokens_total or 0) for r in llm_rows)
    latency_vals = [r.latency_ms for r in llm_rows if r.latency_ms is not None]
    latency_avg = (sum(latency_vals) / len(latency_vals)) if latency_vals else None
    llm_errors = sum(1 for r in llm_rows if r.status != "OK")

    finops_cost = (
        db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0))
        .filter(
            FinOpsRecord.organization_id == org_id,
            FinOpsRecord.employee_id == employee_id,
            FinOpsRecord.created_at >= since,
        )
        .scalar()
    )
    llm_cost = sum((r.cost or 0) for r in llm_rows)
    cost_total = float(finops_cost or 0) + float(llm_cost or 0)

    limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == employee_id).first()
    daily_limit = limits.daily_cost_limit if limits else None
    cost_ratio_daily = (cost_total / daily_limit) if daily_limit and daily_limit > 0 else None

    test_runs = (
        db.query(EmployeeTestRun)
        .filter(EmployeeTestRun.employee_id == employee_id, EmployeeTestRun.created_at >= since)
        .all()
    )
    failed_tests = sum(1 for t in test_runs if t.status == "FAILED")
    passed_tests = sum(1 for t in test_runs if t.status == "PASSED")

    plan_ids = [p.id for p in plans]
    approvals_pending = 0
    approvals_rejected = 0
    approvals_total = 0
    if plan_ids:
        approvals = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.organization_id == org_id, ApprovalRequest.work_plan_id.in_(plan_ids))
            .all()
        )
        approvals_total = len(approvals)
        approvals_rejected = sum(1 for a in approvals if a.status == "REJECTED")
        approvals_pending = sum(1 for a in approvals if a.status == "PENDING")
    approval_reject_rate = (approvals_rejected / approvals_total) if approvals_total else None

    grants_active = (
        db.query(func.count(EmployeeKnowledgeGrant.id))
        .filter(
            EmployeeKnowledgeGrant.organization_id == org_id,
            EmployeeKnowledgeGrant.employee_id == employee_id,
            EmployeeKnowledgeGrant.is_active.is_(True),
        )
        .scalar()
        or 0
    )

    exp_negative = (
        db.query(func.count(EmployeeExperienceRecord.id))
        .filter(
            EmployeeExperienceRecord.organization_id == org_id,
            EmployeeExperienceRecord.employee_id == employee_id,
            EmployeeExperienceRecord.estado.in_(["NEGATIVO", "FALLIDO", "DEBIL"]),
            EmployeeExperienceRecord.created_at >= since,
        )
        .scalar()
        or 0
    )

    return {
        "employee_id": employee_id,
        "employee_code": emp.code,
        "employee_name": emp.name,
        "lifecycle_status": emp.lifecycle_status,
        "certified_at": emp.certified_at.isoformat() if emp.certified_at else None,
        "window_days": window_days,
        "window_start": since.isoformat(),
        "executions_total": total_exec,
        "executions_failed": failed_exec,
        "executions_completed": completed_exec,
        "error_rate": round(error_rate, 4),
        "success_rate": round(success_rate, 4) if success_rate is not None else None,
        "latency_ms_avg": round(latency_avg, 2) if latency_avg is not None else None,
        "llm_calls": len(llm_rows),
        "llm_errors": llm_errors,
        "tokens_total": int(tokens_total),
        "cost_total_usd": round(cost_total, 4),
        "cost_ratio_daily": round(cost_ratio_daily, 4) if cost_ratio_daily is not None else None,
        "daily_cost_limit": daily_limit,
        "failed_tests": failed_tests,
        "passed_tests": passed_tests,
        "approvals_total": approvals_total,
        "approvals_rejected": approvals_rejected,
        "approvals_pending": approvals_pending,
        "approval_reject_rate": round(approval_reject_rate, 4) if approval_reject_rate is not None else None,
        "knowledge_grants_active": int(grants_active),
        "experience_negative_count": int(exp_negative),
        "model_provider": emp.model_provider,
        "model_name": emp.model_name,
    }
