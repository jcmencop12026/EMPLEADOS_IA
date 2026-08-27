"""Selección de especialistas IPS — capacidades base + orquestador transversal."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.enums import EmployeeLifecycleStatus
from app.orchestration_models import AIEmployee, Capability, EmployeeCapability, EmployeeToolGrant, Tool
from app.salud_models import IpsEmployeePerformance

IPS_DOMAIN_CAPABILITIES: dict[str, list[str]] = {
    "facturacion": ["ips-facturacion", "ips-analitica"],
    "radicacion": ["ips-radicacion", "ips-analitica"],
    "glosas": ["ips-glosas", "ips-analitica"],
    "cartera": ["ips-cartera", "ips-analitica"],
    "contratos": ["ips-contractual", "ips-analitica"],
    "rips": ["rips", "ips-analitica"],
    "estrategico": ["ips-estrategico", "ips-analitica"],
    "ideacion": ["ips-estrategico", "ips-proceso"],
}

REQUEST_KEYWORDS: dict[str, list[str]] = {
    "facturacion": ["facturación", "facturacion", "facturado", "factura"],
    "radicacion": ["radicación", "radicacion", "radicado"],
    "glosas": ["glosa", "glosas", "objeción", "objecion", "devolución", "devolucion"],
    "cartera": ["cartera", "cobro", "mora", "recaudo", "caja", "pagador"],
    "contratos": ["contrato", "contractual", "tarifa", "capitación", "capitacion"],
    "rips": ["rips", "validación rips"],
    "estrategico": ["estratég", "estrateg", "integral", "diagnóstico", "diagnostico", "situación", "situacion"],
    "ideacion": ["propón", "propon", "estrategias", "ideas", "reducir", "mejorar"],
}


def detect_required_domains(request: str, available_data: list[str] | None = None) -> list[str]:
    text = request.lower()
    domains: set[str] = set()
    for domain, keywords in REQUEST_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            domains.add(domain)
    if available_data:
        data_domain_map = {
            "facturacion": "facturacion",
            "radicacion": "radicacion",
            "glosas": "glosas",
            "cartera": "cartera",
            "contratos": "contratos",
            "pagos": "cartera",
        }
        for src in available_data:
            if src in data_domain_map:
                domains.add(data_domain_map[src])
    if not domains or "estrategico" in text or "integral" in text:
        if available_data:
            for src in available_data:
                mapped = {
                    "facturacion": "facturacion", "radicacion": "radicacion",
                    "glosas": "glosas", "cartera": "cartera", "contratos": "contratos",
                }.get(src)
                if mapped:
                    domains.add(mapped)
        domains.add("estrategico")
    return sorted(domains)


def _employee_capabilities(db: Session, employee_id: str) -> list[str]:
    rows = (
        db.query(Capability.code)
        .join(EmployeeCapability, EmployeeCapability.capability_id == Capability.id)
        .filter(EmployeeCapability.employee_id == employee_id)
        .all()
    )
    return [r[0] for r in rows]


def _employee_tools(db: Session, employee_id: str) -> list[str]:
    rows = (
        db.query(Tool.code)
        .join(EmployeeToolGrant, EmployeeToolGrant.tool_id == Tool.id)
        .filter(EmployeeToolGrant.employee_id == employee_id, EmployeeToolGrant.permission != "DENY")
        .all()
    )
    return [r[0] for r in rows]


def _performance_score(db: Session, org_id: str, employee_id: str, specialty: str) -> float:
    perf = (
        db.query(IpsEmployeePerformance)
        .filter(
            IpsEmployeePerformance.organization_id == org_id,
            IpsEmployeePerformance.employee_id == employee_id,
            IpsEmployeePerformance.specialty == specialty,
        )
        .first()
    )
    if not perf:
        return 0.5
    try:
        metrics = json.loads(perf.metrics_json or "{}")
    except json.JSONDecodeError:
        return 0.5
    acceptance = metrics.get("tasa_aceptacion", 0.5)
    positive = metrics.get("resultados_positivos", 0)
    total = max(metrics.get("analisis_realizados", 1), 1)
    return min(0.3 * acceptance + 0.2 * (positive / total) + 0.5, 1.0)


def score_employee_for_domain(
    db: Session,
    org_id: str,
    employee: AIEmployee,
    domain: str,
    task_type: str = "analisis",
) -> dict[str, Any]:
    del task_type
    required_caps = IPS_DOMAIN_CAPABILITIES.get(domain, ["ips-analitica"])
    emp_caps = _employee_capabilities(db, employee.id)
    emp_tools = _employee_tools(db, employee.id)
    cap_match = sum(1 for c in required_caps if c in emp_caps) / max(len(required_caps), 1)
    tool_match = 1.0 if any(t.startswith("salud-") or t.startswith("ips-") for t in emp_tools) else 0.3
    specialty_lower = (employee.specialty or "").lower()
    specialty_bonus = 0.0
    domain_keywords = REQUEST_KEYWORDS.get(domain, [])
    if any(kw in specialty_lower for kw in domain_keywords):
        specialty_bonus = 0.2
    availability = 1.0 if employee.lifecycle_status in (
        EmployeeLifecycleStatus.ACTIVE, EmployeeLifecycleStatus.PUBLISHED,
    ) else 0.0
    experience = _performance_score(db, org_id, employee.id, employee.specialty)
    total = cap_match * 0.35 + tool_match * 0.15 + specialty_bonus + availability * 0.15 + experience * 0.15
    return {
        "employee_id": employee.id,
        "employee_code": employee.code,
        "employee_name": employee.name,
        "specialty": employee.specialty,
        "domain": domain,
        "score": round(total, 3),
        "factors": {
            "capacidades": round(cap_match, 3),
            "herramientas": round(tool_match, 3),
            "especialidad": specialty_bonus,
            "disponibilidad": availability,
            "experiencia": round(experience, 3),
        },
    }


def select_specialists(
    db: Session,
    org_id: str,
    request: str,
    available_data: list[str] | None = None,
    data_profiles: dict[str, Any] | None = None,
    contexto: dict | None = None,
    max_per_domain: int = 1,
) -> dict[str, Any]:
    """Delega al orquestador transversal ORQUESTADOR-EXPERIENCIA-1010."""
    from app.services.orchestrator_selection import select_team

    del max_per_domain
    plan = select_team(
        db, org_id, request,
        available_data=available_data,
        data_profiles=data_profiles,
        contexto=contexto,
        persist_log=True,
    )
    if not plan.get("dominios"):
        plan["dominios"] = detect_required_domains(request, available_data)
    return plan
