"""Servicio — Empleado IA 2.0 (ficha, supervisión, evaluación, aprendizaje)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.employee_20_constants import (
    LEARNING_PROPOSAL_STATES,
    SUPERVISION_EVENT_TYPES,
    default_autonomy_for_employee,
    mission_phase_for_employee,
)
from app.employee_20_models import (
    EmployeeLaborProfile,
    EmployeeLearningProposal,
    EmployeePerformanceIndicator,
    EmployeeResultLink,
    EmployeeSupervisionLog,
)
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    EmployeeTask,
    EmployeeVersion,
    FinOpsRecord,
    WorkPlan,
)
from app.services import agent_factory
from app.services.employee_20_autonomy import resolve_autonomy_level


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_loads(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default if default is not None else []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default if default is not None else []


def _json_dumps(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def _get_employee(db: Session, org_id: str, employee_id: str) -> AIEmployee | None:
    return (
        db.query(AIEmployee)
        .filter(AIEmployee.id == employee_id, AIEmployee.organization_id == org_id)
        .first()
    )


def _get_or_create_profile(db: Session, org_id: str, employee: AIEmployee) -> EmployeeLaborProfile:
    row = (
        db.query(EmployeeLaborProfile)
        .filter(
            EmployeeLaborProfile.organization_id == org_id,
            EmployeeLaborProfile.employee_id == employee.id,
        )
        .first()
    )
    if row:
        return row
    row = EmployeeLaborProfile(
        organization_id=org_id,
        employee_id=employee.id,
        autonomy_level=default_autonomy_for_employee(
            maturity=employee.maturity, shadow_mode=employee.shadow_mode
        ),
    )
    db.add(row)
    db.flush()
    return row


def build_ficha_laboral(db: Session, org_id: str, employee_id: str) -> dict[str, Any] | None:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        return None
    snapshot = agent_factory._employee_config_snapshot(db, emp)
    profile = _get_or_create_profile(db, org_id, emp)
    versions = (
        db.query(EmployeeVersion)
        .filter(EmployeeVersion.employee_id == emp.id)
        .order_by(EmployeeVersion.version.desc())
        .limit(5)
        .all()
    )
    return {
        "employee_id": emp.id,
        "codigo": emp.code,
        "nombre": emp.name,
        "cargo": profile.cargo or emp.role,
        "mision": profile.mision or emp.objective,
        "objetivo": emp.objective,
        "funciones": _json_loads(profile.funciones_json),
        "responsabilidades": _json_loads(profile.responsabilidades_json),
        "capacidades": snapshot.get("capabilities", []),
        "herramientas_autorizadas": snapshot.get("tools", []),
        "conocimiento": snapshot.get("knowledge", []),
        "procesos": _json_loads(profile.procesos_json),
        "empresa": profile.empresa_ref,
        "supervisor_user_id": profile.supervisor_user_id,
        "limites": _json_loads(profile.limites_json) or snapshot.get("limits"),
        "horario": _json_loads(profile.horario_json),
        "autonomia": resolve_autonomy_level(db, org_id, emp),
        "indicadores": _json_loads(profile.indicadores_json),
        "criterios_exito": _json_loads(profile.criterios_exito_json),
        "criterios_escalamiento": _json_loads(profile.criterios_escalamiento_json),
        "ciclo_vida": {
            "lifecycle_status": emp.lifecycle_status,
            "fase_mision": mission_phase_for_employee(
                emp.lifecycle_status, shadow_mode=emp.shadow_mode
            ),
            "maturity": emp.maturity,
            "shadow_mode": emp.shadow_mode,
            "version": emp.version,
            "historial_versiones": [
                {"version": v.version, "status": v.status, "created_at": v.created_at.isoformat()}
                for v in versions
            ],
        },
        "modelo": snapshot.get("model_policy"),
        "instrucciones": snapshot.get("instructions"),
    }


def upsert_ficha_laboral(
    db: Session,
    org_id: str,
    employee_id: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    profile = _get_or_create_profile(db, org_id, emp)
    for field, attr in (
        ("cargo", "cargo"),
        ("mision", "mision"),
        ("empresa", "empresa_ref"),
        ("supervisor_user_id", "supervisor_user_id"),
        ("autonomia", "autonomy_level"),
    ):
        if field in data and data[field] is not None:
            setattr(profile, attr, data[field])
    for field, attr in (
        ("funciones", "funciones_json"),
        ("responsabilidades", "responsabilidades_json"),
        ("procesos", "procesos_json"),
        ("limites", "limites_json"),
        ("horario", "horario_json"),
        ("indicadores", "indicadores_json"),
        ("criterios_exito", "criterios_exito_json"),
        ("criterios_escalamiento", "criterios_escalamiento_json"),
    ):
        if field in data:
            setattr(profile, attr, _json_dumps(data[field]))
    profile.updated_at = _utcnow()
    db.flush()
    return build_ficha_laboral(db, org_id, employee_id) or {}


def record_supervision(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    event_type: str,
    descripcion: str | None = None,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    metricas: dict | None = None,
    calidad_score: float | None = None,
    duracion_ms: int | None = None,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    event_type = event_type.upper()
    if event_type not in SUPERVISION_EVENT_TYPES:
        raise ValueError(f"Tipo de supervisión no válido: {event_type}")
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    row = EmployeeSupervisionLog(
        organization_id=org_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        event_type=event_type,
        descripcion=descripcion,
        metricas_json=_json_dumps(metricas),
        calidad_score=calidad_score,
        duracion_ms=duracion_ms,
        actor_user_id=actor_user_id,
    )
    db.add(row)
    db.flush()
    return supervision_log_to_dict(row)


def supervision_log_to_dict(row: EmployeeSupervisionLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "event_type": row.event_type,
        "descripcion": row.descripcion,
        "work_plan_id": row.work_plan_id,
        "task_id": row.task_id,
        "metricas": _json_loads(row.metricas_json, {}),
        "calidad_score": row.calidad_score,
        "duracion_ms": row.duracion_ms,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_supervision(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = (
        db.query(EmployeeSupervisionLog)
        .filter(
            EmployeeSupervisionLog.organization_id == org_id,
            EmployeeSupervisionLog.employee_id == employee_id,
        )
        .order_by(EmployeeSupervisionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [supervision_log_to_dict(r) for r in rows]


def supervision_summary(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    base_q = db.query(EmployeeSupervisionLog).filter(
        EmployeeSupervisionLog.organization_id == org_id,
        EmployeeSupervisionLog.employee_id == employee_id,
    )
    total = base_q.count()
    errores = base_q.filter(EmployeeSupervisionLog.event_type == "ERROR").count()
    intervenciones = base_q.filter(
        EmployeeSupervisionLog.event_type.in_(("INTERVENCION_HUMANA", "ESCALAMIENTO", "APROBACION"))
    ).count()
    completados = base_q.filter(EmployeeSupervisionLog.event_type == "TRABAJO_COMPLETADO").count()
    avg_calidad = (
        db.query(func.avg(EmployeeSupervisionLog.calidad_score))
        .filter(
            EmployeeSupervisionLog.organization_id == org_id,
            EmployeeSupervisionLog.employee_id == employee_id,
            EmployeeSupervisionLog.calidad_score.isnot(None),
        )
        .scalar()
    )
    return {
        "total_eventos": total,
        "trabajos_completados": completados,
        "errores": errores,
        "intervenciones_humanas": intervenciones,
        "calidad_promedio": float(avg_calidad) if avg_calidad is not None else None,
    }


def upsert_performance_indicator(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    codigo: str,
    nombre: str,
    unidad: str = "%",
    valor_esperado: float | None = None,
    valor_real: float | None = None,
    periodo: str | None = None,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    row = (
        db.query(EmployeePerformanceIndicator)
        .filter(
            EmployeePerformanceIndicator.organization_id == org_id,
            EmployeePerformanceIndicator.employee_id == employee_id,
            EmployeePerformanceIndicator.codigo == codigo,
        )
        .first()
    )
    alerta = _detect_alert(valor_esperado, valor_real)
    if not row:
        row = EmployeePerformanceIndicator(
            organization_id=org_id,
            employee_id=employee_id,
            codigo=codigo,
            nombre=nombre,
            unidad=unidad,
            valor_esperado=valor_esperado,
            valor_real=valor_real,
            periodo=periodo,
            alerta=alerta,
        )
        db.add(row)
    else:
        row.nombre = nombre
        row.unidad = unidad
        row.valor_esperado = valor_esperado
        row.valor_real = valor_real
        row.periodo = periodo
        row.alerta = alerta
        row.updated_at = _utcnow()
    db.flush()
    return indicator_to_dict(row)


def _detect_alert(esperado: float | None, real: float | None) -> str | None:
    if esperado is None or real is None:
        return None
    if real < esperado * 0.7:
        return "BAJO_RENDIMIENTO"
    if real > esperado * 1.5:
        return "CONSUMO_ANOMALO"
    return None


def indicator_to_dict(row: EmployeePerformanceIndicator) -> dict[str, Any]:
    return {
        "id": row.id,
        "codigo": row.codigo,
        "nombre": row.nombre,
        "unidad": row.unidad,
        "valor_esperado": row.valor_esperado,
        "valor_real": row.valor_real,
        "periodo": row.periodo,
        "alerta": row.alerta,
        "brecha": (
            (row.valor_real - row.valor_esperado) if row.valor_real is not None and row.valor_esperado is not None else None
        ),
    }


def evaluate_employee(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    """Evaluación determinística esperado vs real + señales operativas."""
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    indicators = (
        db.query(EmployeePerformanceIndicator)
        .filter(
            EmployeePerformanceIndicator.organization_id == org_id,
            EmployeePerformanceIndicator.employee_id == employee_id,
        )
        .all()
    )
    sup = supervision_summary(db, org_id, employee_id)
    findings: list[str] = []
    if sup["errores"] >= 3:
        findings.append("ERRORES_REPETIDOS")
    if sup["intervenciones_humanas"] >= 5:
        findings.append("INTERVENCION_HUMANA_EXCESIVA")
    for ind in indicators:
        if ind.alerta == "BAJO_RENDIMIENTO":
            findings.append(f"BAJO_RENDIMIENTO:{ind.codigo}")
        if ind.alerta == "CONSUMO_ANOMALO":
            findings.append(f"CONSUMO_ANOMALO:{ind.codigo}")

    cost_total = (
        db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0.0))
        .filter(FinOpsRecord.organization_id == org_id, FinOpsRecord.employee_id == employee_id)
        .scalar()
    ) or 0.0

    pending_approvals = (
        db.query(ApprovalRequest)
        .join(WorkPlan, WorkPlan.id == ApprovalRequest.work_plan_id)
        .join(EmployeeTask, EmployeeTask.work_plan_id == WorkPlan.id)
        .filter(
            ApprovalRequest.organization_id == org_id,
            EmployeeTask.employee_id == employee_id,
            ApprovalRequest.status == "PENDING",
        )
        .count()
    )

    return {
        "employee_id": employee_id,
        "indicadores": [indicator_to_dict(i) for i in indicators],
        "supervision": sup,
        "costo_acumulado": float(cost_total),
        "aprobaciones_pendientes": pending_approvals,
        "hallazgos": findings,
        "autonomia": resolve_autonomy_level(db, org_id, emp),
    }


def create_learning_proposal(
    db: Session,
    org_id: str,
    employee_id: str,
    user_id: str,
    *,
    observacion: str,
    propuesta: str,
    causa_probable: str | None = None,
    evidencia: dict | None = None,
    impacto_esperado: str | None = None,
) -> dict[str, Any]:
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    row = EmployeeLearningProposal(
        organization_id=org_id,
        employee_id=employee_id,
        estado="PROPUESTA",
        observacion=observacion,
        causa_probable=causa_probable,
        propuesta=propuesta,
        evidencia_json=_json_dumps(evidencia),
        impacto_esperado=impacto_esperado,
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    return learning_to_dict(row)


def decide_learning_proposal(
    db: Session,
    org_id: str,
    proposal_id: str,
    user_id: str,
    *,
    aprobar: bool,
    notas: str | None = None,
) -> dict[str, Any]:
    row = (
        db.query(EmployeeLearningProposal)
        .filter(
            EmployeeLearningProposal.id == proposal_id,
            EmployeeLearningProposal.organization_id == org_id,
        )
        .first()
    )
    if not row:
        raise LookupError("Propuesta no encontrada.")
    if row.estado not in ("PROPUESTA", "OBSERVACION"):
        raise ValueError("La propuesta ya fue decidida.")
    emp = _get_employee(db, org_id, row.employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    now = _utcnow()
    if aprobar:
        row.estado = "APROBADA"
        row.aprobado_por = user_id
        row.aprobado_at = now
        row.target_version = emp.version + 1
        # NO autoeditar configuración productiva — queda para prueba/promoción manual
        row.estado = "EN_PRUEBA"
    else:
        row.estado = "RECHAZADA"
        row.aprobado_por = user_id
        row.aprobado_at = now
    if notas:
        row.impacto_esperado = (row.impacto_esperado or "") + f"\n[Decisión] {notas}"
    row.updated_at = now
    db.flush()
    return learning_to_dict(row)


def learning_to_dict(row: EmployeeLearningProposal) -> dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "estado": row.estado,
        "observacion": row.observacion,
        "causa_probable": row.causa_probable,
        "propuesta": row.propuesta,
        "evidencia": _json_loads(row.evidencia_json, {}),
        "impacto_esperado": row.impacto_esperado,
        "target_version": row.target_version,
        "aprobado_at": row.aprobado_at.isoformat() if row.aprobado_at else None,
        "nota": "No se modifica configuración productiva sin prueba y promoción explícita.",
    }


def list_learning_proposals(
    db: Session, org_id: str, employee_id: str
) -> list[dict[str, Any]]:
    rows = (
        db.query(EmployeeLearningProposal)
        .filter(
            EmployeeLearningProposal.organization_id == org_id,
            EmployeeLearningProposal.employee_id == employee_id,
        )
        .order_by(EmployeeLearningProposal.created_at.desc())
        .all()
    )
    return [learning_to_dict(r) for r in rows]


def link_result(
    db: Session,
    org_id: str,
    employee_id: str,
    *,
    work_plan_id: str | None = None,
    task_id: str | None = None,
    resultado_ref: str | None = None,
    indicador_codigo: str | None = None,
    valor_ref: float | None = None,
    valor_economico_ref: str | None = None,
    notas: str | None = None,
) -> dict[str, Any]:
    """Contrato empleado→resultado→indicador (valor económico = referencia externa motor B)."""
    emp = _get_employee(db, org_id, employee_id)
    if not emp:
        raise LookupError("Empleado no encontrado.")
    row = EmployeeResultLink(
        organization_id=org_id,
        employee_id=employee_id,
        work_plan_id=work_plan_id,
        task_id=task_id,
        resultado_ref=resultado_ref,
        indicador_codigo=indicador_codigo,
        valor_ref=valor_ref,
        valor_economico_ref=valor_economico_ref,
        notas=notas,
    )
    db.add(row)
    db.flush()
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "work_plan_id": row.work_plan_id,
        "task_id": row.task_id,
        "resultado_ref": row.resultado_ref,
        "indicador_codigo": row.indicador_codigo,
        "valor_ref": row.valor_ref,
        "valor_economico_ref": row.valor_economico_ref,
        "contrato": "employee_20_results_v1",
        "nota": "Valor económico provisto por motor B — no duplicado aquí.",
    }


def results_contract(db: Session, org_id: str, employee_id: str) -> dict[str, Any]:
    links = (
        db.query(EmployeeResultLink)
        .filter(
            EmployeeResultLink.organization_id == org_id,
            EmployeeResultLink.employee_id == employee_id,
        )
        .order_by(EmployeeResultLink.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        "employee_id": employee_id,
        "contrato": "employee_20_results_v1",
        "esquema": {
            "empleado_id": "string",
            "work_plan_id": "string?",
            "task_id": "string?",
            "resultado_ref": "string?",
            "indicador_codigo": "string?",
            "valor_ref": "number?",
            "valor_economico_ref": "ref motor B",
        },
        "enlaces": [
            {
                "id": l.id,
                "work_plan_id": l.work_plan_id,
                "task_id": l.task_id,
                "resultado_ref": l.resultado_ref,
                "indicador_codigo": l.indicador_codigo,
                "valor_ref": l.valor_ref,
                "valor_economico_ref": l.valor_economico_ref,
            }
            for l in links
        ],
    }
