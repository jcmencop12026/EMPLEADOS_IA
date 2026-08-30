"""Servicio — Auditor determinístico de Empleados IA."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.employee_audit_models import (
    EmployeeAuditAssessment,
    EmployeeAuditFinding,
    EmployeeAuditPolicy,
    EmployeeAuditRun,
    HEALTH_STATUSES,
    RECOMMENDED_ACTIONS,
)
from app.enums import EmployeeLifecycleStatus
from app.models import Organization, User
from app.notifications import emit_event
from app.orchestration_models import AIEmployee
from app.permissions import check_permission, user_permissions
from app.services import control_center_service as cc_svc
from app.services.employee_audit_metrics import (
    collect_employee_metrics,
    merge_thresholds,
    metrics_active_for,
)

AUDIT_EVENT_GUARD = "_employee_audit_guard"
AUDIT_LOOP_EVENT_PREFIX = "employee.audit."

RULE_ACTION_MAP: dict[str, str] = {
    "FAILED_EXECUTIONS_HIGH": "SOLICITAR_REVISION_HUMANA",
    "ERROR_RATE_HIGH": "SOLICITAR_REVISION_HUMANA",
    "SUCCESS_RATE_LOW": "MEJORAR_INSTRUCCIONES",
    "LATENCY_HIGH": "CAMBIAR_MODELO",
    "COST_LIMIT_CRITICAL": "CAMBIAR_PROVEEDOR",
    "COST_LIMIT_WARNING": "AJUSTAR_AUTOMATIZACION",
    "TOKENS_HIGH": "AJUSTAR_AUTOMATIZACION",
    "FAILED_TESTS": "CAPACITAR",
    "NO_KNOWLEDGE_GRANTS": "ACTUALIZAR_CONOCIMIENTO",
    "APPROVAL_REJECTIONS_HIGH": "MEJORAR_INSTRUCCIONES",
    "EXPERIENCE_NEGATIVE": "CAPACITAR",
    "ACTIVE_WITHOUT_CERTIFICATION": "SOLICITAR_REVISION_HUMANA",
    "LLM_ERRORS_HIGH": "CAMBIAR_MODELO",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def resolve_organization_id(db: Session, user: User, requested_org_id: str | None) -> str:
    return cc_svc.resolve_organization_id(db, user, requested_org_id)


def get_or_create_org_policy(db: Session, org_id: str) -> EmployeeAuditPolicy:
    row = (
        db.query(EmployeeAuditPolicy)
        .filter(EmployeeAuditPolicy.organization_id == org_id, EmployeeAuditPolicy.employee_id.is_(None))
        .first()
    )
    if row:
        return row
    row = EmployeeAuditPolicy(
        organization_id=org_id,
        employee_id=None,
        thresholds_json=_json_dumps(merge_thresholds(None)),
        metrics_active_json=_json_dumps(metrics_active_for(None)),
        allowed_actions_json=_json_dumps({}),
    )
    db.add(row)
    db.flush()
    return row


def policy_to_dict(row: EmployeeAuditPolicy) -> dict[str, Any]:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "employee_id": row.employee_id,
        "enabled": row.enabled,
        "frequency": row.frequency,
        "window_days": row.window_days,
        "thresholds": _json_loads(row.thresholds_json) or merge_thresholds(None),
        "metrics_active": metrics_active_for(row),
        "allowed_actions": _json_loads(row.allowed_actions_json) or {},
        "budget_usd": row.budget_usd,
        "max_runs_per_window": row.max_runs_per_window,
        "window_hours": row.window_hours,
        "automation_id": row.automation_id,
        "last_executed_at": row.last_executed_at,
        "next_scheduled_at": row.next_scheduled_at,
    }


def update_org_policy(db: Session, org_id: str, data: dict[str, Any]) -> EmployeeAuditPolicy:
    row = get_or_create_org_policy(db, org_id)
    if data.get("enabled") is not None:
        row.enabled = bool(data["enabled"])
    if data.get("frequency"):
        row.frequency = str(data["frequency"]).upper()
    if data.get("window_days") is not None:
        row.window_days = int(data["window_days"])
    if data.get("thresholds") is not None:
        row.thresholds_json = _json_dumps(data["thresholds"])
    if data.get("metrics_active") is not None:
        row.metrics_active_json = _json_dumps(data["metrics_active"])
    if data.get("allowed_actions") is not None:
        row.allowed_actions_json = _json_dumps(data["allowed_actions"])
    if data.get("budget_usd") is not None:
        row.budget_usd = float(data["budget_usd"])
    if data.get("max_runs_per_window") is not None:
        row.max_runs_per_window = int(data["max_runs_per_window"])
    if data.get("window_hours") is not None:
        row.window_hours = int(data["window_hours"])
    if data.get("automation_id") is not None:
        row.automation_id = data["automation_id"]
    row.updated_at = _utcnow()
    db.flush()
    return row


def _severity_from_value(metric_key: str, value: float | None, thresholds: dict[str, dict[str, float]]) -> str | None:
    if value is None:
        return None
    levels = thresholds.get(metric_key, {})
    crit = levels.get("critico")
    adv = levels.get("advertencia")
    if crit is not None and value >= crit:
        return "CRITICO"
    if adv is not None and value >= adv:
        return "ADVERTENCIA"
    if metric_key == "success_rate" and crit is not None and value <= crit:
        return "CRITICO"
    if metric_key == "success_rate" and adv is not None and value <= adv:
        return "ADVERTENCIA"
    return "NORMAL"


def _evaluate_rules(
    metrics: dict[str, Any],
    thresholds: dict[str, dict[str, float]],
    active: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def add(
        rule_code: str,
        metric_name: str,
        observed: Any,
        threshold: Any,
        severity: str,
        semantic_kind: str,
        title: str,
        detail: str,
        evidence: dict[str, Any],
    ) -> None:
        if severity == "NORMAL":
            return
        action = RULE_ACTION_MAP.get(rule_code, "SOLICITAR_REVISION_HUMANA")
        findings.append(
            {
                "rule_code": rule_code,
                "metric_name": metric_name,
                "observed_value": str(observed),
                "threshold_value": str(threshold),
                "severity": severity,
                "semantic_kind": semantic_kind,
                "title": title,
                "detail": detail,
                "evidence": evidence,
                "recommended_action": action,
            }
        )

    if "executions" in active or "errors" in active:
        sev = _severity_from_value("failed_executions", float(metrics.get("executions_failed", 0)), thresholds)
        if sev:
            add(
                "FAILED_EXECUTIONS_HIGH",
                "executions_failed",
                metrics.get("executions_failed"),
                thresholds.get("failed_executions"),
                sev,
                "HECHO",
                "Ejecuciones fallidas en ventana",
                f"{metrics.get('executions_failed')} ejecuciones fallidas en {metrics.get('window_days')} días.",
                {"executions_failed": metrics.get("executions_failed")},
            )
        sev = _severity_from_value("error_rate", float(metrics.get("error_rate", 0)), thresholds)
        if sev:
            add(
                "ERROR_RATE_HIGH",
                "error_rate",
                metrics.get("error_rate"),
                thresholds.get("error_rate"),
                sev,
                "HECHO",
                "Tasa de error elevada",
                f"Tasa de error {metrics.get('error_rate')}.",
                {"error_rate": metrics.get("error_rate")},
            )

    if "success_rate" in active and metrics.get("success_rate") is not None:
        sev = _severity_from_value("success_rate", float(metrics["success_rate"]), thresholds)
        if sev:
            add(
                "SUCCESS_RATE_LOW",
                "success_rate",
                metrics.get("success_rate"),
                thresholds.get("success_rate"),
                sev,
                "HECHO",
                "Tasa de éxito baja",
                f"Tasa de éxito {metrics.get('success_rate')}.",
                {"success_rate": metrics.get("success_rate")},
            )

    if "latency" in active and metrics.get("latency_ms_avg") is not None:
        sev = _severity_from_value("latency_ms_avg", float(metrics["latency_ms_avg"]), thresholds)
        if sev:
            add(
                "LATENCY_HIGH",
                "latency_ms_avg",
                metrics.get("latency_ms_avg"),
                thresholds.get("latency_ms_avg"),
                sev,
                "HECHO",
                "Latencia media elevada",
                f"Latencia media {metrics.get('latency_ms_avg')} ms.",
                {"latency_ms_avg": metrics.get("latency_ms_avg")},
            )

    if "cost" in active and metrics.get("cost_ratio_daily") is not None:
        sev = _severity_from_value("cost_ratio_daily", float(metrics["cost_ratio_daily"]), thresholds)
        if sev:
            code = "COST_LIMIT_CRITICAL" if sev == "CRITICO" else "COST_LIMIT_WARNING"
            add(
                code,
                "cost_ratio_daily",
                metrics.get("cost_ratio_daily"),
                thresholds.get("cost_ratio_daily"),
                sev,
                "INFERENCIA",
                "Consumo de costo cerca del límite diario",
                f"Ratio costo/límite {metrics.get('cost_ratio_daily')}.",
                {"cost_total_usd": metrics.get("cost_total_usd"), "daily_limit": metrics.get("daily_cost_limit")},
            )

    if "tokens" in active:
        sev = _severity_from_value("tokens_total", float(metrics.get("tokens_total", 0)), thresholds)
        if sev:
            add(
                "TOKENS_HIGH",
                "tokens_total",
                metrics.get("tokens_total"),
                thresholds.get("tokens_total"),
                sev,
                "HECHO",
                "Consumo de tokens elevado",
                f"Tokens totales {metrics.get('tokens_total')}.",
                {"tokens_total": metrics.get("tokens_total")},
            )

    if "tests" in active:
        sev = _severity_from_value("failed_tests", float(metrics.get("failed_tests", 0)), thresholds)
        if sev:
            add(
                "FAILED_TESTS",
                "failed_tests",
                metrics.get("failed_tests"),
                thresholds.get("failed_tests"),
                sev,
                "HECHO",
                "Pruebas fallidas",
                f"{metrics.get('failed_tests')} pruebas fallidas en ventana.",
                {"failed_tests": metrics.get("failed_tests"), "passed_tests": metrics.get("passed_tests")},
            )

    if "knowledge_grants" in active:
        lifecycle = metrics.get("lifecycle_status")
        grants = int(metrics.get("knowledge_grants_active", 0))
        if lifecycle in ("ACTIVE", "PUBLISHED") and grants == 0:
            add(
                "NO_KNOWLEDGE_GRANTS",
                "knowledge_grants_active",
                grants,
                1,
                "ADVERTENCIA",
                "INFERENCIA",
                "Sin conocimiento asignado",
                "Empleado activo sin grants de conocimiento activos.",
                {"knowledge_grants_active": grants},
            )

    if "approvals" in active and metrics.get("approval_reject_rate") is not None:
        sev = _severity_from_value("approval_reject_rate", float(metrics["approval_reject_rate"]), thresholds)
        if sev:
            add(
                "APPROVAL_REJECTIONS_HIGH",
                "approval_reject_rate",
                metrics.get("approval_reject_rate"),
                thresholds.get("approval_reject_rate"),
                sev,
                "HECHO",
                "Rechazos de aprobación frecuentes",
                f"Tasa rechazo {metrics.get('approval_reject_rate')}.",
                {"approvals_rejected": metrics.get("approvals_rejected")},
            )

    if "experience" in active and int(metrics.get("experience_negative_count", 0)) > 0:
        add(
            "EXPERIENCE_NEGATIVE",
            "experience_negative_count",
            metrics.get("experience_negative_count"),
            0,
            "ADVERTENCIA",
            "HECHO",
            "Experiencias negativas registradas",
            f"{metrics.get('experience_negative_count')} registros de experiencia negativa.",
            {"experience_negative_count": metrics.get("experience_negative_count")},
        )

    if metrics.get("lifecycle_status") == EmployeeLifecycleStatus.ACTIVE and not metrics.get("certified_at"):
        add(
            "ACTIVE_WITHOUT_CERTIFICATION",
            "certified_at",
            None,
            "required",
            "CRITICO",
            "INFERENCIA",
            "Activo sin certificación registrada",
            "El empleado está ACTIVE pero sin certified_at.",
            {"lifecycle_status": metrics.get("lifecycle_status")},
        )

    if metrics.get("llm_errors", 0) > 0 and metrics.get("llm_calls", 0) > 0:
        ratio = metrics["llm_errors"] / metrics["llm_calls"]
        if ratio >= 0.3:
            add(
                "LLM_ERRORS_HIGH",
                "llm_error_ratio",
                round(ratio, 4),
                0.3,
                "CRITICO" if ratio >= 0.5 else "ADVERTENCIA",
                "HECHO",
                "Errores LLM frecuentes",
                f"{metrics.get('llm_errors')} errores en {metrics.get('llm_calls')} llamadas.",
                {"llm_errors": metrics.get("llm_errors"), "llm_calls": metrics.get("llm_calls")},
            )

    return findings


def _classify_health(findings: list[dict[str, Any]], metrics: dict[str, Any]) -> tuple[str, float]:
    """Reglas determinísticas de salud — documentadas en entregable."""
    if any(f["severity"] == "CRITICO" for f in findings):
        return "CRITICO", 20.0
    if any(f["rule_code"] == "ACTIVE_WITHOUT_CERTIFICATION" for f in findings):
        return "REQUIERE_INTERVENCION", 35.0
    crit_count = sum(1 for f in findings if f["severity"] == "CRITICO")
    adv_count = sum(1 for f in findings if f["severity"] == "ADVERTENCIA")
    if crit_count > 0 or adv_count >= 3:
        return "REQUIERE_MEJORA", 50.0
    if adv_count >= 1:
        return "OBSERVAR", 75.0
    if metrics.get("lifecycle_status") in ("FAILED_TEST", "DRAFT"):
        return "REQUIERE_INTERVENCION", 30.0
    return "SALUDABLE", 95.0


def _count_runs_in_window(db: Session, org_id: str, hours: int) -> int:
    since = _utcnow() - timedelta(hours=hours)
    return (
        db.query(EmployeeAuditRun)
        .filter(EmployeeAuditRun.organization_id == org_id, EmployeeAuditRun.started_at >= since)
        .count()
    )


def _build_idempotency_key(org_id: str, trigger_type: str, trigger_ref: str | None, employee_ids: list[str]) -> str:
    bucket = _utcnow().strftime("%Y%m%d%H") if trigger_type in ("SCHEDULE", "EVENT", "INTERNAL") else str(uuid.uuid4())
    raw = "|".join([org_id, trigger_type, trigger_ref or "", bucket, ",".join(sorted(employee_ids))])
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_employee_ids(
    db: Session,
    org_id: str,
    *,
    employee_id: str | None,
    employee_ids: list[str] | None,
    scope: str | None,
) -> list[str]:
    if employee_id:
        return [employee_id]
    if employee_ids:
        rows = (
            db.query(AIEmployee.id)
            .filter(AIEmployee.organization_id == org_id, AIEmployee.id.in_(employee_ids))
            .all()
        )
        return [r[0] for r in rows]
    q = db.query(AIEmployee.id).filter(AIEmployee.organization_id == org_id, AIEmployee.is_active.is_(True))
    if scope == "ACTIVE" or not scope:
        q = q.filter(AIEmployee.lifecycle_status.in_(["ACTIVE", "PUBLISHED", "CERTIFIED"]))
    return [r[0] for r in q.all()]


def execute_audit(
    db: Session,
    user: User,
    *,
    organization_id: str | None = None,
    employee_id: str | None = None,
    employee_ids: list[str] | None = None,
    scope: str | None = "ACTIVE",
    trigger_type: str = "MANUAL",
    trigger_ref: str | None = None,
    skip_rate_limit: bool = False,
) -> dict[str, Any]:
    org_id = resolve_organization_id(db, user, organization_id)
    policy = get_or_create_org_policy(db, org_id)
    if not policy.enabled and trigger_type == "MANUAL":
        pass  # manual siempre permitido con permiso execute
    elif not policy.enabled:
        return {"status": "SKIPPED", "reason": "Política deshabilitada"}

    if (
        not skip_rate_limit
        and trigger_type != "MANUAL"
        and _count_runs_in_window(db, org_id, policy.window_hours) >= policy.max_runs_per_window
    ):
        return {"status": "SKIPPED", "reason": "Límite de ejecuciones por ventana alcanzado"}

    target_ids = _resolve_employee_ids(
        db, org_id, employee_id=employee_id, employee_ids=employee_ids, scope=scope,
    )
    if not target_ids:
        return {"status": "SKIPPED", "reason": "Sin empleados en alcance"}

    idem = _build_idempotency_key(org_id, trigger_type, trigger_ref, target_ids)
    existing = (
        db.query(EmployeeAuditRun)
        .filter(EmployeeAuditRun.organization_id == org_id, EmployeeAuditRun.idempotency_key == idem)
        .first()
    )
    if existing and existing.status == "COMPLETED":
        return run_to_dict(db, existing)

    correlation_id = str(uuid.uuid4())
    run = existing or EmployeeAuditRun(
        organization_id=org_id,
        policy_id=policy.id,
        trigger_type=trigger_type,
        trigger_ref=trigger_ref,
        scope_json=_json_dumps({"employee_ids": target_ids, "scope": scope}),
        status="RUNNING",
        correlation_id=correlation_id,
        idempotency_key=idem,
        initiated_by=user.id,
        cost_usd=0.0,
    )
    if not existing:
        db.add(run)
        db.flush()
    else:
        run.status = "RUNNING"
        run.started_at = _utcnow()
        run.error_message = None

    thresholds = merge_thresholds(policy)
    active_metrics = metrics_active_for(policy)
    total_findings = 0
    assessments_out: list[dict[str, Any]] = []

    try:
        for emp_id in target_ids:
            metrics = collect_employee_metrics(db, org_id, emp_id, window_days=policy.window_days)
            if metrics.get("error"):
                continue
            rule_findings = _evaluate_rules(metrics, thresholds, active_metrics)
            health, score = _classify_health(rule_findings, metrics)

            assessment = EmployeeAuditAssessment(
                organization_id=org_id,
                run_id=run.id,
                employee_id=emp_id,
                health_status=health,
                score=score,
                metrics_snapshot_json=_json_dumps(metrics),
                lifecycle_status=metrics.get("lifecycle_status"),
            )
            db.add(assessment)
            db.flush()

            finding_rows: list[dict[str, Any]] = []
            for f in rule_findings:
                finding = EmployeeAuditFinding(
                    organization_id=org_id,
                    run_id=run.id,
                    assessment_id=assessment.id,
                    employee_id=emp_id,
                    rule_code=f["rule_code"],
                    metric_name=f["metric_name"],
                    observed_value=f.get("observed_value"),
                    threshold_value=f.get("threshold_value"),
                    severity=f["severity"],
                    semantic_kind=f["semantic_kind"],
                    title=f["title"],
                    detail=f.get("detail"),
                    evidence_json=_json_dumps(f.get("evidence")),
                    recommended_action=f.get("recommended_action"),
                    status="ABIERTO",
                    correlation_id=correlation_id,
                )
                db.add(finding)
                db.flush()
                total_findings += 1
                if f["severity"] == "CRITICO" and health in ("CRITICO", "REQUIERE_INTERVENCION"):
                    _maybe_notify_critical(db, org_id, emp_id, finding, metrics, user.id)
                finding_rows.append(finding_to_dict(finding))

            assessments_out.append(
                {
                    **assessment_to_dict(assessment, metrics.get("employee_name")),
                    "metrics": metrics,
                    "findings": finding_rows,
                }
            )

        run.status = "COMPLETED"
        run.employee_count = len(target_ids)
        run.findings_count = total_findings
        run.finished_at = _utcnow()
        run.cost_usd = 0.0
        policy.last_executed_at = run.finished_at
        if policy.frequency == "DAILY":
            policy.next_scheduled_at = run.finished_at + timedelta(days=1)
        elif policy.frequency == "WEEKLY":
            policy.next_scheduled_at = run.finished_at + timedelta(days=7)
        elif policy.frequency == "MONTHLY":
            policy.next_scheduled_at = run.finished_at + timedelta(days=30)
        db.commit()
        db.refresh(run)
        return run_to_dict(db, run, assessments_out)
    except Exception as exc:
        run.status = "FAILED"
        run.error_message = str(exc)[:500]
        run.finished_at = _utcnow()
        db.commit()
        raise


def _maybe_notify_critical(
    db: Session,
    org_id: str,
    employee_id: str,
    finding: EmployeeAuditFinding,
    metrics: dict[str, Any],
    user_id: str | None,
) -> None:
    recent = (
        db.query(EmployeeAuditFinding)
        .filter(
            EmployeeAuditFinding.organization_id == org_id,
            EmployeeAuditFinding.employee_id == employee_id,
            EmployeeAuditFinding.rule_code == finding.rule_code,
            EmployeeAuditFinding.severity == "CRITICO",
            EmployeeAuditFinding.created_at >= _utcnow() - timedelta(hours=24),
        )
        .count()
    )
    if recent > 1:
        return
    payload = {
        "employee_id": employee_id,
        "finding_id": finding.id,
        "rule_code": finding.rule_code,
        "correlation_id": finding.correlation_id,
        "employee_audit_guard": True,
    }
    notif = emit_event(
        "EMPLOYEE_AUDIT_CRITICAL",
        org_id,
        "employee_audit",
        employee_id,
        payload,
        db,
        commit=False,
    )
    if notif:
        finding.notification_id = notif[0].id


def finding_to_dict(row: EmployeeAuditFinding) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "assessment_id": row.assessment_id,
        "employee_id": row.employee_id,
        "rule_code": row.rule_code,
        "metric_name": row.metric_name,
        "observed_value": row.observed_value,
        "threshold_value": row.threshold_value,
        "severity": row.severity,
        "semantic_kind": row.semantic_kind,
        "title": row.title,
        "detail": row.detail,
        "evidence": _json_loads(row.evidence_json) or {},
        "recommended_action": row.recommended_action,
        "status": row.status,
        "correlation_id": row.correlation_id,
        "created_at": row.created_at,
    }


def assessment_to_dict(row: EmployeeAuditAssessment, employee_name: str | None = None) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "employee_id": row.employee_id,
        "employee_name": employee_name,
        "health_status": row.health_status,
        "score": row.score,
        "metrics": _json_loads(row.metrics_snapshot_json) or {},
        "lifecycle_status": row.lifecycle_status,
        "created_at": row.created_at,
    }


def run_to_dict(
    db: Session,
    run: EmployeeAuditRun,
    assessments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if assessments is None:
        assessments = []
        for a in db.query(EmployeeAuditAssessment).filter(EmployeeAuditAssessment.run_id == run.id).all():
            metrics = _json_loads(a.metrics_snapshot_json) or {}
            findings = [
                finding_to_dict(f)
                for f in db.query(EmployeeAuditFinding).filter(EmployeeAuditFinding.assessment_id == a.id).all()
            ]
            assessments.append(
                {
                    **assessment_to_dict(a, metrics.get("employee_name")),
                    "metrics": metrics,
                    "findings": findings,
                }
            )
    return {
        "id": run.id,
        "organization_id": run.organization_id,
        "trigger_type": run.trigger_type,
        "trigger_ref": run.trigger_ref,
        "status": run.status,
        "correlation_id": run.correlation_id,
        "employee_count": run.employee_count,
        "findings_count": run.findings_count,
        "cost_usd": run.cost_usd,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "error_message": run.error_message,
        "assessments": assessments,
    }


def list_health(db: Session, user: User, organization_id: str | None = None) -> list[dict[str, Any]]:
    org_id = resolve_organization_id(db, user, organization_id)
    employees = db.query(AIEmployee).filter(AIEmployee.organization_id == org_id, AIEmployee.is_active.is_(True)).all()
    out: list[dict[str, Any]] = []
    for emp in employees:
        latest = (
            db.query(EmployeeAuditAssessment)
            .filter(
                EmployeeAuditAssessment.organization_id == org_id,
                EmployeeAuditAssessment.employee_id == emp.id,
            )
            .order_by(EmployeeAuditAssessment.created_at.desc())
            .first()
        )
        open_f = (
            db.query(EmployeeAuditFinding)
            .filter(
                EmployeeAuditFinding.organization_id == org_id,
                EmployeeAuditFinding.employee_id == emp.id,
                EmployeeAuditFinding.status == "ABIERTO",
            )
            .count()
        )
        crit_f = (
            db.query(EmployeeAuditFinding)
            .filter(
                EmployeeAuditFinding.organization_id == org_id,
                EmployeeAuditFinding.employee_id == emp.id,
                EmployeeAuditFinding.status == "ABIERTO",
                EmployeeAuditFinding.severity == "CRITICO",
            )
            .count()
        )
        out.append(
            {
                "employee_id": emp.id,
                "employee_name": emp.name,
                "organization_id": org_id,
                "health_status": latest.health_status if latest else "OBSERVAR",
                "score": latest.score if latest else None,
                "lifecycle_status": emp.lifecycle_status,
                "last_audit_at": latest.created_at if latest else None,
                "open_findings": open_f,
                "critical_findings": crit_f,
            }
        )
    return out


def centro_control_resumen(db: Session, user: User, organization_id: str | None = None) -> dict[str, Any]:
    org_id = resolve_organization_id(db, user, organization_id)
    health_rows = list_health(db, user, organization_id=org_id)
    counts = {h: 0 for h in HEALTH_STATUSES}
    for row in health_rows:
        st = row.get("health_status")
        if st in counts:
            counts[st] += 1
    last_run = (
        db.query(EmployeeAuditRun)
        .filter(EmployeeAuditRun.organization_id == org_id, EmployeeAuditRun.status == "COMPLETED")
        .order_by(EmployeeAuditRun.finished_at.desc())
        .first()
    )
    open_findings = (
        db.query(EmployeeAuditFinding)
        .filter(EmployeeAuditFinding.organization_id == org_id, EmployeeAuditFinding.status == "ABIERTO")
        .count()
    )
    policy = get_or_create_org_policy(db, org_id)
    overdue = 0
    next_scheduled = _as_utc(policy.next_scheduled_at)
    if next_scheduled and next_scheduled < _utcnow():
        overdue = 1
    return {
        "organization_id": org_id,
        "total": len(health_rows),
        "saludables": counts.get("SALUDABLE", 0),
        "en_observacion": counts.get("OBSERVAR", 0),
        "requieren_mejora": counts.get("REQUIERE_MEJORA", 0),
        "requieren_intervencion": counts.get("REQUIERE_INTERVENCION", 0),
        "criticos": counts.get("CRITICO", 0),
        "ultima_auditoria_at": last_run.finished_at if last_run else None,
        "hallazgos_abiertos": open_findings,
        "auditorias_vencidas": overdue,
    }


def list_trabajo_contract(db: Session, org_id: str) -> list[dict[str, Any]]:
    """Contrato portable para Mi Trabajo — no modifica trabajo_service."""
    rows = (
        db.query(EmployeeAuditFinding)
        .filter(
            EmployeeAuditFinding.organization_id == org_id,
            EmployeeAuditFinding.status == "ABIERTO",
            EmployeeAuditFinding.severity.in_(["CRITICO", "ADVERTENCIA"]),
        )
        .order_by(EmployeeAuditFinding.created_at.desc())
        .limit(50)
        .all()
    )
    out: list[dict[str, Any]] = []
    for f in rows:
        assessment = db.query(EmployeeAuditAssessment).filter(EmployeeAuditAssessment.id == f.assessment_id).first()
        health = assessment.health_status if assessment else "OBSERVAR"
        requires = f.severity == "CRITICO" or health in ("CRITICO", "REQUIERE_INTERVENCION")
        out.append(
            {
                "id": f"auditoria_hallazgo:{f.id}",
                "tipo": "auditoria_hallazgo",
                "asunto": f.title,
                "modulo": "auditor_empleados",
                "employee_id": f.employee_id,
                "severity": f.severity,
                "health_status": health,
                "recommended_action": f.recommended_action,
                "correlation_id": f.correlation_id,
                "enlace": f"/empleados/auditoria?employee_id={f.employee_id}",
                "requires_action": requires,
            }
        )
    return out


def process_scheduled_audits(db: Session) -> int:
    """Invocado por evento employee.audit.scheduled — no scheduler paralelo."""
    now = _utcnow()
    policies = (
        db.query(EmployeeAuditPolicy)
        .filter(
            EmployeeAuditPolicy.enabled.is_(True),
            EmployeeAuditPolicy.employee_id.is_(None),
            EmployeeAuditPolicy.next_scheduled_at.isnot(None),
            EmployeeAuditPolicy.next_scheduled_at <= now,
        )
        .all()
    )
    from app.models import User

    count = 0
    for policy in policies:
        admin = db.query(User).filter(User.organization_id == policy.organization_id, User.role == "admin").first()
        if not admin:
            continue
        result = execute_audit(
            db,
            admin,
            organization_id=policy.organization_id,
            scope="ACTIVE",
            trigger_type="SCHEDULE",
            trigger_ref="employee.audit.scheduled",
        )
        if result.get("status") not in ("SKIPPED",):
            count += 1
    return count
