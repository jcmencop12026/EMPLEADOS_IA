from sqlalchemy.orm import Session

from app.enums import ExecutorType
from app.orchestration_models import AIEmployee, Capability, EmployeeCapability, Tool


def bootstrap_orchestration(db: Session, organization_id: str) -> None:
    if db.query(Capability).filter(Capability.organization_id == organization_id).first():
        return

    cap_docint = Capability(
        organization_id=organization_id,
        code="docint",
        name="Análisis Documental DOCINT",
        description="Validación y análisis de documentos clínicos/administrativos",
        risk_level="medium",
        requires_approval=False,
    )
    cap_rips = Capability(
        organization_id=organization_id,
        code="rips",
        name="Validación RIPS Salud IPS",
        description="Validación estructural de archivos RIPS",
        risk_level="high",
        requires_approval=True,
    )
    db.add_all([cap_docint, cap_rips])
    db.flush()

    tool_docint = Tool(
        organization_id=organization_id,
        capability_id=cap_docint.id,
        code="docint",
        name="Motor DOCINT",
        executor_type=ExecutorType.PYTHON,
        risk_level="medium",
        requires_approval=False,
    )
    tool_rips = Tool(
        organization_id=organization_id,
        capability_id=cap_rips.id,
        code="rips",
        name="Validador RIPS",
        executor_type=ExecutorType.RULE,
        risk_level="high",
        requires_approval=True,
    )
    db.add_all([tool_docint, tool_rips])
    db.flush()

    emp_docint = AIEmployee(
        organization_id=organization_id,
        name="Analista Documental IA",
        specialty="DOCINT",
        model_provider="rule-engine",
        model_name="docint-rules-v1",
    )
    emp_rips = AIEmployee(
        organization_id=organization_id,
        name="Auditor RIPS IA",
        specialty="RIPS Salud IPS",
        model_provider="rule-engine",
        model_name="rips-validator-v1",
    )
    db.add_all([emp_docint, emp_rips])
    db.flush()

    db.add_all([
        EmployeeCapability(employee_id=emp_docint.id, capability_id=cap_docint.id),
        EmployeeCapability(employee_id=emp_rips.id, capability_id=cap_rips.id),
    ])
    db.commit()
