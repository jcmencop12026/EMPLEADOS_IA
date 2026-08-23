import json

from sqlalchemy.orm import Session

from app.enums import EmployeeLifecycleStatus, EmployeeMaturity, ExecutorType, RiskLevel, ToolPermission
from app.orchestration_models import (
    AIEmployee,
    Capability,
    EmployeeCapability,
    EmployeeInstructions,
    EmployeeLimits,
    EmployeeModelPolicy,
    EmployeeTemplate,
    EmployeeToolGrant,
    Tool,
)


def _cap_meta(code: str) -> dict:
    if code == "docint":
        return {
            "inputs": ["documents"],
            "outputs": ["findings", "confidence", "summary"],
            "executor_types": [ExecutorType.PYTHON, ExecutorType.RULE],
        }
    return {
        "inputs": ["rips"],
        "outputs": ["findings", "confidence", "summary"],
        "executor_types": [ExecutorType.RULE, ExecutorType.PYTHON],
    }


def bootstrap_orchestration(db: Session, organization_id: str) -> None:
    if db.query(Capability).filter(Capability.organization_id == organization_id).first():
        _upgrade_existing(db, organization_id)
        return

    cap_docint = Capability(
        organization_id=organization_id,
        code="docint",
        name="Análisis Documental DOCINT",
        description="Validación y análisis de documentos clínicos/administrativos",
        risk_level=RiskLevel.MEDIUM,
        requires_approval=False,
        inputs_json=json.dumps(_cap_meta("docint")["inputs"]),
        outputs_json=json.dumps(_cap_meta("docint")["outputs"]),
        executor_types_json=json.dumps(_cap_meta("docint")["executor_types"]),
    )
    cap_rips = Capability(
        organization_id=organization_id,
        code="rips",
        name="Validación RIPS Salud IPS",
        description="Validación estructural de archivos RIPS",
        risk_level=RiskLevel.HIGH,
        requires_approval=True,
        inputs_json=json.dumps(_cap_meta("rips")["inputs"]),
        outputs_json=json.dumps(_cap_meta("rips")["outputs"]),
        executor_types_json=json.dumps(_cap_meta("rips")["executor_types"]),
    )
    db.add_all([cap_docint, cap_rips])
    db.flush()

    tool_docint = Tool(
        organization_id=organization_id,
        capability_id=cap_docint.id,
        code="docint",
        name="Motor DOCINT",
        executor_type=ExecutorType.PYTHON,
        risk_level=RiskLevel.MEDIUM,
        requires_approval=False,
    )
    tool_rips = Tool(
        organization_id=organization_id,
        capability_id=cap_rips.id,
        code="rips",
        name="Validador RIPS",
        executor_type=ExecutorType.RULE,
        risk_level=RiskLevel.HIGH,
        requires_approval=True,
    )
    db.add_all([tool_docint, tool_rips])
    db.flush()

    emp_docint = _make_employee(
        organization_id, "docint-analyst", "Analista Documental IA", "DOCINT",
        "Analista documental", "Analizar documentos y detectar problemas estructurales",
        RiskLevel.MEDIUM, "docint-rules-v1",
    )
    emp_rips = _make_employee(
        organization_id, "rips-auditor", "Auditor RIPS IA", "RIPS Salud IPS",
        "Auditor RIPS", "Validar archivos RIPS y reportar inconsistencias",
        RiskLevel.HIGH, "rips-validator-v1",
    )
    db.add_all([emp_docint, emp_rips])
    db.flush()

    for emp, cap, tool, perm in [
        (emp_docint, cap_docint, tool_docint, ToolPermission.ALLOW),
        (emp_rips, cap_rips, tool_rips, ToolPermission.REQUIRES_APPROVAL),
    ]:
        db.add(EmployeeCapability(employee_id=emp.id, capability_id=cap.id))
        db.add(EmployeeToolGrant(employee_id=emp.id, tool_id=tool.id, permission=perm))
        db.add(EmployeeLimits(employee_id=emp.id))
        db.add(EmployeeModelPolicy(employee_id=emp.id, preferred_provider="rule-engine", preferred_model=emp.model_name))
        db.add(EmployeeInstructions(
            employee_id=emp.id,
            system_purpose=f"Especialista {emp.specialty}",
            role_text=emp.role,
            objective_text=emp.objective,
        ))

    _seed_templates(db, organization_id)
    db.commit()


def _make_employee(
    org_id: str, code: str, name: str, specialty: str,
    role: str, objective: str, risk: str, model: str,
) -> AIEmployee:
    return AIEmployee(
        organization_id=org_id,
        code=code,
        name=name,
        specialty=specialty,
        role=role,
        objective=objective,
        risk_level=risk,
        lifecycle_status=EmployeeLifecycleStatus.ACTIVE,
        maturity=EmployeeMaturity.AUTONOMOUS_CONTROLLED,
        model_provider="rule-engine",
        model_name=model,
        version=1,
    )


def _seed_templates(db: Session, organization_id: str) -> None:
    if db.query(EmployeeTemplate).first():
        return
    templates = [
        ("analista-documental", "Analista documental", "DOCINT", "docint", ["docint"], {"docint": "ALLOW"}),
        ("auditor-rips", "Auditor RIPS", "RIPS Salud IPS", "rips", ["rips"], {"rips": "REQUIRES_APPROVAL"}),
        ("analista-datos", "Analista de datos", "Datos", "docint", ["docint"], {"docint": "ALLOW"}),
        ("asistente-investigacion", "Asistente de investigación", "Investigación", "docint", ["docint"], {"docint": "ALLOW"}),
    ]
    for code, name, specialty, cap, tools, perms in templates:
        db.add(EmployeeTemplate(
            organization_id=organization_id,
            code=code,
            name=name,
            specialty=specialty,
            description=f"Plantilla {name}",
            template_json=json.dumps({
                "role": name,
                "objective": f"Ejecutar tareas de {specialty}",
                "risk_level": RiskLevel.MEDIUM,
                "model_provider": "rule-engine",
                "capabilities": [cap],
                "tools": tools,
                "tool_permissions": perms,
                "instructions": {
                    "system_purpose": f"Asistente especializado en {specialty}",
                    "role": name,
                    "operating_rules": "Preferir RULE/PYTHON antes de LLM",
                },
            }),
        ))


def _upgrade_existing(db: Session, organization_id: str) -> None:
    """Migra empleados CURSOR-801 a representación Agent Factory."""
    for cap in db.query(Capability).filter(Capability.organization_id == organization_id).all():
        meta = _cap_meta(cap.code)
        if not cap.inputs_json:
            cap.inputs_json = json.dumps(meta["inputs"])
            cap.outputs_json = json.dumps(meta["outputs"])
            cap.executor_types_json = json.dumps(meta["executor_types"])

    mapping = {
        "Analista Documental IA": ("docint-analyst", "DOCINT", RiskLevel.MEDIUM),
        "Auditor RIPS IA": ("rips-auditor", "RIPS Salud IPS", RiskLevel.HIGH),
    }
    for emp in db.query(AIEmployee).filter(AIEmployee.organization_id == organization_id).all():
        if not emp.code or emp.code == "":
            info = mapping.get(emp.name, (f"emp-{emp.id[:8]}", emp.specialty, RiskLevel.LOW))
            emp.code = info[0]
            emp.role = emp.role or emp.name
            emp.objective = emp.objective or f"Especialista {emp.specialty}"
            emp.risk_level = info[2]
        if emp.lifecycle_status in ("DRAFT", None) or not emp.lifecycle_status:
            emp.lifecycle_status = EmployeeLifecycleStatus.ACTIVE
            emp.maturity = EmployeeMaturity.AUTONOMOUS_CONTROLLED
        if not db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == emp.id).first():
            db.add(EmployeeLimits(employee_id=emp.id))
        if not db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first():
            db.add(EmployeeModelPolicy(employee_id=emp.id, preferred_provider=emp.model_provider, preferred_model=emp.model_name))
        if not db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp.id).first():
            db.add(EmployeeInstructions(employee_id=emp.id, role_text=emp.role, objective_text=emp.objective))
        cap = db.query(Capability).join(EmployeeCapability).filter(EmployeeCapability.employee_id == emp.id).first()
        tool = db.query(Tool).filter(Tool.organization_id == organization_id).first()
        if cap:
            tool = db.query(Tool).filter(Tool.capability_id == cap.id).first()
        if tool and not db.query(EmployeeToolGrant).filter(EmployeeToolGrant.employee_id == emp.id).first():
            perm = ToolPermission.REQUIRES_APPROVAL if tool.code == "rips" else ToolPermission.ALLOW
            db.add(EmployeeToolGrant(employee_id=emp.id, tool_id=tool.id, permission=perm))

    _seed_templates(db, organization_id)
    db.commit()
