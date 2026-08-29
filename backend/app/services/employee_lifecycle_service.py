"""MB-06 — Ciclo de vida fábrica empleados IA: versionado, pruebas, aprobación, capacitación."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.automation_models import Automation
from app.models import User
from app.enums import (
    ApprovalStatus,
    EmployeeApprovalKind,
    EmployeeEventType,
    EmployeeLifecycleStatus,
    EmployeeTestCategory,
    EmployeeTrainingType,
    RiskLevel,
    TestType,
    WorkPlanStatus,
)
from app.llm_models import LlmProviderConfig
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    Capability,
    EmployeeCapability,
    EmployeeFactoryApproval,
    EmployeeInstructions,
    EmployeeKnowledgeSource,
    EmployeeLimits,
    EmployeeModelPolicy,
    EmployeeTestCase,
    EmployeeTestRun,
    EmployeeToolGrant,
    EmployeeTraining,
    EmployeeVersion,
    Tool,
    WorkPlan,
)
from app.services import agent_factory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


LIFECYCLE_PHASE_MAP = {
    EmployeeLifecycleStatus.DRAFT: "BORRADOR",
    EmployeeLifecycleStatus.CONFIGURING: "CONFIGURADO",
    EmployeeLifecycleStatus.READY_FOR_TEST: "CONFIGURADO",
    EmployeeLifecycleStatus.TESTING: "EN_PRUEBAS",
    EmployeeLifecycleStatus.FAILED_TEST: "EN_PRUEBAS",
    EmployeeLifecycleStatus.READY_FOR_CERTIFICATION: "EN_PRUEBAS",
    EmployeeLifecycleStatus.CERTIFIED: "APROBADO",
    EmployeeLifecycleStatus.PUBLISHED: "PUBLICADO",
    EmployeeLifecycleStatus.ACTIVE: "ACTIVO",
    EmployeeLifecycleStatus.PAUSED: "PAUSADO",
    EmployeeLifecycleStatus.RETIRED: "RETIRADO",
}

SIGNIFICANT_CHANGE_KEYS = frozenset({
    "instructions",
    "knowledge",
    "tools",
    "model_policy",
    "limits",
    "capability_ids",
    "risk_level",
})

CRITICAL_RISK_LEVELS = frozenset({RiskLevel.HIGH, RiskLevel.CRITICAL})


def _get_employee(db: Session, org_id: str, employee_id: str) -> AIEmployee | None:
    return (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )


def lifecycle_phase(status: str) -> str:
    return LIFECYCLE_PHASE_MAP.get(status, status)


def _test_category_for_type(test_type: str) -> str:
    if test_type in (TestType.SECURITY, TestType.NEGATIVE):
        return EmployeeTestCategory.SECURITY
    if test_type == TestType.FUNCTIONAL:
        return EmployeeTestCategory.FUNCTIONAL
    return EmployeeTestCategory.TECHNICAL


def build_inventory(db: Session, org_id: str, employee_id: str) -> dict[str, Any] | None:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return None

    snapshot = agent_factory._employee_config_snapshot(db, emp)
    instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
    policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first()
    limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == emp.id).first()
    automations = (
        db.query(Automation)
        .filter(Automation.organization_id == org_id, Automation.employee_id == emp.id)
        .all()
    )
    knowledge_sources = (
        db.query(EmployeeKnowledgeSource)
        .filter(
            EmployeeKnowledgeSource.employee_id == emp.id,
            EmployeeKnowledgeSource.organization_id == org_id,
        )
        .all()
    )

    return {
        "id": emp.id,
        "code": emp.code,
        "name": emp.name,
        "objective": emp.objective,
        "role": emp.role,
        "responsibilities": instructions.operating_rules if instructions else None,
        "organization_id": emp.organization_id,
        "lifecycle_status": emp.lifecycle_status,
        "lifecycle_phase": lifecycle_phase(emp.lifecycle_status),
        "operational_status": emp.status,
        "version": emp.version,
        "instructions": snapshot.get("instructions"),
        "knowledge": [
            {
                "id": k.id,
                "name": k.name,
                "source_type": k.source_type,
                "knowledge_source_id": k.knowledge_source_id,
                "is_active": k.is_active,
                "assigned_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in knowledge_sources
        ],
        "tools": snapshot.get("tools"),
        "capabilities": snapshot.get("capabilities"),
        "automations": [{"id": a.id, "name": a.name, "status": a.status} for a in automations],
        "model": {
            "provider": policy.preferred_provider if policy else emp.model_provider,
            "model": policy.preferred_model if policy else emp.model_name,
            "fallback_model": policy.fallback_model if policy else None,
            "allowed_models": json.loads(policy.allowed_models_json) if policy and policy.allowed_models_json else [],
        },
        "limits": snapshot.get("limits"),
        "finops": {
            "budget_daily": policy.budget_daily if policy else None,
            "cost_ceiling": policy.cost_ceiling if policy else None,
            "daily_cost_limit": limits.daily_cost_limit if limits else None,
            "task_cost_limit": limits.task_cost_limit if limits else None,
        },
        "permissions": snapshot.get("tools"),
        "approvals_pending": _pending_factory_approvals(db, org_id, emp.id),
        "publication": {
            "published_at": emp.published_at.isoformat() if emp.published_at else None,
            "certified_at": emp.certified_at.isoformat() if emp.certified_at else None,
            "last_training_at": emp.last_training_at.isoformat() if emp.last_training_at else None,
        },
    }


def validate_configuration(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"valid": False, "errors": ["Empleado no encontrado"]}

    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []

    caps = db.query(EmployeeCapability).filter(EmployeeCapability.employee_id == emp.id, EmployeeCapability.is_active.is_(True)).count()
    checks.append({"check": "capabilities", "ok": caps > 0, "detail": f"{caps} capacidad(es)"})
    if caps == 0:
        errors.append("Sin capacidades asignadas")

    tools = db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id).count()
    checks.append({"check": "tools", "ok": tools > 0, "detail": f"{tools} herramienta(s)"})
    if tools == 0:
        errors.append("Sin herramientas asignadas")

    instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
    has_instructions = bool(instructions and (instructions.role_text or instructions.objective_text or emp.role or emp.objective))
    checks.append({"check": "instructions", "ok": has_instructions, "detail": "rol/objetivo definido"})
    if not has_instructions:
        errors.append("Instrucciones incompletas (rol u objetivo)")

    knowledge = db.query(EmployeeKnowledgeSource).filter(EmployeeKnowledgeSource.employee_id == emp.id, EmployeeKnowledgeSource.is_active.is_(True)).count()
    checks.append({"check": "knowledge", "ok": knowledge > 0, "detail": f"{knowledge} fuente(s)"})
    if knowledge == 0:
        warnings.append("Sin fuentes de conocimiento asignadas")

    policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first()
    provider = policy.preferred_provider if policy else emp.model_provider
    model_ok = bool(provider)
    if provider and provider != "rule-engine":
        cfg = (
            db.query(LlmProviderConfig)
            .filter(LlmProviderConfig.organization_id == org_id, LlmProviderConfig.provider_key == provider, LlmProviderConfig.is_active.is_(True))
            .first()
        )
        model_ok = cfg is not None
        if not cfg:
            errors.append(f"Proveedor '{provider}' no configurado en la organización")
    checks.append({"check": "model_provider", "ok": model_ok, "detail": provider or "sin proveedor"})

    limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == emp.id).first()
    checks.append({
        "check": "limits",
        "ok": limits is not None,
        "detail": f"timeout={limits.timeout_seconds if limits else 'N/A'}s",
    })

    passed_tests = (
        db.query(EmployeeTestRun)
        .filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "PASSED")
        .count()
    )
    checks.append({"check": "tests_passed", "ok": passed_tests > 0, "detail": f"{passed_tests} prueba(s) PASS"})
    if passed_tests == 0:
        errors.append("Sin pruebas exitosas")

    failed = db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "FAILED").count()
    if failed:
        errors.append(f"{failed} prueba(s) fallida(s)")

    automations = db.query(Automation).filter(Automation.organization_id == org_id, Automation.employee_id == emp.id, Automation.status == "ERROR").count()
    if automations:
        warnings.append(f"{automations} automatización(es) en error")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "lifecycle_phase": lifecycle_phase(emp.lifecycle_status),
    }


def _diff_payload(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for key in SIGNIFICANT_CHANGE_KEYS:
        if key in new and json.dumps(old.get(key), sort_keys=True) != json.dumps(new.get(key), sort_keys=True):
            changed.append(key)
    return changed


def create_version(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    *,
    reason: str,
    changed_fields: list[str] | None = None,
    status: str = "DRAFT",
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    snapshot = agent_factory._employee_config_snapshot(db, emp)
    prev_version = emp.version
    new_version_num = emp.version

    version_row = EmployeeVersion(
        organization_id=org_id,
        employee_id=emp.id,
        version=new_version_num,
        previous_version=prev_version - 1 if prev_version > 1 else None,
        configuration_json=json.dumps(snapshot, ensure_ascii=False),
        changed_fields_json=json.dumps(changed_fields or [], ensure_ascii=False),
        change_reason=reason,
        status=status,
        created_by_id=user_id,
    )
    db.add(version_row)
    db.commit()
    db.refresh(version_row)

    write_audit(
        db,
        action="employee.version_created",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({"employee_id": emp.id, "version": new_version_num, "reason": reason}, ensure_ascii=False),
    )
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_VERSION_CHANGED, emp.id, {"version": new_version_num, "reason": reason})
    return {
        "id": version_row.id,
        "version": version_row.version,
        "previous_version": version_row.previous_version,
        "changed_fields": changed_fields or [],
        "reason": reason,
        "status": version_row.status,
        "created_at": version_row.created_at.isoformat(),
    }


def maybe_version_on_update(
    db: Session,
    org_id: str,
    user_id: str,
    emp: AIEmployee,
    payload: dict[str, Any],
    before_snapshot: dict[str, Any],
) -> list[str]:
    after_snapshot = dict(before_snapshot)
    if "instructions" in payload:
        after_snapshot["instructions"] = payload["instructions"]
    if "knowledge" in payload:
        after_snapshot["knowledge"] = payload["knowledge"]
    if "tools" in payload:
        after_snapshot["tools"] = payload["tools"]
    if "model_policy" in payload:
        after_snapshot["model_policy"] = payload["model_policy"]
    if "limits" in payload:
        after_snapshot["limits"] = payload["limits"]
    if "capability_ids" in payload:
        after_snapshot["capability_ids"] = payload["capability_ids"]
    if "risk_level" in payload:
        after_snapshot["risk_level"] = payload["risk_level"]

    changed = _diff_payload(before_snapshot, after_snapshot)
    if not changed:
        return []
    emp.version += 1
    create_version(db, org_id, user_id, emp.id, reason="Cambio de configuración", changed_fields=changed)
    if emp.lifecycle_status in (EmployeeLifecycleStatus.CERTIFIED, EmployeeLifecycleStatus.PUBLISHED, EmployeeLifecycleStatus.ACTIVE):
        emp.lifecycle_status = EmployeeLifecycleStatus.CONFIGURING
        db.commit()
    return changed


def list_versions(db: Session, org_id: str, employee_id: str) -> list[dict[str, Any]]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return []
    rows = (
        db.query(EmployeeVersion)
        .filter(EmployeeVersion.employee_id == emp.id, EmployeeVersion.organization_id == org_id)
        .order_by(EmployeeVersion.version.desc())
        .all()
    )
    return [
        {
            "id": v.id,
            "version": v.version,
            "previous_version": v.previous_version,
            "status": v.status,
            "change_reason": v.change_reason,
            "changed_fields": json.loads(v.changed_fields_json) if v.changed_fields_json else [],
            "created_by_id": v.created_by_id,
            "approved_by_id": v.approved_by_id,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "created_at": v.created_at.isoformat(),
        }
        for v in rows
    ]


def get_version_detail(db: Session, org_id: str, employee_id: str, version_num: int) -> dict[str, Any] | None:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return None
    row = (
        db.query(EmployeeVersion)
        .filter(
            EmployeeVersion.employee_id == emp.id,
            EmployeeVersion.organization_id == org_id,
            EmployeeVersion.version == version_num,
        )
        .first()
    )
    if not row:
        return None
    return {
        "id": row.id,
        "version": row.version,
        "configuration": json.loads(row.configuration_json),
        "change_reason": row.change_reason,
        "changed_fields": json.loads(row.changed_fields_json) if row.changed_fields_json else [],
        "status": row.status,
        "test_summary": json.loads(row.test_summary_json) if row.test_summary_json else None,
    }


def list_test_cases(db: Session, org_id: str, employee_id: str) -> list[dict[str, Any]]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return []
    rows = db.query(EmployeeTestCase).filter(EmployeeTestCase.employee_id == emp.id, EmployeeTestCase.organization_id == org_id).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "test_type": t.test_type,
            "test_category": getattr(t, "test_category", _test_category_for_type(t.test_type)),
            "criterion": getattr(t, "criterion", None),
            "input": json.loads(t.input_json),
            "expected": json.loads(t.expected_json) if t.expected_json else None,
            "is_active": t.is_active,
        }
        for t in rows
    ]


def create_test_case(db: Session, org_id: str, employee_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}
    test_type = payload.get("test_type", TestType.SMOKE)
    category = payload.get("test_category") or _test_category_for_type(test_type)
    row = EmployeeTestCase(
        organization_id=org_id,
        employee_id=emp.id,
        name=payload["name"],
        description=payload.get("description"),
        test_type=test_type,
        test_category=category,
        input_json=json.dumps(payload.get("input", {}), ensure_ascii=False),
        expected_json=json.dumps(payload.get("expected"), ensure_ascii=False) if payload.get("expected") is not None else None,
        criterion=payload.get("criterion"),
        validation_rules_json=json.dumps(payload.get("validation_rules")) if payload.get("validation_rules") else None,
        severity=payload.get("severity", "medium"),
        is_active=payload.get("is_active", True),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "test_category": row.test_category}


def _create_lifecycle_work_plan(db: Session, org_id: str, user_id: str, emp: AIEmployee, objective: str) -> WorkPlan:
    plan = WorkPlan(
        organization_id=org_id,
        user_id=user_id,
        correlation_id=str(uuid.uuid4()),
        request=f"employee-lifecycle:{emp.id}",
        objective=objective,
        status=WorkPlanStatus.WAITING_APPROVAL,
        employee_id=emp.id,
        approval_status=ApprovalStatus.PENDING,
    )
    db.add(plan)
    db.flush()
    return plan


def _pending_factory_approvals(db: Session, org_id: str, employee_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(EmployeeFactoryApproval)
        .filter(
            EmployeeFactoryApproval.organization_id == org_id,
            EmployeeFactoryApproval.employee_id == employee_id,
            EmployeeFactoryApproval.status == "PENDING",
        )
        .all()
    )
    return [{"id": r.id, "kind": r.approval_kind, "target_version": r.target_version} for r in rows]


def requires_approval(emp: AIEmployee, kind: str, user_id: str) -> bool:
    if emp.risk_level in CRITICAL_RISK_LEVELS:
        if kind in (
            EmployeeApprovalKind.PUBLISH,
            EmployeeApprovalKind.ROLLBACK,
            EmployeeApprovalKind.PROVIDER_CHANGE,
            EmployeeApprovalKind.PERMISSION_CHANGE,
            EmployeeApprovalKind.LIMIT_INCREASE,
        ):
            return True
    if emp.created_by_id == user_id and emp.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        if kind in (EmployeeApprovalKind.PUBLISH, EmployeeApprovalKind.CRITICAL_CHANGE):
            return True
    return False


def request_approval(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    *,
    kind: str,
    reason: str,
    target_version: int | None = None,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    existing = (
        db.query(EmployeeFactoryApproval)
        .filter(
            EmployeeFactoryApproval.employee_id == emp.id,
            EmployeeFactoryApproval.approval_kind == kind,
            EmployeeFactoryApproval.status == "PENDING",
        )
        .first()
    )
    if existing:
        return {"error": "Ya existe una aprobación pendiente para esta acción", "approval_id": existing.id}

    plan = _create_lifecycle_work_plan(db, org_id, user_id, emp, f"Aprobación fábrica: {kind}")
    approval = ApprovalRequest(
        organization_id=org_id,
        work_plan_id=plan.id,
        action=f"Empleado IA — {kind}: {emp.name}",
        employee_name=emp.name,
        reason=reason,
        evidence_json=json.dumps({"employee_id": emp.id, "kind": kind, "target_version": target_version}, ensure_ascii=False),
        requested_by=user_id,
    )
    db.add(approval)
    db.flush()

    factory_approval = EmployeeFactoryApproval(
        organization_id=org_id,
        employee_id=emp.id,
        approval_request_id=approval.id,
        approval_kind=kind,
        target_version=target_version or emp.version,
        status="PENDING",
        created_by_id=user_id,
    )
    db.add(factory_approval)
    db.commit()

    write_audit(
        db,
        action="employee.approval_requested",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({"employee_id": emp.id, "kind": kind, "approval_id": approval.id}, ensure_ascii=False),
    )
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_APPROVAL_REQUESTED, emp.id, {"kind": kind})
    return {
        "factory_approval_id": factory_approval.id,
        "approval_request_id": approval.id,
        "work_plan_id": plan.id,
        "status": "PENDING",
        "kind": kind,
    }


def assert_factory_approval_decision_allowed(db: Session, approval: ApprovalRequest, user_id: str) -> str | None:
    """Segregación: el solicitante no puede decidir su propia solicitud de fábrica."""
    factory = (
        db.query(EmployeeFactoryApproval)
        .filter(EmployeeFactoryApproval.approval_request_id == approval.id)
        .first()
    )
    if factory and approval.requested_by == user_id:
        return "El solicitante no puede aprobar su propia solicitud"
    return None


def sync_factory_approval_on_decide(db: Session, approval_request_id: str, decision: str) -> None:
    factory = (
        db.query(EmployeeFactoryApproval)
        .filter(EmployeeFactoryApproval.approval_request_id == approval_request_id)
        .first()
    )
    if not factory:
        return
    factory.status = "APPROVED" if decision == "approve" else "REJECTED"


def list_employee_approvals(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    viewer_id: str | None = None,
) -> list[dict[str, Any]] | None:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return None

    rows = (
        db.query(EmployeeFactoryApproval, ApprovalRequest)
        .join(ApprovalRequest, ApprovalRequest.id == EmployeeFactoryApproval.approval_request_id)
        .filter(
            EmployeeFactoryApproval.organization_id == org_id,
            EmployeeFactoryApproval.employee_id == employee_id,
        )
        .order_by(EmployeeFactoryApproval.created_at.desc())
        .all()
    )

    user_ids: set[str] = set()
    for factory_row, approval_row in rows:
        user_ids.add(approval_row.requested_by)
        user_ids.add(factory_row.created_by_id)
        if approval_row.decided_by:
            user_ids.add(approval_row.decided_by)

    users = (
        {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}
        if user_ids
        else {}
    )

    def _user_name(uid: str) -> str | None:
        user = users.get(uid)
        if not user:
            return None
        return user.full_name or user.username

    result: list[dict[str, Any]] = []
    for factory_row, approval_row in rows:
        can_decide = (
            approval_row.status == "PENDING"
            and viewer_id is not None
            and approval_row.requested_by != viewer_id
        )
        result.append({
            "factory_approval_id": factory_row.id,
            "approval_request_id": approval_row.id,
            "approval_kind": factory_row.approval_kind,
            "status": factory_row.status,
            "approval_status": approval_row.status,
            "reason": approval_row.reason,
            "requested_by_id": approval_row.requested_by,
            "requested_by_name": _user_name(approval_row.requested_by),
            "requester_id": factory_row.created_by_id,
            "requester_name": _user_name(factory_row.created_by_id),
            "decided_by_id": approval_row.decided_by,
            "decided_by_name": _user_name(approval_row.decided_by) if approval_row.decided_by else None,
            "decision_comment": approval_row.decision_comment,
            "target_version": factory_row.target_version,
            "created_at": factory_row.created_at.isoformat(),
            "requested_at": approval_row.created_at.isoformat(),
            "decided_at": approval_row.decided_at.isoformat() if approval_row.decided_at else None,
            "can_decide": can_decide,
            "work_plan_id": approval_row.work_plan_id,
        })
    return result


def decide_employee_approval(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    approval_request_id: str,
    *,
    decision: str,
    comment: str | None = None,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    factory = (
        db.query(EmployeeFactoryApproval)
        .filter(
            EmployeeFactoryApproval.organization_id == org_id,
            EmployeeFactoryApproval.employee_id == employee_id,
            EmployeeFactoryApproval.approval_request_id == approval_request_id,
        )
        .first()
    )
    if not factory:
        return {"error": "Aprobación de fábrica no encontrada para este empleado"}

    from app.services.coordinator import decide_approval

    result = decide_approval(
        db,
        approval_id=approval_request_id,
        organization_id=org_id,
        user_id=user_id,
        decision=decision,
        comment=comment,
    )
    if result.get("error"):
        return result

    db.refresh(factory)
    write_audit(
        db,
        action="employee.approval_decided",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({
            "employee_id": employee_id,
            "approval_request_id": approval_request_id,
            "decision": decision,
            "kind": factory.approval_kind,
        }, ensure_ascii=False),
    )
    return {
        "factory_approval_id": factory.id,
        "approval_request_id": approval_request_id,
        "status": factory.status,
        "approval_status": result.get("status", factory.status),
        "kind": factory.approval_kind,
        "decision": decision,
    }


def check_approval_for_action(db: Session, org_id: str, employee_id: str, kind: str) -> bool:
    approved = (
        db.query(EmployeeFactoryApproval)
        .filter(
            EmployeeFactoryApproval.organization_id == org_id,
            EmployeeFactoryApproval.employee_id == employee_id,
            EmployeeFactoryApproval.approval_kind == kind,
            EmployeeFactoryApproval.status == "APPROVED",
        )
        .order_by(EmployeeFactoryApproval.created_at.desc())
        .first()
    )
    return approved is not None


def publish_with_guards(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    validation = validate_configuration(db, org_id, employee_id)
    if not validation["valid"]:
        return {"error": "Configuración incompleta", "validation": validation}

    if emp.lifecycle_status != EmployeeLifecycleStatus.CERTIFIED:
        return {"error": "Solo empleados CERTIFIED pueden publicarse. Ejecute pruebas y certificación primero."}

    if requires_approval(emp, EmployeeApprovalKind.PUBLISH, user_id):
        if not check_approval_for_action(db, org_id, employee_id, EmployeeApprovalKind.PUBLISH):
            return {
                "error": "Requiere aprobación humana para publicar",
                "requires_approval": True,
                "approval_kind": EmployeeApprovalKind.PUBLISH,
            }

    snapshot = agent_factory._employee_config_snapshot(db, emp)
    test_summary = {
        "passed": db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "PASSED").count(),
        "failed": db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "FAILED").count(),
    }
    version_row = EmployeeVersion(
        organization_id=org_id,
        employee_id=emp.id,
        version=emp.version,
        previous_version=emp.version - 1 if emp.version > 1 else None,
        configuration_json=json.dumps(snapshot, ensure_ascii=False),
        change_reason="Publicación",
        status="PUBLISHED",
        test_summary_json=json.dumps(test_summary, ensure_ascii=False),
        created_by_id=user_id,
        published_at=_utcnow(),
    )
    db.add(version_row)
    emp.lifecycle_status = EmployeeLifecycleStatus.PUBLISHED
    emp.published_at = _utcnow()
    db.commit()

    write_audit(
        db,
        action="employee.published",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({"employee_id": emp.id, "version": emp.version, "tests": test_summary}, ensure_ascii=False),
    )
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_PUBLISHED, emp.id, {"version": emp.version})
    detail = agent_factory.get_employee_detail(db, org_id, emp.id) or {}
    detail["validation"] = validation
    detail["published_version_id"] = version_row.id
    return detail


def rollback_to_version(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    target_version: int,
    *,
    reason: str,
    force: bool = False,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    version_row = (
        db.query(EmployeeVersion)
        .filter(
            EmployeeVersion.employee_id == emp.id,
            EmployeeVersion.organization_id == org_id,
            EmployeeVersion.version == target_version,
            EmployeeVersion.status.in_(("PUBLISHED", "APPROVED", "DRAFT")),
        )
        .order_by(EmployeeVersion.created_at.desc())
        .first()
    )
    if not version_row:
        return {"error": f"Versión {target_version} no encontrada o no aprobada"}

    if emp.risk_level in CRITICAL_RISK_LEVELS and not force:
        if not check_approval_for_action(db, org_id, employee_id, EmployeeApprovalKind.ROLLBACK):
            return {
                "error": "Rollback crítico requiere aprobación humana",
                "requires_approval": True,
                "approval_kind": EmployeeApprovalKind.ROLLBACK,
            }

    config = json.loads(version_row.configuration_json)
    emp_data = config.get("employee", {})
    for field in ("name", "role", "objective", "specialty", "risk_level", "maturity", "shadow_mode"):
        if field in emp_data and hasattr(emp, field):
            setattr(emp, field, emp_data[field])

    instructions = config.get("instructions", {})
    ins_row = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
    if ins_row:
        ins_row.system_purpose = instructions.get("system_purpose")
        ins_row.role_text = instructions.get("role")
        ins_row.objective_text = instructions.get("objective")

    emp.version = target_version
    emp.lifecycle_status = EmployeeLifecycleStatus.CONFIGURING
    emp.updated_at = _utcnow()
    db.commit()

    write_audit(
        db,
        action="employee.rollback",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({"employee_id": emp.id, "target_version": target_version, "reason": reason}, ensure_ascii=False),
    )
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_ROLLBACK, emp.id, {"target_version": target_version})
    return agent_factory.get_employee_detail(db, org_id, emp.id) or {}


def train_employee(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    *,
    training_type: str,
    reason: str,
    source: str | None = None,
    config_delta: dict[str, Any] | None = None,
    approved_by_id: str | None = None,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    version_before = emp.version
    last_test = (
        db.query(EmployeeTestRun)
        .filter(EmployeeTestRun.employee_id == emp.id)
        .order_by(EmployeeTestRun.created_at.desc())
        .first()
    )

    if config_delta:
        agent_factory.update_employee(db, org_id, user_id, employee_id, config_delta)

    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    version_after = emp.version
    if version_after == version_before:
        emp.version += 1
        version_after = emp.version

    create_version(db, org_id, user_id, employee_id, reason=f"Capacitación: {reason}", changed_fields=list((config_delta or {}).keys()), status="TRAINED")

    test_after = agent_factory.run_employee_tests(db, org_id, user_id, employee_id)
    test_after_id = None
    if test_after.get("results"):
        last_run = (
            db.query(EmployeeTestRun)
            .filter(EmployeeTestRun.employee_id == emp.id)
            .order_by(EmployeeTestRun.created_at.desc())
            .first()
        )
        test_after_id = last_run.id if last_run else None

    training = EmployeeTraining(
        organization_id=org_id,
        employee_id=emp.id,
        training_type=training_type,
        reason=reason,
        source=source,
        version_before=version_before,
        version_after=version_after,
        config_delta_json=json.dumps(config_delta or {}, ensure_ascii=False),
        test_before_id=last_test.id if last_test else None,
        test_after_id=test_after_id,
        approved_by_id=approved_by_id,
        created_by_id=user_id,
    )
    db.add(training)
    emp.last_training_at = _utcnow()
    db.commit()

    write_audit(
        db,
        action="employee.trained",
        organization_id=org_id,
        user_id=user_id,
        detail=json.dumps({"employee_id": emp.id, "type": training_type, "reason": reason}, ensure_ascii=False),
    )
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_TRAINED, emp.id, {"training_type": training_type})
    return {
        "training_id": training.id,
        "version_before": version_before,
        "version_after": version_after,
        "test_result": test_after,
    }


def retire_employee(db: Session, org_id: str, user_id: str, employee_id: str, *, reason: str) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}
    emp.lifecycle_status = EmployeeLifecycleStatus.RETIRED
    emp.status = "FINALIZADO"
    emp.is_active = False
    db.commit()
    write_audit(db, action="employee.retired", organization_id=org_id, user_id=user_id, detail=json.dumps({"reason": reason}))
    agent_factory._emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_RETIRED, emp.id, {"reason": reason})
    return agent_factory.get_employee_detail(db, org_id, emp.id) or {}


def health_snapshot(db: Session, org_id: str, employee_id: str) -> dict[str, Any] | None:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return None
    last_test = (
        db.query(EmployeeTestRun)
        .filter(EmployeeTestRun.employee_id == emp.id)
        .order_by(EmployeeTestRun.created_at.desc())
        .first()
    )
    last_training = (
        db.query(EmployeeTraining)
        .filter(EmployeeTraining.employee_id == emp.id)
        .order_by(EmployeeTraining.created_at.desc())
        .first()
    )
    active_version = (
        db.query(EmployeeVersion)
        .filter(EmployeeVersion.employee_id == emp.id, EmployeeVersion.status == "PUBLISHED")
        .order_by(EmployeeVersion.version.desc())
        .first()
    )
    return {
        "employee_id": emp.id,
        "active_version": active_version.version if active_version else emp.version,
        "lifecycle_status": emp.lifecycle_status,
        "lifecycle_phase": lifecycle_phase(emp.lifecycle_status),
        "last_publication": emp.published_at.isoformat() if emp.published_at else None,
        "last_test_at": last_test.created_at.isoformat() if last_test else None,
        "last_test_result": last_test.status if last_test else None,
        "last_training_at": emp.last_training_at.isoformat() if emp.last_training_at else None,
        "last_training_type": last_training.training_type if last_training else None,
    }


def auditor_contract() -> dict[str, Any]:
    return {
        "module": "employee_factory",
        "version": "1.0",
        "operations": [
            {"op": "capacitar", "method": "POST", "path": "/api/agent-factory/employees/{id}/train"},
            {"op": "crear_version", "method": "POST", "path": "/api/agent-factory/employees/{id}/versions"},
            {"op": "probar", "method": "POST", "path": "/api/agent-factory/employees/{id}/test"},
            {"op": "aprobar", "method": "POST", "path": "/api/agent-factory/employees/{id}/request-approval"},
            {"op": "publicar", "method": "POST", "path": "/api/agent-factory/employees/{id}/publish"},
            {"op": "rollback", "method": "POST", "path": "/api/agent-factory/employees/{id}/rollback"},
            {"op": "pausar", "method": "POST", "path": "/api/agent-factory/employees/{id}/pause"},
            {"op": "retirar", "method": "POST", "path": "/api/agent-factory/employees/{id}/retire"},
            {"op": "inventario", "method": "GET", "path": "/api/agent-factory/employees/{id}/inventory"},
            {"op": "salud", "method": "GET", "path": "/api/agent-factory/employees/{id}/health"},
        ],
        "note": "El Auditor de Empleados IA consumirá estas operaciones sin motor propio.",
    }
