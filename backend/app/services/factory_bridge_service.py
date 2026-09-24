"""MB-06 — Puente Arquitecto de Transformación ↔ Fábrica de Empleados IA."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.enums import EmployeeLifecycleStatus, RiskLevel
from app.orchestration_models import (
    AIEmployee,
    BUSINESS_CAPABILITY_CODES,
    EmployeeBusinessCapability,
    EmployeeInstructions,
    EmployeeLimits,
    EmployeeModelPolicy,
    OPERATION_CLASSES,
)
from app.services import agent_factory
from app.services import consumption_planner_service as planner_svc
from app.services import employee_lifecycle_service as lifecycle_svc
from app.transformacion_models import EmpleadoIARequerimiento

_AUTONOMY_LEVELS = frozenset({"ASISTIDO", "SUPERVISADO", "AUTONOMO_LIMITADO"})
_SOURCE_TYPES = frozenset({"MANUAL", "ARQUITECTO", "OPORTUNIDAD", "PROCESO", "OPERACIONAL", "PLANTILLA_CLON"})

_CAPABILITY_DEFAULTS: dict[str, tuple[str, str]] = {
    "conocimiento": ("CONSULTAR_DATOS", "LECTURA"),
    "operaciones": ("EJECUTAR_PROCESO", "EJECUCION"),
    "notificaciones": ("NOTIFICAR", "PROPUESTA"),
    "documentos": ("OBTENER_DOCUMENTO", "LECTURA"),
    "analisis": ("ANALIZAR", "ANALISIS"),
}


def _map_risk(riesgo: str) -> str:
    m = {"BAJO": RiskLevel.LOW, "MEDIO": RiskLevel.MEDIUM, "ALTO": RiskLevel.HIGH}
    return m.get(riesgo.upper(), RiskLevel.MEDIUM)


def _infer_autonomy(supervision: str | None, riesgo: str) -> str:
    if supervision and "humana" in supervision.lower():
        return "SUPERVISADO"
    if riesgo.upper() == "ALTO":
        return "ASISTIDO"
    return "SUPERVISADO"


def list_requerimientos_pendientes(db: Session, org_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(EmpleadoIARequerimiento)
        .filter(
            EmpleadoIARequerimiento.organization_id == org_id,
            EmpleadoIARequerimiento.estado == "PENDIENTE",
        )
        .order_by(EmpleadoIARequerimiento.created_at.desc())
        .all()
    )
    return [_req_dict(r) for r in rows]


def _req_dict(r: EmpleadoIARequerimiento) -> dict[str, Any]:
    return {
        "id": r.id,
        "dossier_id": r.dossier_id,
        "objetivo": r.objetivo,
        "responsabilidad": r.responsabilidad,
        "frecuencia": r.frecuencia,
        "riesgo": r.riesgo,
        "supervision": r.supervision,
        "confianza": r.confianza,
        "estado": r.estado,
        "employee_id": r.employee_id,
        "entradas": _json_loads(r.entradas_json, []),
        "salidas": _json_loads(r.salidas_json, []),
        "herramientas": _json_loads(r.herramientas_json, []),
    }


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def create_employee_from_requerimiento(
    db: Session,
    org_id: str,
    user_id: str,
    requerimiento_id: str,
    *,
    template_code: str | None = "asistente-operativo",
) -> dict[str, Any]:
    req = (
        db.query(EmpleadoIARequerimiento)
        .filter(
            EmpleadoIARequerimiento.id == requerimiento_id,
            EmpleadoIARequerimiento.organization_id == org_id,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requerimiento no encontrado")
    if req.estado == "CONSUMIDO" and req.employee_id:
        detail = agent_factory.get_employee_detail(db, org_id, req.employee_id)
        if detail:
            return {"employee": detail, "requerimiento": _req_dict(req), "reused": True}

    name = f"Empleado IA — {req.objetivo[:60]}"
    autonomy = _infer_autonomy(req.supervision, req.riesgo)
    emp_data = agent_factory.create_employee(
        db,
        org_id,
        user_id,
        name=name,
        specialty="TRANSFORMACION",
        role=req.responsabilidad or "Asistente de transformación",
        objective=req.objetivo,
        template_code=template_code,
    )
    emp_id = emp_data["id"]
    emp = db.query(AIEmployee).filter(AIEmployee.id == emp_id).one()
    emp.source_type = "ARQUITECTO"
    emp.source_ref = requerimiento_id
    emp.requerimiento_id = requerimiento_id
    emp.dossier_id = req.dossier_id
    emp.autonomy_level = autonomy
    emp.risk_level = _map_risk(req.riesgo)

    instructions = db.query(EmployeeInstructions).filter(EmployeeInstructions.employee_id == emp_id).first()
    if instructions:
        instructions.objective_text = req.objetivo
        instructions.role_text = req.responsabilidad
        instructions.operating_rules = req.supervision
        entradas = _json_loads(req.entradas_json, [])
        salidas = _json_loads(req.salidas_json, [])
        if entradas or salidas:
            instructions.context_notes = json.dumps(
                {"entradas": entradas, "salidas": salidas, "indicadores": _json_loads(req.indicadores_json, [])},
                ensure_ascii=False,
            )

    herramientas = _json_loads(req.herramientas_json, [])
    for h in herramientas:
        key = str(h).lower()
        for token, (code, op_class) in _CAPABILITY_DEFAULTS.items():
            if token in key or code.lower() in key:
                _add_business_capability(db, org_id, emp_id, code, code.replace("_", " ").title(), op_class)
                break
        else:
            _add_business_capability(db, org_id, emp_id, "ANALIZAR", str(h), "ANALISIS")

    if not herramientas:
        _add_business_capability(db, org_id, emp_id, "ANALIZAR", "Análisis asistido", "ANALISIS")
        _add_business_capability(db, org_id, emp_id, "GENERAR_INFORME", "Generar informe", "PROPUESTA")

    req.employee_id = emp_id
    req.estado = "CONSUMIDO"
    db.flush()

    detail = agent_factory.get_employee_detail(db, org_id, emp_id) or emp_data
    detail["source_type"] = emp.source_type
    detail["autonomy_level"] = emp.autonomy_level
    detail["requerimiento_id"] = requerimiento_id
    return {
        "employee": detail,
        "requerimiento": _req_dict(req),
        "trazabilidad": {
            "origen": "ARQUITECTO",
            "dossier_id": req.dossier_id,
            "alternativa_id": req.alternativa_id,
            "iniciativa_id": req.iniciativa_id,
        },
    }


def _add_business_capability(
    db: Session,
    org_id: str,
    employee_id: str,
    code: str,
    label: str,
    operation_class: str,
) -> None:
    if code not in BUSINESS_CAPABILITY_CODES:
        code = "ANALIZAR"
    if operation_class not in OPERATION_CLASSES:
        operation_class = "LECTURA"
    existing = (
        db.query(EmployeeBusinessCapability)
        .filter(EmployeeBusinessCapability.employee_id == employee_id, EmployeeBusinessCapability.code == code)
        .first()
    )
    if existing:
        return
    db.add(
        EmployeeBusinessCapability(
            organization_id=org_id,
            employee_id=employee_id,
            code=code,
            label=label,
            operation_class=operation_class,
        )
    )


def clone_employee_as_draft(db: Session, org_id: str, user_id: str, employee_id: str) -> dict[str, Any]:
    source = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    detail = agent_factory.get_employee_detail(db, org_id, employee_id) or {}
    created = agent_factory.create_employee(
        db,
        org_id,
        user_id,
        name=f"{source.name} (copia)",
        specialty=source.specialty,
        role=source.role,
        objective=source.objective,
    )
    new_id = created["id"]
    new_emp = db.query(AIEmployee).filter(AIEmployee.id == new_id).one()
    new_emp.source_type = "PLANTILLA_CLON"
    new_emp.source_ref = employee_id
    new_emp.autonomy_level = source.autonomy_level
    new_emp.risk_level = source.risk_level

    update_payload: dict[str, Any] = {}
    if detail.get("capabilities"):
        update_payload["capability_ids"] = [c["id"] for c in detail.get("capabilities", []) if c.get("id")]
    if detail.get("tools"):
        update_payload["tools"] = [
            {"tool_id": t["id"], "permission": t.get("permission", "ALLOW")}
            for t in detail.get("tools", [])
            if t.get("id")
        ]
    mp = detail.get("model_policy") or {}
    if mp:
        update_payload["model_policy"] = {
            "preferred_provider": mp.get("provider") or mp.get("preferred_provider"),
            "preferred_model": mp.get("model") or mp.get("preferred_model"),
        }
    if detail.get("instructions"):
        update_payload["instructions"] = detail.get("instructions")
    if detail.get("limits"):
        update_payload["limits"] = detail.get("limits")
    if update_payload:
        agent_factory.update_employee(db, org_id, user_id, new_id, update_payload)
    caps = db.query(EmployeeBusinessCapability).filter(EmployeeBusinessCapability.employee_id == employee_id).all()
    for c in caps:
        _add_business_capability(db, org_id, new_id, c.code, c.label, c.operation_class)

    new_emp.lifecycle_status = EmployeeLifecycleStatus.DRAFT
    db.flush()

    result = agent_factory.get_employee_detail(db, org_id, new_id) or created
    if isinstance(result, dict):
        result["source_type"] = new_emp.source_type
    return result


def list_biblioteca(
    db: Session,
    org_id: str,
    *,
    q: str | None = None,
    lifecycle_status: str | None = None,
    source_type: str | None = None,
    include_templates: bool = True,
) -> dict[str, Any]:
    query = db.query(AIEmployee).filter(AIEmployee.organization_id == org_id)
    if lifecycle_status:
        query = query.filter(AIEmployee.lifecycle_status == lifecycle_status)
    if source_type:
        query = query.filter(AIEmployee.source_type == source_type)
    if not include_templates:
        query = query.filter(AIEmployee.is_template.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter((AIEmployee.name.ilike(like)) | (AIEmployee.code.ilike(like)))
    rows = query.order_by(AIEmployee.updated_at.desc()).all()
    items = []
    for e in rows:
        items.append({
            "id": e.id,
            "code": e.code,
            "name": e.name,
            "specialty": e.specialty,
            "lifecycle_status": e.lifecycle_status,
            "lifecycle_phase": lifecycle_svc.lifecycle_phase(e.lifecycle_status),
            "source_type": e.source_type or "MANUAL",
            "autonomy_level": e.autonomy_level,
            "is_template": e.is_template,
            "version": e.version,
            "is_active": e.is_active,
        })
    return {"items": items, "total": len(items)}


def estimate_capacity_cost(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    try:
        detail = planner_svc.employee_cost_detail(db, org_id, employee_id)
    except Exception:
        detail = {"estimado": False, "mensaje": "Sin base suficiente para estimación FinOps"}
    policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == employee_id).first()
    limits = db.query(EmployeeLimits).filter(EmployeeLimits.employee_id == employee_id).first()
    return {
        "employee_id": employee_id,
        "frecuencia_estimada": "Según configuración operativa",
        "modelo": {
            "provider": policy.preferred_provider if policy else emp.model_provider,
            "model": policy.preferred_model if policy else emp.model_name,
        },
        "limites": {
            "daily_cost_limit": float(limits.daily_cost_limit) if limits and limits.daily_cost_limit else None,
            "task_cost_limit": float(limits.task_cost_limit) if limits and limits.task_cost_limit else None,
        },
        "finops": detail,
        "advertencia": "Estimación proyectada — consumo real puede variar",
        "confianza": "MEDIA" if detail.get("estimado", True) else "BAJA",
    }


def gobierno_operacional_boundary(db: Session | None = None, org_id: str | None = None) -> dict[str, Any]:
    """Adaptador frontera hacia Gobierno Operacional (rama A) — sin motor paralelo."""
    return {
        "modulo": "gobierno_operacional_adapter",
        "estado": "FRONTERA_PREPARADA",
        "clasificacion_operaciones": list(OPERATION_CLASSES),
        "descripcion": "Las operaciones del empleado se clasifican LECTURA/ANÁLISIS/PROPUESTA/EJECUCIÓN para integración con aprobaciones transversales.",
        "integracion_pendiente": "GENERAL — Gobierno Operacional",
        "aprobaciones_actuales": "EmployeeFactoryApproval + ApprovalRequest (existente)",
    }


def validate_provider_for_test(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    """Valida proveedor/modelo antes de prueba — falla controlada si no disponible."""
    emp = db.query(AIEmployee).filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == employee_id).first()
    provider = policy.preferred_provider if policy else emp.model_provider or "rule-engine"
    if provider == "rule-engine":
        return {"valid": True, "provider": provider, "modo": "deterministico"}
    from app.llm_models import LlmProviderConfig
    cfg = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.organization_id == org_id, LlmProviderConfig.provider_type == provider)
        .first()
    )
    if not cfg or not cfg.is_enabled:
        return {
            "valid": False,
            "provider": provider,
            "error": f"Proveedor '{provider}' no configurado o inactivo",
            "puede_activar": False,
        }
    return {"valid": True, "provider": provider, "model": policy.preferred_model if policy else None}
