"""Puente Auditor → Mi Trabajo → Fábrica — sin ejecución automática."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.employee_audit_models import (
    EmployeeAuditFinding,
    EmployeeImprovementTrace,
    OUTCOME_CLASSIFICATIONS,
)
from app.models import User
from app.orchestration_models import AIEmployee
from app.permissions import check_permission, user_permissions
from app.services import agent_factory, employee_lifecycle_service
from app.services.employee_audit_metrics import collect_employee_metrics
from app.services.employee_audit_service import execute_audit

HIGH_IMPACT_OPS = frozenset({"publicar", "rollback", "retirar"})

RECOMMENDATION_NAVIGATION: dict[str, dict[str, Any]] = {
    "CAPACITAR": {
        "factory_op": "capacitar",
        "permission": "employee.train",
        "tab": "Resumen",
        "label": "Capacitar",
    },
    "ACTUALIZAR_CONOCIMIENTO": {
        "factory_op": "actualizar_conocimiento",
        "permission": "employee.edit",
        "tab": "Conocimiento",
        "label": "Actualizar conocimiento",
    },
    "MEJORAR_INSTRUCCIONES": {
        "factory_op": "crear_version",
        "permission": "employee.edit",
        "tab": "Configuración",
        "label": "Mejorar instrucciones",
    },
    "AGREGAR_HERRAMIENTA": {
        "factory_op": "configurar",
        "permission": "employee.edit",
        "tab": "Herramientas",
        "label": "Agregar herramienta",
    },
    "CAMBIAR_HERRAMIENTA": {
        "factory_op": "configurar",
        "permission": "employee.edit",
        "tab": "Herramientas",
        "label": "Cambiar herramienta",
    },
    "CAMBIAR_MODELO": {
        "factory_op": "configurar",
        "permission": "employee.edit",
        "tab": "Modelo",
        "label": "Cambiar modelo",
    },
    "CAMBIAR_PROVEEDOR": {
        "factory_op": "configurar",
        "permission": "employee.edit",
        "tab": "Modelo",
        "label": "Cambiar proveedor",
    },
    "AJUSTAR_AUTOMATIZACION": {
        "factory_op": "configurar",
        "permission": "employee.edit",
        "tab": "Automatizaciones",
        "label": "Ajustar automatización",
    },
    "REDISEÑAR_EMPLEADO": {
        "factory_op": "crear_version",
        "permission": "employee.edit",
        "tab": "Versiones",
        "label": "Rediseñar empleado",
    },
    "SOLICITAR_REVISION_HUMANA": {
        "factory_op": "solicitar_aprobacion",
        "permission": "employee.edit",
        "tab": "Aprobación",
        "label": "Solicitar aprobación",
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _json_loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _get_finding(db: Session, org_id: str, finding_id: str) -> EmployeeAuditFinding | None:
    return (
        db.query(EmployeeAuditFinding)
        .filter(
            EmployeeAuditFinding.id == finding_id,
            EmployeeAuditFinding.organization_id == org_id,
        )
        .first()
    )


def _get_employee(db: Session, org_id: str, employee_id: str) -> AIEmployee | None:
    return (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )


def _metrics_snapshot(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    try:
        return collect_employee_metrics(db, org_id, employee_id)
    except Exception:
        return {}


def resolve_factory_navigation(recommended_action: str | None) -> dict[str, Any] | None:
    if not recommended_action:
        return None
    return RECOMMENDATION_NAVIGATION.get(recommended_action)


def build_factory_href(
    employee_id: str,
    *,
    tab: str,
    finding_id: str,
    audit_run_id: str | None,
    correlation_id: str,
    trace_id: str | None = None,
) -> str:
    params = [
        f"tab={tab}",
        f"finding_id={finding_id}",
        f"correlation_id={correlation_id}",
    ]
    if audit_run_id:
        params.append(f"audit_run_id={audit_run_id}")
    if trace_id:
        params.append(f"trace_id={trace_id}")
    return f"/empleados/{employee_id}?{'&'.join(params)}"


def get_finding_factory_action(db: Session, org_id: str, user: User, finding_id: str) -> dict[str, Any]:
    finding = _get_finding(db, org_id, finding_id)
    if not finding:
        return {"error": "Hallazgo no encontrado"}
    nav = resolve_factory_navigation(finding.recommended_action)
    perms = user_permissions(user, db)
    can_execute = bool(nav and nav["permission"] in perms)
    return {
        "finding_id": finding.id,
        "employee_id": finding.employee_id,
        "audit_run_id": finding.run_id,
        "correlation_id": finding.correlation_id,
        "recommendation": finding.recommended_action,
        "semantic_kind": finding.semantic_kind,
        "navigation": nav,
        "can_execute": can_execute,
        "auto_execution_blocked": True,
        "factory_contract": employee_lifecycle_service.auditor_contract(),
    }


def iniciar_mejora(
    db: Session,
    org_id: str,
    user: User,
    finding_id: str,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    finding = _get_finding(db, org_id, finding_id)
    if not finding:
        return {"error": "Hallazgo no encontrado"}
    if finding.status != "ABIERTO":
        return {"error": "El hallazgo ya no está abierto"}

    emp = _get_employee(db, org_id, finding.employee_id)
    if not emp:
        return {"error": "Empleado no encontrado"}

    nav = resolve_factory_navigation(finding.recommended_action)
    if not nav:
        return {"error": "Recomendación sin acción de fábrica compatible"}

    open_trace = (
        db.query(EmployeeImprovementTrace)
        .filter(
            EmployeeImprovementTrace.organization_id == org_id,
            EmployeeImprovementTrace.finding_id == finding_id,
            EmployeeImprovementTrace.status.in_(("PENDING", "IN_PROGRESS")),
        )
        .first()
    )
    if open_trace:
        return {
            "trace_id": open_trace.id,
            "status": open_trace.status,
            "href": build_factory_href(
                finding.employee_id,
                tab=nav["tab"],
                finding_id=finding.id,
                audit_run_id=finding.run_id,
                correlation_id=finding.correlation_id,
                trace_id=open_trace.id,
            ),
            "idempotent": True,
        }

    key = idempotency_key or f"improvement:{finding_id}:{user.id}:{nav['factory_op']}"
    existing = (
        db.query(EmployeeImprovementTrace)
        .filter(
            EmployeeImprovementTrace.organization_id == org_id,
            EmployeeImprovementTrace.idempotency_key == key,
        )
        .first()
    )
    if existing:
        return {
            "trace_id": existing.id,
            "status": existing.status,
            "href": build_factory_href(
                finding.employee_id,
                tab=nav["tab"],
                finding_id=finding.id,
                audit_run_id=finding.run_id,
                correlation_id=finding.correlation_id,
                trace_id=existing.id,
            ),
            "idempotent": True,
        }

    before = _metrics_snapshot(db, org_id, finding.employee_id)
    trace = EmployeeImprovementTrace(
        organization_id=org_id,
        employee_id=finding.employee_id,
        audit_run_id=finding.run_id,
        finding_id=finding.id,
        correlation_id=finding.correlation_id,
        recommendation=finding.recommended_action or nav["factory_op"],
        work_item_ref=f"auditor_empleado:{finding.id}",
        status="PENDING",
        outcome_classification="PENDIENTE_VALIDACION",
        requested_by_id=user.id,
        factory_operation=nav["factory_op"],
        before_snapshot_json=_json_dumps(before),
        idempotency_key=key,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)

    write_audit(
        db,
        action="auditor.improvement_initiated",
        organization_id=org_id,
        user_id=user.id,
        detail=_json_dumps({
            "trace_id": trace.id,
            "finding_id": finding.id,
            "employee_id": finding.employee_id,
            "correlation_id": finding.correlation_id,
        }),
    )

    return {
        "trace_id": trace.id,
        "status": trace.status,
        "required_permission": nav["permission"],
        "factory_operation": nav["factory_op"],
        "tab": nav["tab"],
        "href": build_factory_href(
            finding.employee_id,
            tab=nav["tab"],
            finding_id=finding.id,
            audit_run_id=finding.run_id,
            correlation_id=finding.correlation_id,
            trace_id=trace.id,
        ),
        "auto_execution_blocked": True,
    }


def _require_factory_permission(user: User, permission: str, db: Session) -> str | None:
    try:
        check_permission(user, permission, db)
        return None
    except Exception:
        return f"Permiso requerido: {permission}"


def ejecutar_operacion_fabrica(
    db: Session,
    org_id: str,
    user: User,
    trace_id: str,
    *,
    operation: str | None = None,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    trace = (
        db.query(EmployeeImprovementTrace)
        .filter(EmployeeImprovementTrace.id == trace_id, EmployeeImprovementTrace.organization_id == org_id)
        .first()
    )
    if not trace:
        return {"error": "Trazabilidad no encontrada"}
    if trace.status == "COMPLETED":
        return {
            "trace_id": trace.id,
            "status": trace.status,
            "outcome_classification": trace.outcome_classification,
            "idempotent": True,
            "factory_result_ref": trace.factory_result_ref,
        }
    if trace.status == "IN_PROGRESS" and trace.executed_by_id and trace.executed_by_id != user.id:
        return {"error": "Otra acción incompatible está en curso sobre este hallazgo"}

    op = operation or trace.factory_operation
    if not op:
        return {"error": "Operación de fábrica no especificada"}

    nav = resolve_factory_navigation(trace.recommendation) or {}
    permission = nav.get("permission")
    if permission:
        denied = _require_factory_permission(user, permission, db)
        if denied:
            return {"error": denied}

    if op in HIGH_IMPACT_OPS:
        high_perm = {
            "publicar": "employee.publish",
            "rollback": "employee.rollback",
            "retirar": "employee.retire",
        }.get(op)
        if high_perm:
            denied = _require_factory_permission(user, high_perm, db)
            if denied:
                return {"error": denied}

    exec_key = idempotency_key or f"exec:{trace.id}:{op}"
    evidence = _json_loads(trace.evidence_json) or {}
    if evidence.get("exec_keys", {}).get(exec_key):
        return {
            "trace_id": trace.id,
            "status": trace.status,
            "idempotent": True,
            "factory_result_ref": trace.factory_result_ref,
        }

    trace.status = "IN_PROGRESS"
    trace.executed_by_id = user.id
    trace.updated_at = _utcnow()
    db.commit()

    body = payload or {}
    result: dict[str, Any]
    employee_id = trace.employee_id

    try:
        if op == "capacitar":
            result = employee_lifecycle_service.train_employee(
                db,
                org_id,
                user.id,
                employee_id,
                training_type=body.get("training_type", "INSTRUCTIONS"),
                reason=body.get("reason", f"Capacitación por hallazgo {trace.finding_id}"),
                source=body.get("source", "auditor-mejora"),
                config_delta=body.get("config_delta"),
            )
            if result.get("error"):
                raise ValueError(result["error"])
            trace.factory_result_ref = result.get("training_id")
        elif op == "probar":
            result = agent_factory.run_employee_tests(db, org_id, user.id, employee_id)
            if result.get("error"):
                raise ValueError(result["error"])
            from app.orchestration_models import EmployeeTestRun

            last_run = (
                db.query(EmployeeTestRun)
                .filter(EmployeeTestRun.employee_id == employee_id)
                .order_by(EmployeeTestRun.created_at.desc())
                .first()
            )
            if last_run:
                trace.test_run_id = last_run.id
                trace.factory_result_ref = last_run.id
        elif op == "solicitar_aprobacion":
            result = employee_lifecycle_service.request_approval(
                db,
                org_id,
                user.id,
                employee_id,
                kind=body.get("kind", "PUBLISH"),
                reason=body.get("reason", f"Aprobación por hallazgo {trace.finding_id}"),
                target_version=body.get("target_version"),
            )
            if result.get("error"):
                raise ValueError(result["error"])
            trace.approval_id = result.get("approval_request_id")
            trace.factory_result_ref = trace.approval_id
        elif op == "publicar":
            result = employee_lifecycle_service.publish_with_guards(db, org_id, user.id, employee_id)
            if result.get("error"):
                raise ValueError(result["error"])
            trace.version_id = result.get("published_version_id")
            trace.factory_result_ref = trace.version_id
        elif op == "rollback":
            result = employee_lifecycle_service.rollback_to_version(
                db,
                org_id,
                user.id,
                employee_id,
                body.get("target_version"),
                reason=body.get("reason", f"Rollback por hallazgo {trace.finding_id}"),
                force=bool(body.get("force")),
            )
            if result.get("error"):
                raise ValueError(result["error"])
            trace.factory_result_ref = str(body.get("target_version"))
        elif op == "pausar":
            result = agent_factory.pause_employee(db, org_id, user.id, employee_id)
            if result.get("error"):
                raise ValueError(result["error"])
        elif op == "retirar":
            result = employee_lifecycle_service.retire_employee(
                db,
                org_id,
                user.id,
                employee_id,
                reason=body.get("reason", f"Retiro por hallazgo {trace.finding_id}"),
            )
            if result.get("error"):
                raise ValueError(result["error"])
        elif op in ("crear_version", "configurar", "actualizar_conocimiento"):
            if body.get("config_delta"):
                result = agent_factory.update_employee(db, org_id, user.id, employee_id, body["config_delta"])
                if result.get("error"):
                    raise ValueError(result["error"])
            else:
                result = {"status": "NAVIGATION_ONLY", "message": "Configurar en ficha de empleado"}
        else:
            return {"error": f"Operación no soportada: {op}"}
    except ValueError as exc:
        trace.status = "FAILED"
        trace.evidence_json = _json_dumps({**evidence, "error": str(exc)})
        trace.updated_at = _utcnow()
        db.commit()
        return {"error": str(exc), "trace_id": trace.id}

    after = _metrics_snapshot(db, org_id, employee_id)
    trace.after_snapshot_json = _json_dumps(after)
    trace.outcome_classification = classify_outcome(
        _json_loads(trace.before_snapshot_json) or {},
        after,
    )
    trace.status = "COMPLETED"
    trace.completed_at = _utcnow()
    trace.updated_at = _utcnow()
    exec_keys = evidence.get("exec_keys", {})
    exec_keys[exec_key] = _utcnow().isoformat()
    trace.evidence_json = _json_dumps({**evidence, "exec_keys": exec_keys, "result": result})

    finding = _get_finding(db, org_id, trace.finding_id)
    if finding and finding.status == "ABIERTO" and op in ("capacitar", "probar", "publicar"):
        finding.status = "CERRADO"
        finding.evidence_json = _json_dumps({
            **_json_loads(finding.evidence_json) or {},
            "closed_by_trace": trace.id,
            "factory_operation": op,
        })

    db.commit()
    write_audit(
        db,
        action="auditor.improvement_executed",
        organization_id=org_id,
        user_id=user.id,
        detail=_json_dumps({
            "trace_id": trace.id,
            "operation": op,
            "outcome": trace.outcome_classification,
        }),
    )
    return {
        "trace_id": trace.id,
        "status": trace.status,
        "outcome_classification": trace.outcome_classification,
        "factory_operation": op,
        "factory_result_ref": trace.factory_result_ref,
        "result": result,
        "correlation_id": trace.correlation_id,
    }


def classify_outcome(before: dict[str, Any], after: dict[str, Any]) -> str:
    if not before or not after:
        return "NO_DETERMINADO"
    improved_metrics = 0
    worsened_metrics = 0
    comparable = 0
    for key in ("success_rate", "test_pass_rate", "health_score"):
        b_val = before.get(key)
        a_val = after.get(key)
        if b_val is None or a_val is None:
            continue
        try:
            b_f, a_f = float(b_val), float(a_val)
        except (TypeError, ValueError):
            continue
        comparable += 1
        if a_f > b_f:
            improved_metrics += 1
        elif a_f < b_f:
            worsened_metrics += 1
    if comparable == 0:
        return "PENDIENTE_VALIDACION"
    if improved_metrics > worsened_metrics:
        return "MEJORADO"
    if worsened_metrics > improved_metrics:
        return "EMPEORADO"
    return "SIN_CAMBIO"


def solicitar_reauditoria(
    db: Session,
    org_id: str,
    user: User,
    trace_id: str,
    *,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    trace = (
        db.query(EmployeeImprovementTrace)
        .filter(EmployeeImprovementTrace.id == trace_id, EmployeeImprovementTrace.organization_id == org_id)
        .first()
    )
    if not trace:
        return {"error": "Trazabilidad no encontrada"}

    denied = _require_factory_permission(user, "auditor_empleados.execute", db)
    if denied:
        return {"error": denied}

    key = idempotency_key or f"reaudit:{trace.id}"
    evidence = _json_loads(trace.evidence_json) or {}
    if evidence.get("reaudit_key") == key:
        return evidence.get("reaudit_result", {"idempotent": True})

    result = execute_audit(
        db,
        user,
        organization_id=org_id,
        employee_id=trace.employee_id,
        trigger_type="MANUAL",
        trigger_ref=f"reaudit_trace:{trace.id}",
    )
    after = _metrics_snapshot(db, org_id, trace.employee_id)
    comparison = {
        "before": _json_loads(trace.before_snapshot_json),
        "after_action": _json_loads(trace.after_snapshot_json),
        "after_reaudit": after,
        "outcome_prior": trace.outcome_classification,
        "reaudit_run_id": result.get("id"),
        "semantic_note": "Comparación observacional; no implica causalidad automática",
    }
    trace.evidence_json = _json_dumps({
        **evidence,
        "reaudit_key": key,
        "reaudit_result": result,
        "comparison": comparison,
    })
    trace.updated_at = _utcnow()
    db.commit()
    return {
        "trace_id": trace.id,
        "reaudit": result,
        "comparison": comparison,
        "correlation_id": trace.correlation_id,
    }


def get_traceability(db: Session, org_id: str, trace_id: str) -> dict[str, Any] | None:
    trace = (
        db.query(EmployeeImprovementTrace)
        .filter(EmployeeImprovementTrace.id == trace_id, EmployeeImprovementTrace.organization_id == org_id)
        .first()
    )
    if not trace:
        return None
    finding = _get_finding(db, org_id, trace.finding_id)
    return {
        "trace_id": trace.id,
        "employee_id": trace.employee_id,
        "audit_run_id": trace.audit_run_id,
        "finding_id": trace.finding_id,
        "recommendation": trace.recommendation,
        "work_item_ref": trace.work_item_ref,
        "decision": {
            "requested_by_id": trace.requested_by_id,
            "executed_by_id": trace.executed_by_id,
        },
        "factory_operation": trace.factory_operation,
        "factory_result_ref": trace.factory_result_ref,
        "version_id": trace.version_id,
        "approval_id": trace.approval_id,
        "test_run_id": trace.test_run_id,
        "correlation_id": trace.correlation_id,
        "status": trace.status,
        "outcome_classification": trace.outcome_classification,
        "before_snapshot": _json_loads(trace.before_snapshot_json),
        "after_snapshot": _json_loads(trace.after_snapshot_json),
        "evidence": _json_loads(trace.evidence_json),
        "finding_status": finding.status if finding else None,
        "finding_semantic_kind": finding.semantic_kind if finding else None,
        "created_at": trace.created_at.isoformat() if trace.created_at else None,
        "completed_at": trace.completed_at.isoformat() if trace.completed_at else None,
    }


def portable_control_center_contract() -> dict[str, Any]:
    return {
        "module": "auditor_factory_cycle",
        "version": "1.0",
        "widgets": [
            "hallazgos_abiertos",
            "acciones_pendientes",
            "acciones_completadas",
            "mejoras_verificadas",
            "sin_cambio",
            "empeoramientos",
        ],
        "note": "Contrato portable para Centro de Control — sin implementar dashboard aquí.",
    }
