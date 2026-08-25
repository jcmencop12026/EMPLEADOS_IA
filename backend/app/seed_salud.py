"""Seed de capacidades, herramientas y especialistas IPS."""

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

IPS_SPECIALISTS = [
    ("ips-facturacion-analyst", "Analista de Facturación IA", "Facturación IPS", "ips-facturacion", ["salud-concentracion", "salud-tendencias", "salud-anomalias"]),
    ("ips-radicacion-analyst", "Analista de Radicación IA", "Radicación IPS", "ips-radicacion", ["salud-facturado-radicado"]),
    ("ips-glosas-analyst", "Analista de Glosas IA", "Glosas IPS", "ips-glosas", ["salud-glosas"]),
    ("ips-cartera-analyst", "Analista de Cartera IA", "Cartera IPS", "ips-cartera", ["salud-aging", "salud-dias-pago"]),
    ("ips-contractual-analyst", "Analista Contractual IA", "Contratación IPS", "ips-contractual", ["salud-contratos"]),
    ("ips-rips-analyst", "Analista RIPS IA", "RIPS Salud IPS", "rips", ["rips"]),
    ("ips-estrategico-analyst", "Analista Estratégico IPS IA", "Analítica Estratégica IPS", "ips-estrategico", ["salud-indicadores", "salud-trazabilidad"]),
]

IPS_CAPABILITIES = [
    ("ips-facturacion", "Análisis de Facturación IPS", "Facturación y concentración"),
    ("ips-radicacion", "Análisis de Radicación IPS", "Radicación y tiempos"),
    ("ips-glosas", "Análisis de Glosas IPS", "Glosas y recuperación"),
    ("ips-cartera", "Análisis de Cartera IPS", "Cartera, aging y recaudo"),
    ("ips-contractual", "Análisis Contractual IPS", "Contratos y tarifas"),
    ("ips-estrategico", "Análisis Estratégico IPS", "Consolidación y diagnóstico integral"),
    ("ips-analitica", "Analítica IPS General", "Herramientas analíticas transversales"),
    ("ips-proceso", "Análisis de Procesos IPS", "Mejora de procesos operativos"),
]

IPS_TOOLS = [
    ("salud-facturado-radicado", "Análisis facturado/radicado", "ips-radicacion"),
    ("salud-aging", "Análisis aging cartera", "ips-cartera"),
    ("salud-dias-pago", "Análisis días de pago", "ips-cartera"),
    ("salud-concentracion", "Análisis concentración", "ips-facturacion"),
    ("salud-glosas", "Análisis glosas", "ips-glosas"),
    ("salud-tendencias", "Análisis tendencias", "ips-facturacion"),
    ("salud-anomalias", "Detección anomalías", "ips-analitica"),
    ("salud-trazabilidad", "Trazabilidad de valores", "ips-estrategico"),
    ("salud-indicadores", "Cálculo indicadores IPS", "ips-analitica"),
    ("salud-contratos", "Análisis contratos", "ips-contractual"),
    ("salud-perfil-datos", "Perfilado de datos IPS", "ips-analitica"),
]


def bootstrap_salud(db: Session, organization_id: str) -> None:
    """Idempotente: agrega capacidades/herramientas/especialistas IPS."""
    cap_map: dict[str, Capability] = {}

    for code, name, desc in IPS_CAPABILITIES:
        existing = (
            db.query(Capability)
            .filter(Capability.organization_id == organization_id, Capability.code == code)
            .first()
        )
        if existing:
            cap_map[code] = existing
            continue
        cap = Capability(
            organization_id=organization_id,
            code=code,
            name=name,
            description=desc,
            risk_level=RiskLevel.MEDIUM,
            requires_approval=False,
            inputs_json=json.dumps(["datasets"]),
            outputs_json=json.dumps(["indicadores", "hallazgos"]),
            executor_types_json=json.dumps([ExecutorType.PYTHON]),
        )
        db.add(cap)
        db.flush()
        cap_map[code] = cap

    tool_map: dict[str, Tool] = {}
    for code, name, cap_code in IPS_TOOLS:
        existing = (
            db.query(Tool)
            .filter(Tool.organization_id == organization_id, Tool.code == code)
            .first()
        )
        if existing:
            tool_map[code] = existing
            continue
        cap = cap_map.get(cap_code)
        if not cap:
            continue
        tool = Tool(
            organization_id=organization_id,
            capability_id=cap.id,
            code=code,
            name=name,
            executor_type=ExecutorType.PYTHON,
            risk_level=RiskLevel.MEDIUM,
        )
        db.add(tool)
        db.flush()
        tool_map[code] = tool

    for emp_code, name, specialty, cap_code, tool_codes in IPS_SPECIALISTS:
        existing = (
            db.query(AIEmployee)
            .filter(AIEmployee.organization_id == organization_id, AIEmployee.code == emp_code)
            .first()
        )
        if existing:
            continue

        emp = AIEmployee(
            organization_id=organization_id,
            code=emp_code,
            name=name,
            specialty=specialty,
            role=name,
            objective=f"Analizar {specialty.lower()} con evidencia y sin alucinación de datos",
            risk_level=RiskLevel.MEDIUM,
            lifecycle_status=EmployeeLifecycleStatus.ACTIVE,
            maturity=EmployeeMaturity.AUTONOMOUS_CONTROLLED,
            model_provider="rule-engine",
            model_name="salud-ips-v1",
            version=1,
        )
        db.add(emp)
        db.flush()

        cap = cap_map.get(cap_code)
        if cap:
            db.add(EmployeeCapability(employee_id=emp.id, capability_id=cap.id))
        db.add(EmployeeCapability(employee_id=emp.id, capability_id=cap_map["ips-analitica"].id))

        for tc in tool_codes:
            tool = tool_map.get(tc)
            if tool:
                db.add(EmployeeToolGrant(employee_id=emp.id, tool_id=tool.id, permission=ToolPermission.ALLOW))

        db.add(EmployeeLimits(employee_id=emp.id))
        db.add(EmployeeModelPolicy(employee_id=emp.id, preferred_provider="rule-engine", preferred_model="salud-ips-v1"))
        db.add(EmployeeInstructions(
            employee_id=emp.id,
            system_purpose=f"Especialista en {specialty}",
            role_text=name,
            objective_text=f"Analizar {specialty} con indicadores determinísticos",
        ))

    _seed_ips_templates(db, organization_id)
    db.commit()


def _seed_ips_templates(db: Session, organization_id: str) -> None:
    templates = [
        ("plantilla-facturacion-ips", "Analista de Facturación", "Facturación IPS", "ips-facturacion"),
        ("plantilla-radicacion-ips", "Analista de Radicación", "Radicación IPS", "ips-radicacion"),
        ("plantilla-glosas-ips", "Analista de Glosas", "Glosas IPS", "ips-glosas"),
        ("plantilla-cartera-ips", "Analista de Cartera", "Cartera IPS", "ips-cartera"),
        ("plantilla-contractual-ips", "Analista Contractual", "Contratación IPS", "ips-contractual"),
        ("plantilla-estrategico-ips", "Analista Estratégico IPS", "Analítica Estratégica IPS", "ips-estrategico"),
    ]
    for code, name, specialty, cap in templates:
        if db.query(EmployeeTemplate).filter(EmployeeTemplate.code == code).first():
            continue
        db.add(EmployeeTemplate(
            organization_id=organization_id,
            code=code,
            name=name,
            specialty=specialty,
            description=f"Plantilla {name} para análisis IPS",
            template_json=json.dumps({
                "role": name,
                "objective": f"Ejecutar análisis de {specialty}",
                "capabilities": [cap, "ips-analitica"],
                "model_provider": "rule-engine",
            }),
        ))
