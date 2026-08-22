import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.audit import write_audit
from app.enums import (
    CertificationResult,
    EmployeeEventType,
    EmployeeLifecycleStatus,
    EmployeeMaturity,
    RiskLevel,
    ToolPermission,
)
from app.events.bus import EventMessage, publish
from app.orchestration_models import (
    AIEmployee,
    Capability,
    EmployeeCapability,
    EmployeeCertification,
    EmployeeInstructions,
    EmployeeKnowledgeSource,
    EmployeeLimits,
    EmployeeModelPolicy,
    EmployeeTemplate,
    EmployeeTestCase,
    EmployeeTestRun,
    EmployeeToolGrant,
    EmployeeVersion,
    FinOpsRecord,
    Tool,
)
from app.tools import docint, rips


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug_code(name: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _employee_config_snapshot(db: Session, employee: AIEmployee) -> dict[str, Any]:
    caps = (
        db.query(Capability)
        .join(EmployeeCapability, EmployeeCapability.capability_id == Capability.id)
        .filter(EmployeeCapability.employee_id == employee.id)
        .all()
    )
    tools = (
        db.query(Tool, EmployeeToolGrant)
        .join(EmployeeToolGrant, EmployeeToolGrant.tool_id == Tool.id)
        .filter(EmployeeToolGrant.employee_id == employee.id)
        .all()
    )
    knowledge = db.query(EmployeeKnowledgeSource).filter(EmployeeKnowledgeSource.employee_id == employee.id).all()
    policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == employee.id).first()
    limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == employee.id).first()
    instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == employee.id).first()
    return {
        "employee": {
            "code": employee.code,
            "name": employee.name,
            "role": employee.role,
            "objective": employee.objective,
            "specialty": employee.specialty,
            "risk_level": employee.risk_level,
            "maturity": employee.maturity,
            "shadow_mode": employee.shadow_mode,
        },
        "capabilities": [{"code": c.code, "name": c.name} for c in caps],
        "tools": [{"code": t.code, "permission": g.permission} for t, g in tools],
        "knowledge": [{"type": k.source_type, "name": k.name} for k in knowledge],
        "model_policy": {
            "provider": policy.preferred_provider if policy else employee.model_provider,
            "model": policy.preferred_model if policy else employee.model_name,
        },
        "limits": {
            "max_concurrent_tasks": limits.max_concurrent_tasks if limits else 3,
            "timeout_seconds": limits.timeout_seconds if limits else 120,
        },
        "instructions": {
            "system_purpose": instructions.system_purpose if instructions else None,
            "role": instructions.role_text if instructions else employee.role,
            "objective": instructions.objective_text if instructions else employee.objective,
        },
    }


def _emit(db: Session, org_id: str, user_id: str, event_type: str, employee_id: str, payload: dict | None = None) -> None:
    publish(
        EventMessage(
            event_type=event_type,
            organization_id=org_id,
            user_id=user_id,
            payload={"employee_id": employee_id, **(payload or {})},
        ),
        db,
    )
    write_audit(db, action=event_type, organization_id=org_id, user_id=user_id, detail=json.dumps(payload or {})[:2000])


def list_employees(
    db: Session,
    org_id: str,
    *,
    status: str | None = None,
    specialty: str | None = None,
    capability: str | None = None,
) -> list[dict[str, Any]]:
    q = db.query(AIEmployee).filter(AIEmployee.organization_id == org_id)
    if status:
        q = q.filter(AIEmployee.lifecycle_status == status)
    if specialty:
        q = q.filter(AIEmployee.specialty.ilike(f"%{specialty}%"))
    employees = q.order_by(AIEmployee.name).all()
    result = []
    for emp in employees:
        caps = (
            db.query(Capability)
            .join(EmployeeCapability, EmployeeCapability.capability_id == Capability.id)
            .filter(EmployeeCapability.employee_id == emp.id)
            .all()
        )
        if capability and not any(c.code == capability for c in caps):
            continue
        cert = (
            db.query(EmployeeCertification)
            .filter(EmployeeCertification.employee_id == emp.id)
            .order_by(EmployeeCertification.created_at.desc())
            .first()
        )
        finops = (
            db.query(FinOpsRecord)
            .filter(FinOpsRecord.organization_id == org_id)
            .all()
        )
        result.append({
            "id": emp.id,
            "code": emp.code,
            "name": emp.name,
            "specialty": emp.specialty,
            "lifecycle_status": emp.lifecycle_status,
            "maturity": emp.maturity,
            "risk_level": emp.risk_level,
            "status": emp.status,
            "version": emp.version,
            "capabilities": [c.code for c in caps],
            "model_provider": emp.model_provider,
            "model_name": emp.model_name,
            "last_certification": cert.result if cert else None,
            "last_certification_at": cert.created_at.isoformat() if cert else None,
            "shadow_mode": emp.shadow_mode,
            "created_at": emp.created_at.isoformat(),
            "updated_at": emp.updated_at.isoformat() if emp.updated_at else None,
        })
    return result


def get_employee_detail(db: Session, org_id: str, employee_id: str) -> dict[str, Any] | None:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return None
    base = list_employees(db, org_id)[0] if False else None
    items = [e for e in list_employees(db, org_id) if e["id"] == employee_id]
    detail = items[0] if items else {}
    detail.update(_employee_config_snapshot(db, emp))
    detail["instructions_full"] = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
    detail["versions"] = [
        {"id": v.id, "version": v.version, "status": v.status, "created_at": v.created_at.isoformat()}
        for v in db.query(EmployeeVersion).filter(EmployeeVersion.employee_id == emp.id).order_by(EmployeeVersion.version.desc()).all()
    ]
    detail["test_cases"] = [
        {"id": t.id, "name": t.name, "test_type": t.test_type, "is_active": t.is_active}
        for t in db.query(EmployeeTestCase).filter(EmployeeTestCase.employee_id == emp.id).all()
    ]
    detail["certifications"] = [
        {"id": c.id, "result": c.result, "score": c.score, "version": c.version, "created_at": c.created_at.isoformat()}
        for c in db.query(EmployeeCertification).filter(EmployeeCertification.employee_id == emp.id).order_by(EmployeeCertification.created_at.desc()).all()
    ]
    return detail


def create_employee(
    db: Session,
    org_id: str,
    user_id: str,
    *,
    name: str,
    specialty: str,
    role: str | None = None,
    objective: str | None = None,
    template_code: str | None = None,
) -> dict[str, Any]:
    code = _slug_code(name)
    emp = AIEmployee(
        organization_id=org_id,
        code=code,
        name=name,
        specialty=specialty,
        role=role,
        objective=objective,
        lifecycle_status=EmployeeLifecycleStatus.DRAFT,
        maturity=EmployeeMaturity.DRAFT,
        created_by_id=user_id,
        owner_id=user_id,
    )
    db.add(emp)
    db.flush()

    db.add(EmployeeLimits(employee_id=emp.id))
    db.add(EmployeeInstructions(employee_id=emp.id, role_text=role, objective_text=objective))
    db.add(EmployeeModelPolicy(employee_id=emp.id, preferred_provider="rule-engine"))

    if template_code:
        _apply_template(db, emp, org_id, template_code)

    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_CREATED, emp.id, {"code": code})
    return get_employee_detail(db, org_id, emp.id) or {}


def _apply_template(db: Session, emp: AIEmployee, org_id: str, template_code: str) -> None:
    tpl = db.query(EmployeeTemplate).filter(EmployeeTemplate.code == template_code, EmployeeTemplate.is_active.is_(True)).first()
    if not tpl:
        return
    data = json.loads(tpl.template_json)
    emp.role = data.get("role", emp.role)
    emp.objective = data.get("objective", emp.objective)
    emp.risk_level = data.get("risk_level", emp.risk_level)
    emp.model_provider = data.get("model_provider")
    emp.model_name = data.get("model_name")
    for cap_code in data.get("capabilities", []):
        cap = db.query(Capability).filter(Capability.organization_id == org_id, Capability.code == cap_code).first()
        if cap and not db.query(EmployeeCapability).filter(EmployeeCapability.employee_id == emp.id, EmployeeCapability.capability_id == cap.id).first():
            db.add(EmployeeCapability(employee_id=emp.id, capability_id=cap.id))
    for tool_code in data.get("tools", []):
        tool = db.query(Tool).filter(Tool.organization_id == org_id, Tool.code == tool_code).first()
        if tool and not db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id, EmployeeToolGrant.tool_id == tool.id).first():
            perm = data.get("tool_permissions", {}).get(tool_code, ToolPermission.ALLOW)
            db.add(EmployeeToolGrant(employee_id=emp.id, tool_id=tool.id, permission=perm))
    instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
    if instructions and data.get("instructions"):
        ins = data["instructions"]
        instructions.system_purpose = ins.get("system_purpose")
        instructions.role_text = ins.get("role")
        instructions.objective_text = ins.get("objective")
        instructions.operating_rules = ins.get("operating_rules")
        instructions.constraints_text = ins.get("constraints")
        instructions.output_contract = ins.get("output_contract")
    emp.lifecycle_status = EmployeeLifecycleStatus.CONFIGURING


def update_employee(
    db: Session,
    org_id: str,
    user_id: str,
    employee_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}
    if emp.lifecycle_status in (EmployeeLifecycleStatus.ACTIVE, EmployeeLifecycleStatus.PUBLISHED):
        if payload.get("force_new_version"):
            emp.version += 1
            emp.lifecycle_status = EmployeeLifecycleStatus.CONFIGURING

    for field in ("name", "description", "role", "objective", "specialty", "risk_level", "maturity", "shadow_mode"):
        if field in payload:
            setattr(emp, field, payload[field])

    if "capability_ids" in payload:
        db.query(EmployeeCapability).filter(EmployeeCapability.employee_id == emp.id).delete()
        for cap_id in payload["capability_ids"]:
            db.add(EmployeeCapability(employee_id=emp.id, capability_id=cap_id))

    if "tools" in payload:
        db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id).delete()
        for t in payload["tools"]:
            db.add(EmployeeToolGrant(employee_id=emp.id, tool_id=t["tool_id"], permission=t.get("permission", ToolPermission.ALLOW)))

    if "knowledge" in payload:
        db.query(EmployeeKnowledgeSource).filter(EmployeeKnowledgeSource.employee_id == emp.id).delete()
        for k in payload["knowledge"]:
            db.add(EmployeeKnowledgeSource(
                organization_id=org_id,
                employee_id=emp.id,
                source_type=k["source_type"],
                name=k["name"],
                config_json=json.dumps(k.get("config", {})),
            ))

    if "model_policy" in payload:
        policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first()
        if not policy:
            policy = EmployeeModelPolicy(employee_id=emp.id)
            db.add(policy)
        mp = payload["model_policy"]
        policy.preferred_provider = mp.get("preferred_provider")
        policy.preferred_model = mp.get("preferred_model")
        policy.allowed_models_json = json.dumps(mp.get("allowed_models", []))
        policy.fallback_model = mp.get("fallback_model")
        policy.max_tokens = mp.get("max_tokens")
        policy.temperature = mp.get("temperature")
        policy.timeout_seconds = mp.get("timeout_seconds")
        policy.budget_daily = mp.get("budget_daily")
        policy.cost_ceiling = mp.get("cost_ceiling")
        emp.model_provider = mp.get("preferred_provider")
        emp.model_name = mp.get("preferred_model")

    if "limits" in payload:
        limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == emp.id).first()
        if limits:
            for k, v in payload["limits"].items():
                if hasattr(limits, k):
                    setattr(limits, k, v)

    if "instructions" in payload:
        instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first()
        if instructions:
            ins = payload["instructions"]
            for k in ("system_purpose", "role_text", "objective_text", "operating_rules", "constraints_text", "output_contract"):
                if k in ins:
                    setattr(instructions, k, ins[k])

    if emp.lifecycle_status == EmployeeLifecycleStatus.DRAFT:
        emp.lifecycle_status = EmployeeLifecycleStatus.CONFIGURING

    emp.updated_at = _utcnow()
    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_UPDATED, emp.id)
    return get_employee_detail(db, org_id, emp.id) or {}


def _run_tool_for_employee(db: Session, emp: AIEmployee, inputs: dict[str, Any]) -> dict[str, Any]:
    grant = db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id).first()
    if not grant:
        return {"error": "Sin herramientas asignadas"}
    if grant.permission == ToolPermission.DENY:
        return {"error": "Herramienta denegada"}
    tool = db.query(Tool).filter(Tool.id == grant.tool_id).first()
    if not tool:
        return {"error": "Herramienta no encontrada"}
    if emp.shadow_mode:
        return {"shadow": True, "tool": tool.code, "message": "Modo shadow: sin acciones externas"}
    if tool.code == "rips":
        return rips.analyze_rips(inputs)
    return docint.analyze_documents(inputs)


def run_employee_tests(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}

    emp.lifecycle_status = EmployeeLifecycleStatus.TESTING
    cases = db.query(EmployeeTestCase).filter(EmployeeTestCase.employee_id == emp.id, EmployeeTestCase.is_active.is_(True)).all()
    if not cases:
        cases_data = _default_test_cases(emp)
        for c in cases_data:
            db.add(EmployeeTestCase(employee_id=emp.id, **c))
        db.flush()
        cases = db.query(EmployeeTestCase).filter(EmployeeTestCase.employee_id == emp.id).all()

    results = []
    passed = 0
    for case in cases:
        start = time.monotonic()
        inputs = json.loads(case.input_json)
        try:
            actual = _run_tool_for_employee(db, emp, inputs)
            latency = int((time.monotonic() - start) * 1000)
            ok = "error" not in actual and (not case.expected_json or _validate_test(actual, json.loads(case.expected_json)))
            status = "PASSED" if ok else "FAILED"
            if ok:
                passed += 1
            run = EmployeeTestRun(
                employee_id=emp.id,
                test_case_id=case.id,
                test_type=case.test_type,
                status=status,
                input_json=case.input_json,
                actual_json=json.dumps(actual, ensure_ascii=False),
                latency_ms=latency,
                confidence=actual.get("confidence"),
                tools_used_json=json.dumps([actual.get("tool", "rule-engine")]),
            )
            db.add(run)
            results.append({"case": case.name, "status": status, "latency_ms": latency})
        except Exception as exc:
            db.add(EmployeeTestRun(
                employee_id=emp.id, test_case_id=case.id, test_type=case.test_type,
                status="FAILED", error=str(exc), input_json=case.input_json,
            ))
            results.append({"case": case.name, "status": "FAILED", "error": str(exc)})

    all_passed = passed == len(cases)
    emp.lifecycle_status = EmployeeLifecycleStatus.READY_FOR_CERTIFICATION if all_passed else EmployeeLifecycleStatus.FAILED_TEST
    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_TESTED, emp.id, {"passed": passed, "total": len(cases)})
    return {"employee_id": emp.id, "status": emp.lifecycle_status, "passed": passed, "total": len(cases), "results": results}


def _validate_test(actual: dict, expected: dict) -> bool:
    if expected.get("min_findings") is not None:
        return len(actual.get("findings", [])) >= expected["min_findings"]
    if expected.get("has_findings"):
        return len(actual.get("findings", [])) > 0
    return actual.get("confidence", 0) >= expected.get("min_confidence", 0)


def _default_test_cases(emp: AIEmployee) -> list[dict[str, Any]]:
    if "RIPS" in emp.specialty.upper():
        return [{
            "name": "RIPS smoke",
            "test_type": "SMOKE",
            "input_json": json.dumps({"rips": {"usuarios": [], "consultas": [], "procedimientos": [], "medicamentos": [], "otrosServicios": []}}),
            "expected_json": json.dumps({"has_findings": True}),
        }]
    return [{
        "name": "DOCINT smoke",
        "test_type": "SMOKE",
        "input_json": json.dumps({"documents": []}),
        "expected_json": json.dumps({"has_findings": True}),
    }]


def certify_employee(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}

    caps = db.query(EmployeeCapability).filter(EmployeeCapability.employee_id == emp.id).count()
    tools = db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id).count()
    tests = db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "PASSED").count()

    issues = []
    if caps == 0:
        issues.append("Sin capabilities")
    if tools == 0:
        issues.append("Sin herramientas")
    if tests == 0:
        issues.append("Sin pruebas exitosas")

    failed = db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id, EmployeeTestRun.status == "FAILED").count()
    if failed:
        issues.append(f"{failed} prueba(s) fallida(s)")

    score = max(0.0, 1.0 - len(issues) * 0.2)
    if not issues:
        result = CertificationResult.PASS
    elif score >= 0.6:
        result = CertificationResult.PASS_WITH_WARNINGS
    else:
        result = CertificationResult.FAIL

    cert = EmployeeCertification(
        employee_id=emp.id,
        version=emp.version,
        result=result,
        score=score,
        risk_level=emp.risk_level,
        details_json=json.dumps({"issues": issues, "capabilities": caps, "tools": tools, "tests_passed": tests}),
        certified_by_id=user_id,
    )
    db.add(cert)

    if result != CertificationResult.FAIL:
        emp.lifecycle_status = EmployeeLifecycleStatus.CERTIFIED
        emp.certified_at = _utcnow()
        _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_CERTIFIED, emp.id, {"result": result})
    else:
        emp.lifecycle_status = EmployeeLifecycleStatus.FAILED_TEST
        _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_CERTIFICATION_FAILED, emp.id, {"issues": issues})

    db.commit()
    return {"employee_id": emp.id, "result": result, "score": score, "issues": issues, "lifecycle_status": emp.lifecycle_status}


def publish_employee(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}
    if emp.lifecycle_status != EmployeeLifecycleStatus.CERTIFIED:
        return {"error": "Solo empleados CERTIFIED pueden publicarse"}

    snapshot = _employee_config_snapshot(db, emp)
    db.add(EmployeeVersion(
        employee_id=emp.id,
        version=emp.version,
        configuration_json=json.dumps(snapshot, ensure_ascii=False),
        status="PUBLISHED",
        created_by_id=user_id,
    ))
    emp.lifecycle_status = EmployeeLifecycleStatus.PUBLISHED
    emp.published_at = _utcnow()
    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_PUBLISHED, emp.id, {"version": emp.version})
    return get_employee_detail(db, org_id, emp.id) or {}


def activate_employee(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}
    if emp.lifecycle_status not in (EmployeeLifecycleStatus.PUBLISHED, EmployeeLifecycleStatus.PAUSED):
        return {"error": "Empleado debe estar PUBLISHED o PAUSED para activar"}

    emp.lifecycle_status = EmployeeLifecycleStatus.ACTIVE
    emp.status = "DISPONIBLE"
    emp.maturity = EmployeeMaturity.AUTONOMOUS_CONTROLLED if not emp.shadow_mode else EmployeeMaturity.SHADOW
    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_ACTIVATED, emp.id)
    return get_employee_detail(db, org_id, emp.id) or {}


def pause_employee(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}
    emp.lifecycle_status = EmployeeLifecycleStatus.PAUSED
    emp.status = "PAUSADO"
    db.commit()
    _emit(db, org_id, user_id, EmployeeEventType.EMPLOYEE_PAUSED, emp.id)
    return get_employee_detail(db, org_id, emp.id) or {}


def get_employee_metrics(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        return {"error": "Empleado no encontrado"}
    runs = db.query(EmployeeTestRun).filter(EmployeeTestRun.employee_id == emp.id).all()
    finops = db.query(FinOpsRecord).filter(FinOpsRecord.organization_id == org_id).all()
    return {
        "employee_id": emp.id,
        "test_runs": len(runs),
        "test_passed": sum(1 for r in runs if r.status == "PASSED"),
        "avg_latency_ms": sum(r.latency_ms or 0 for r in runs) / len(runs) if runs else None,
        "finops_available": len(finops) > 0,
    }


def list_templates(db: Session) -> list[dict[str, Any]]:
    rows = db.query(EmployeeTemplate).filter(EmployeeTemplate.is_active.is_(True)).all()
    return [{"code": t.code, "name": t.name, "description": t.description, "specialty": t.specialty} for t in rows]


def list_capabilities(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(Capability).filter(Capability.organization_id == org_id, Capability.is_active.is_(True)).all()
    return [{
        "id": c.id, "code": c.code, "name": c.name, "description": c.description,
        "risk_level": c.risk_level, "inputs": json.loads(c.inputs_json) if c.inputs_json else [],
        "outputs": json.loads(c.outputs_json) if c.outputs_json else [],
        "executor_types": json.loads(c.executor_types_json) if c.executor_types_json else [],
    } for c in rows]


def list_tools(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = db.query(Tool).filter(Tool.organization_id == org_id, Tool.is_active.is_(True)).all()
    return [{"id": t.id, "code": t.code, "name": t.name, "executor_type": t.executor_type, "risk_level": t.risk_level} for t in rows]
