"""Selección dinámica transversal de Empleados IA — ORQUESTADOR-EXPERIENCIA-1010."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.enums import EmployeeLifecycleStatus
from app.experience_models import ExperienceSelectionLog
from app.orchestration_models import AIEmployee, Capability, EmployeeCapability, EmployeeToolGrant, FinOpsRecord, Tool
from app.services.experience_core import experiencia_score_para_empleado
from app.services.salud_specialist_selection import (
    IPS_DOMAIN_CAPABILITIES,
    REQUEST_KEYWORDS,
    _employee_capabilities,
    _employee_tools,
)

FACTOR_WEIGHTS = {
    "capacidad": 0.25,
    "experiencia": 0.20,
    "desempeno": 0.15,
    "costo": 0.10,
    "disponibilidad": 0.10,
    "riesgo": 0.10,
    "diversidad": 0.10,
}

ROLE_LIDER = "LIDER"
ROLE_COMPLEMENTARIO = "ESPECIALISTA_COMPLEMENTARIO"
ROLE_VALIDADOR = "VALIDADOR"
ROLE_DISIDENTE = "DISIDENTE"

DOMAIN_TO_PROBLEM_TYPE = {
    "radicacion": "radicacion_tardia",
    "glosas": "glosas_devoluciones",
    "cartera": "comportamiento_pagador",
    "facturacion": "concentracion_facturacion",
    "contratos": "contractual_tarifas",
    "estrategico": "diagnostico_integral",
    "rips": "validacion_rips",
    "ideacion": "datos_insuficientes",
}

DATA_DOMAIN_MAP = {
    "facturacion": "facturacion",
    "radicacion": "radicacion",
    "glosas": "glosas",
    "cartera": "cartera",
    "contratos": "contratos",
    "pagos": "cartera",
}


def detect_primary_domain(
    request: str,
    available_data: list[str] | None = None,
    data_profiles: dict[str, Any] | None = None,
) -> tuple[str, list[str], str]:
    """Detecta dominio principal, secundarios y tipo de problema."""
    text = request.lower()
    scores: dict[str, float] = {}

    for domain, keywords in REQUEST_KEYWORDS.items():
        hit = sum(1 for kw in keywords if kw in text)
        if hit:
            scores[domain] = scores.get(domain, 0) + hit

    if "glosa" in text or "devolucion" in text or "devolución" in text or "objecion" in text:
        scores["glosas"] = scores.get("glosas", 0) + 3
    if ("radicacion" in text or "radicación" in text) and "buen proceso" not in text:
        if "afectando" in text or "si la radicación" in text or "si la radicacion" in text:
            scores["radicacion"] = scores.get("radicacion", 0) + 4
        else:
            scores["radicacion"] = scores.get("radicacion", 0) + 2
    if "pagador" in text or ("comportamiento" in text and "cartera" in text):
        scores["cartera"] = scores.get("cartera", 0) + 2.5
    if "buen proceso" in text and "pagador" in text:
        scores.pop("radicacion", None)
        scores["cartera"] = scores.get("cartera", 0) + 3
    if "integral" in text or "combinad" in text or "concentración" in text or "concentracion" in text:
        scores["estrategico"] = scores.get("estrategico", 0) + 4

    insufficient = _detect_insufficient_data(text, available_data, data_profiles)
    if insufficient:
        return "estrategico", [], "datos_insuficientes"

    secondary: set[str] = set()
    if available_data:
        for src in available_data:
            mapped = DATA_DOMAIN_MAP.get(src)
            if mapped:
                secondary.add(mapped)

    if "integral" in text or "combinad" in text:
        primary = "estrategico"
        return primary, sorted(secondary - {primary}), DOMAIN_TO_PROBLEM_TYPE.get(primary, primary)

    if scores:
        primary = max(scores, key=lambda d: scores[d])
        secondary.discard(primary)
        return primary, sorted(secondary), DOMAIN_TO_PROBLEM_TYPE.get(primary, primary)

    if available_data:
        data_scores = {DATA_DOMAIN_MAP[src]: 1.0 for src in available_data if src in DATA_DOMAIN_MAP}
        if data_scores:
            primary = max(data_scores, key=lambda d: data_scores[d])
            secondary.discard(primary)
            return primary, sorted(secondary - {primary}), DOMAIN_TO_PROBLEM_TYPE.get(primary, primary)

    return "estrategico", sorted(secondary), "diagnostico_integral"


def _detect_insufficient_data(
    text: str,
    available_data: list[str] | None,
    data_profiles: dict[str, Any] | None,
) -> bool:
    asks_cartera = any(kw in text for kw in ("cartera", "cobro", "mora", "recaudo", "caja"))
    if not asks_cartera:
        return False
    if not available_data:
        return True
    has_cartera = "cartera" in available_data and available_data.count("cartera") >= 0
    if "cartera" not in (available_data or []):
        if data_profiles and not data_profiles.get("cartera"):
            return len(available_data) <= 1
        if len(available_data) <= 1:
            return True
    return False


def _finops_cost_score(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    rows = (
        db.query(FinOpsRecord)
        .filter(
            FinOpsRecord.organization_id == org_id,
            FinOpsRecord.employee_id == employee_id,
        )
        .order_by(FinOpsRecord.created_at.desc())
        .limit(20)
        .all()
    )
    if not rows:
        return {"score": 0.6, "costo_promedio": None, "explicacion": "Sin historial FINOPS — neutro"}
    costs = [r.cost for r in rows if r.cost is not None]
    if not costs:
        return {"score": 0.6, "costo_promedio": None, "explicacion": "Sin costos registrados"}
    avg = sum(costs) / len(costs)
    score = max(0.2, min(1.0, 1.0 - (avg / 10.0)))
    return {
        "score": round(score, 3),
        "costo_promedio": round(avg, 4),
        "explicacion": f"Costo promedio ${avg:.4f} — no se penaliza excesivamente",
    }


def _risk_score(employee: AIEmployee) -> float:
    risk_map = {"LOW": 0.9, "MEDIUM": 0.7, "HIGH": 0.4, "CRITICAL": 0.2}
    return risk_map.get((employee.risk_level or "MEDIUM").upper(), 0.7)


def score_candidate(
    db: Session,
    org_id: str,
    employee: AIEmployee,
    domain: str,
    problem_type: str,
    contexto: dict | None = None,
    selected_specialties: set[str] | None = None,
) -> dict[str, Any]:
    """Puntúa candidato con factores separados y trazables."""
    required_caps = IPS_DOMAIN_CAPABILITIES.get(domain, ["ips-analitica"])
    emp_caps = _employee_capabilities(db, employee.id)
    emp_tools = _employee_tools(db, employee.id)

    cap_match = sum(1 for c in required_caps if c in emp_caps) / max(len(required_caps), 1)
    tool_match = 1.0 if any(t.startswith("salud-") or t.startswith("ips-") for t in emp_tools) else 0.3

    specialty_lower = (employee.specialty or "").lower()
    specialty_bonus = 0.0
    domain_keywords = REQUEST_KEYWORDS.get(domain, [])
    if any(kw in specialty_lower for kw in domain_keywords):
        specialty_bonus = 0.15

    availability = 1.0 if employee.lifecycle_status in (
        EmployeeLifecycleStatus.ACTIVE,
        EmployeeLifecycleStatus.PUBLISHED,
    ) else 0.0

    exp = experiencia_score_para_empleado(
        db, org_id, employee.id, domain, problem_type, contexto,
    )
    finops = _finops_cost_score(db, org_id, employee.id)
    risk = _risk_score(employee)

    desempeno = exp["score"]
    diversidad = 1.0
    if selected_specialties and employee.specialty in selected_specialties:
        diversidad = 0.3

    factores = {
        "capacidad": round(cap_match * 0.7 + tool_match * 0.2 + specialty_bonus, 3),
        "experiencia": exp["score"],
        "desempeno": desempeno,
        "costo": finops["score"],
        "disponibilidad": availability,
        "riesgo": risk,
        "diversidad": diversidad,
    }

    total = sum(factores[k] * FACTOR_WEIGHTS[k] for k in FACTOR_WEIGHTS)
    razones = []
    if factores["capacidad"] >= 0.7:
        razones.append(f"capacidades alineadas con {domain}")
    if exp["casos"] > 0:
        razones.append(exp["explicacion"])
    if specialty_bonus > 0:
        razones.append(f"especialidad {employee.specialty} relevante")
    if finops.get("costo_promedio"):
        razones.append(f"costo histórico ${finops['costo_promedio']:.4f}")

    return {
        "employee_id": employee.id,
        "employee_code": employee.code,
        "employee_name": employee.name,
        "specialty": employee.specialty,
        "domain": domain,
        "score": round(total, 3),
        "factores": factores,
        "factors": factores,
        "pesos": FACTOR_WEIGHTS,
        "razon_seleccion": "; ".join(razones) if razones else f"mejor puntaje disponible para {domain}",
        "experiencia_consultada": exp.get("experiencias_consultadas", []),
        "finops": finops,
    }


def select_team(
    db: Session,
    org_id: str,
    request: str,
    available_data: list[str] | None = None,
    data_profiles: dict[str, Any] | None = None,
    contexto: dict | None = None,
    *,
    persist_log: bool = True,
    caso_origen_id: str | None = None,
) -> dict[str, Any]:
    """Selecciona equipo con roles: LIDER, COMPLEMENTARIO, VALIDADOR, DISIDENTE."""
    primary, secondary, problem_type = detect_primary_domain(request, available_data, data_profiles)
    all_domains = [primary] + [d for d in secondary if d != primary][:3]

    employees = (
        db.query(AIEmployee)
        .filter(
            AIEmployee.organization_id == org_id,
            AIEmployee.is_active.is_(True),
            AIEmployee.lifecycle_status.in_([
                EmployeeLifecycleStatus.ACTIVE,
                EmployeeLifecycleStatus.PUBLISHED,
            ]),
        )
        .all()
    )

    candidatos: list[dict[str, Any]] = []
    asignaciones: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_specialties: set[str] = set()

    for domain in all_domains:
        domain_scores = [
            score_candidate(db, org_id, emp, domain, problem_type, contexto, selected_specialties)
            for emp in employees
            if emp.id not in selected_ids
        ]
        domain_scores.sort(key=lambda x: x["score"], reverse=True)
        candidatos.extend(domain_scores[:5])

        if domain_scores and domain_scores[0]["score"] > 0.15:
            best = domain_scores[0]
            best["domain"] = domain
            asignaciones.append(best)
            selected_ids.add(best["employee_id"])
            selected_specialties.add(best.get("specialty") or "")

    if not asignaciones:
        fallback = [
            score_candidate(db, org_id, emp, primary, problem_type, contexto)
            for emp in employees
        ]
        fallback.sort(key=lambda x: x["score"], reverse=True)
        if fallback and fallback[0]["score"] > 0:
            asignaciones.append(fallback[0])
            candidatos.extend(fallback[:5])

    if not asignaciones:
        return {
            "dominios": all_domains,
            "dominio_principal": primary,
            "tipo_problema": problem_type,
            "asignaciones": [],
            "equipo": [],
            "lider": None,
            "consolidador": None,
            "validador": None,
            "disidente": None,
            "razon_seleccion_global": "Sin candidatos activos disponibles",
            "candidatos_evaluados": 0,
            "factores_pesos": FACTOR_WEIGHTS,
        }

    leader = _pick_leader(asignaciones, primary, problem_type)
    complementarios = [a for a in asignaciones if a["employee_id"] != leader["employee_id"]]

    validador = _pick_validator(
        db, org_id, employees, leader, complementarios, primary, problem_type, contexto,
    )
    disidente = _pick_dissident(
        db, org_id, employees, leader, complementarios, primary, problem_type, contexto,
    )

    roles: list[dict[str, Any]] = [
        {**leader, "rol": ROLE_LIDER, "razon_rol": _leader_reason(leader, primary, problem_type)},
    ]
    for c in complementarios[:3]:
        roles.append({**c, "rol": ROLE_COMPLEMENTARIO, "razon_rol": f"Apoyo en dominio {c.get('domain')}"})
    if validador:
        roles.append({**validador, "rol": ROLE_VALIDADOR, "razon_rol": validador.get("razon_rol", "Diversidad de criterio")})
    if disidente:
        roles.append({**disidente, "rol": ROLE_DISIDENTE, "razon_rol": disidente.get("razon_rol", "Postura alternativa")})

    consolidador = next(
        (r for r in roles if r.get("domain") == "estrategico" or r.get("rol") == ROLE_LIDER),
        leader,
    )
    if primary == "estrategico":
        consolidador = leader

    ordered_asignaciones = [leader] + [c for c in complementarios if c["employee_id"] != leader.get("employee_id")]

    razon_global = (
        f"Seleccionado {leader.get('employee_name')} como líder porque "
        f"{leader.get('razon_seleccion', 'mejor puntaje')} "
        f"en dominio principal '{primary}' (tipo: {problem_type})"
    )

    plan: dict[str, Any] = {
        "dominios": all_domains,
        "dominio_principal": primary,
        "tipo_problema": problem_type,
        "asignaciones": ordered_asignaciones,
        "equipo": roles,
        "lider": leader,
        "consolidador": consolidador,
        "validador": validador,
        "disidente": disidente,
        "razon_seleccion_global": razon_global,
        "candidatos_evaluados": len(candidatos),
        "factores_pesos": FACTOR_WEIGHTS,
    }

    if persist_log:
        log = ExperienceSelectionLog(
            organization_id=org_id,
            solicitud=request[:2000] if request else None,
            dominio_principal=primary,
            candidatos_json=json.dumps(candidatos[:15], ensure_ascii=False),
            factores_json=json.dumps(FACTOR_WEIGHTS, ensure_ascii=False),
            experiencia_consultada_json=json.dumps(
                [c.get("experiencia_consultada") for c in asignaciones], ensure_ascii=False,
            ),
            seleccionados_json=json.dumps(
                [
                    {"id": r.get("employee_id"), "nombre": r.get("employee_name"), "rol": r.get("rol")}
                    for r in roles if r.get("employee_id")
                ],
                ensure_ascii=False,
            ),
            roles_json=json.dumps(roles, ensure_ascii=False, default=str),
            razon_seleccion=razon_global,
            caso_origen_id=caso_origen_id,
        )
        db.add(log)
        db.flush()
        plan["selection_log_id"] = log.id

    return plan


def _pick_leader(asignaciones: list[dict], primary: str, problem_type: str) -> dict[str, Any]:
    for a in asignaciones:
        if a.get("domain") == primary:
            return a
    if problem_type == "datos_insuficientes":
        for a in asignaciones:
            if a.get("domain") == "estrategico" or "estratég" in (a.get("specialty") or "").lower():
                return a
    return asignaciones[0] if asignaciones else {}


def _leader_reason(leader: dict, primary: str, problem_type: str) -> str:
    if problem_type == "datos_insuficientes":
        return "Datos insuficientes — liderazgo estratégico/de datos, no cartera por defecto"
    return f"Líder por dominio principal '{primary}': {leader.get('razon_seleccion', '')}"


def _pick_validator(
    db: Session,
    org_id: str,
    employees: list[AIEmployee],
    leader: dict,
    complementarios: list[dict],
    primary: str,
    problem_type: str,
    contexto: dict | None,
) -> dict[str, Any] | None:
    leader_spec = (leader.get("specialty") or "").lower()
    high_impact = primary in ("estrategico", "glosas", "cartera") or len(complementarios) >= 2
    if not high_impact:
        return None

    candidates = []
    for emp in employees:
        if emp.id == leader.get("employee_id"):
            continue
        spec = (emp.specialty or "").lower()
        if spec == leader_spec:
            continue
        scored = score_candidate(db, org_id, emp, primary, problem_type, contexto)
        if scored["score"] > 0.25:
            scored["razon_rol"] = (
                f"Validador con especialidad diferente ({emp.specialty}) "
                f"para diversidad ante impacto en {primary}"
            )
            candidates.append(scored)

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0] if candidates else None


def _pick_dissident(
    db: Session,
    org_id: str,
    employees: list[AIEmployee],
    leader: dict,
    complementarios: list[dict],
    primary: str,
    problem_type: str,
    contexto: dict | None,
) -> dict[str, Any] | None:
    if len(complementarios) < 1:
        return None
    used_ids = {leader.get("employee_id")} | {c["employee_id"] for c in complementarios}
    alt_domain = "contratos" if primary == "cartera" else "cartera"
    candidates = []
    for emp in employees:
        if emp.id in used_ids:
            continue
        scored = score_candidate(db, org_id, emp, alt_domain, problem_type, contexto)
        if scored["score"] > 0.2:
            scored["razon_rol"] = f"Disidente con perspectiva {alt_domain} para contrastar hipótesis"
            candidates.append(scored)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0] if candidates else None
