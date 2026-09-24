"""MB-08 — Centro de Control operacional (capa de lectura/orquestación)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.enums import EmployeeLifecycleStatus
from app.llm_models import LlmInferenceLog, LlmProviderConfig
from app.models import User
from app.orchestration_models import (
    AIEmployee,
    ApprovalRequest,
    EmployeeBusinessCapability,
    EmployeeFactoryApproval,
    EmployeeModelPolicy,
    WorkPlan,
)
from app.permissions import user_permissions
from app.services import finops_service, operations_center
from app.services import consumption_planner_service as planner_svc

_LIFECYCLE_LABELS: dict[str, str] = {
    EmployeeLifecycleStatus.DRAFT: "Borrador",
    EmployeeLifecycleStatus.CONFIGURING: "En configuración",
    EmployeeLifecycleStatus.TESTING: "En prueba",
    EmployeeLifecycleStatus.FAILED_TEST: "Prueba fallida",
    EmployeeLifecycleStatus.CERTIFIED: "Certificado",
    EmployeeLifecycleStatus.PUBLISHED: "Publicado",
    EmployeeLifecycleStatus.ACTIVE: "Activo",
    EmployeeLifecycleStatus.PAUSED: "Pausado",
    EmployeeLifecycleStatus.RETIRED: "Retirado",
    "PENDING_APPROVAL": "Pendiente de aprobación",
}

_CAPABILITY_STATES = ("DISPONIBLE", "NO_DISPONIBLE", "EN_COLA", "ESPERANDO_APROBACION", "EN_EJECUCION", "FALLIDA")

_SEVERITY_WEIGHT = {"CRITICA": 4, "ALTA": 3, "MEDIA": 2, "BAJA": 1}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _period_start(periodo: str | None) -> datetime | None:
    now = _utcnow()
    if periodo == "7d":
        return now - timedelta(days=7)
    if periodo == "30d":
        return now - timedelta(days=30)
    if periodo == "mtd":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _has(permissions: set[str], code: str) -> bool:
    try:
        return code in permissions
    except Exception:
        return False


def _score_attention(item: dict[str, Any]) -> float:
    base = max(0, 21 - int(item.get("prioridad", 20)))
    sev = _SEVERITY_WEIGHT.get(str(item.get("severidad", "MEDIA")).upper(), 2)
    tipo_boost = {
        "ejecucion_fallida": 3,
        "aprobacion": 2,
        "empleado_error": 3,
        "proveedor_no_disponible": 3,
        "presupuesto_ia": 2,
        "automatizacion_fallida": 2,
    }.get(item.get("tipo", ""), 1)
    return base * sev * tipo_boost


def _enhance_attention(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for item in items:
        copy = dict(item)
        copy["impacto"] = copy.get("severidad", "MEDIA")
        copy["urgencia"] = "ALTA" if copy.get("tipo") in ("ejecucion_fallida", "empleado_error", "proveedor_no_disponible") else "MEDIA"
        copy["puntuacion"] = round(_score_attention(copy), 2)
        enriched.append(copy)
    enriched.sort(key=lambda x: (-x["puntuacion"], x.get("prioridad", 99)))
    return enriched


def _workforce_summary(db: Session, org_id: str, *, employee_id: str | None = None) -> dict[str, Any]:
    query = db.query(AIEmployee).filter(
        AIEmployee.organization_id == org_id,
        AIEmployee.is_template.is_(False),
    )
    if employee_id:
        query = query.filter(AIEmployee.id == employee_id)

    employees = query.order_by(AIEmployee.updated_at.desc()).limit(100).all()
    buckets: dict[str, int] = {k: 0 for k in _LIFECYCLE_LABELS}
    items: list[dict[str, Any]] = []

    for emp in employees:
        lc = emp.lifecycle_status or EmployeeLifecycleStatus.DRAFT
        buckets[lc] = buckets.get(lc, 0) + 1
        last_wp = (
            db.query(func.max(func.coalesce(WorkPlan.completed_at, WorkPlan.started_at, WorkPlan.created_at)))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.employee_id == emp.id)
            .scalar()
        )
        running = (
            db.query(func.count(WorkPlan.id))
            .filter(
                WorkPlan.organization_id == org_id,
                WorkPlan.employee_id == emp.id,
                WorkPlan.status.in_(["RUNNING", "PLANNING", "PARTIAL"]),
            )
            .scalar()
            or 0
        )
        policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first()
        provider = policy.preferred_provider if policy else emp.model_provider
        caps_count = (
            db.query(func.count(EmployeeBusinessCapability.id))
            .filter(EmployeeBusinessCapability.employee_id == emp.id, EmployeeBusinessCapability.is_active.is_(True))
            .scalar()
            or 0
        )
        items.append({
            "id": emp.id,
            "nombre": emp.name,
            "lifecycle_status": lc,
            "lifecycle_label": _LIFECYCLE_LABELS.get(lc, lc),
            "estado_operacional": emp.status,
            "autonomia": emp.autonomy_level,
            "origen": emp.source_type or "MANUAL",
            "es_plantilla": emp.is_template,
            "ultima_actividad": last_wp.isoformat() if last_wp else (emp.updated_at.isoformat() if emp.updated_at else None),
            "ejecuciones_activas": running,
            "proveedor": provider,
            "capacidades_declaradas": caps_count,
            "responsable_id": emp.owner_id,
            "enlace": f"/empleados/{emp.id}",
            "enlace_configuracion": f"/empleados/{emp.id}?tab=configuracion",
        })

    return {
        "total": len(employees),
        "activos": buckets.get(EmployeeLifecycleStatus.ACTIVE, 0),
        "en_prueba": buckets.get(EmployeeLifecycleStatus.TESTING, 0),
        "pausados": buckets.get(EmployeeLifecycleStatus.PAUSED, 0),
        "con_error": buckets.get(EmployeeLifecycleStatus.FAILED_TEST, 0),
        "pendientes_aprobacion": (
            db.query(func.count(EmployeeFactoryApproval.id))
            .filter(EmployeeFactoryApproval.organization_id == org_id, EmployeeFactoryApproval.status == "PENDING")
            .scalar()
            or 0
        ),
        "retirados": buckets.get(EmployeeLifecycleStatus.RETIRED, 0),
        "por_estado": {k: v for k, v in buckets.items() if v > 0},
        "items": items,
    }


def _executions_summary(
    db: Session,
    org_id: str,
    *,
    employee_id: str | None = None,
    proceso: str | None = None,
    estado: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    summary = operations_center.get_summary(db, org_id)
    items = operations_center.list_operations(
        db,
        org_id,
        employee_id=employee_id,
        proceso=proceso,
        status=estado,
        limit=limit,
    )
    return {
        "resumen": {
            "en_ejecucion": summary.get("running", 0),
            "pendientes": summary.get("pending", 0),
            "esperando_aprobacion": summary.get("approval", 0),
            "fallidas": summary.get("error", 0),
            "vencidas": summary.get("overdue", 0),
            "proximas_vencer": summary.get("due_soon", 0),
        },
        "items": [
            {
                "id": it["id"],
                "trabajo": it.get("trabajo"),
                "empleado": it.get("empleado_ia"),
                "employee_id": it.get("employee_id"),
                "estado": it.get("estado"),
                "estado_codigo": it.get("estado_codigo"),
                "progreso": it.get("progreso"),
                "aprobaciones_pendientes": it.get("aprobaciones_pendientes", 0),
                "ultima_actividad": it.get("ultima_actividad").isoformat() if it.get("ultima_actividad") else None,
                "correlation_id": it.get("correlation_id"),
                "acciones": it.get("acciones", ["ver"]),
                "enlace": f"/ejecuciones/{it['id']}",
            }
            for it in items
        ],
    }


def _capacity_summary(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    if not _has(permissions, "finops.view"):
        return {"disponible": False, "estado": "Sin permiso finops.view"}

    running = (
        db.query(func.count(WorkPlan.id))
        .filter(WorkPlan.organization_id == org_id, WorkPlan.status.in_(["RUNNING", "PARTIAL", "PLANNING"]))
        .scalar()
        or 0
    )
    try:
        contract = planner_svc.centro_control_contract(db, org_id)
        sim = planner_svc.simulate(db, org_id, {"active_employees": 25, "executions_per_day": 20, "days": 30})
        capacity_total = sim.get("capacity", {}).get("total_units")
        utilizacion = sim.get("capacity", {}).get("utilization_pct")
    except Exception:
        contract = {}
        capacity_total = None
        utilizacion = None

    saturacion = "NORMAL"
    if contract.get("capacidad_riesgo") in ("ALTO", "CRITICO", "HIGH", "CRITICAL"):
        saturacion = "SATURADA"
    elif running >= 10:
        saturacion = "ELEVADA"

    return {
        "disponible": True,
        "capacidad_disponible": capacity_total,
        "capacidad_utilizada": running,
        "concurrencia_activa": running,
        "cola_pendiente": (
            db.query(func.count(WorkPlan.id))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.status.in_(["CREATED", "READY", "PLANNING"]))
            .scalar()
            or 0
        ),
        "saturacion": saturacion,
        "proyeccion": contract.get("consumo_proyectado"),
        "riesgo_capacidad": contract.get("capacidad_riesgo"),
        "nota": "Capacidad derivada de ejecuciones y planificador — no solo del número de empleados",
    }


def _cost_operational(db: Session, org_id: str, permissions: set[str], *, period_start: datetime | None) -> dict[str, Any]:
    if not _has(permissions, "finops.view"):
        return {"disponible": False, "estado": "Sin permiso finops.view"}

    dash = finops_service.dashboard_summary(db, org_id, period_start=period_start, period_end=_utcnow())
    try:
        planner = planner_svc.centro_control_contract(db, org_id)
    except Exception:
        planner = {}

    return {
        "disponible": True,
        "estimado": {
            "consumo_proyectado": planner.get("consumo_proyectado"),
            "presupuesto_limite": planner.get("presupuesto_limite"),
            "utilizacion_pct": planner.get("presupuesto_utilizacion_pct"),
        },
        "real": {
            "costo_periodo": dash.get("total_cost"),
            "costo_label": dash.get("total_cost_label"),
            "ejecuciones": dash.get("execution_count"),
            "tokens": dash.get("tokens_total"),
        },
        "clasificacion": ["DIRECTO", "TRANSVERSAL_ATRIBUIBLE", "PLATAFORMA"],
        "nota": "Economía privada restringida por permisos — sin segundo motor FinOps",
    }


def _approvals_operational(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if _has(permissions, "operations.view"):
        for ap in (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.organization_id == org_id, ApprovalRequest.status == "PENDING")
            .order_by(ApprovalRequest.created_at.asc())
            .limit(20)
            .all()
        ):
            items.append({
                "id": ap.id,
                "tipo": "operaciones",
                "accion": ap.action,
                "desde": ap.created_at.isoformat() if ap.created_at else None,
                "contexto": ap.reason,
                "impacto": "EJECUCION",
                "enlace": "/aprobaciones",
                "gobierno_operacional": "FRONTERA_PREPARADA",
            })

    if _has(permissions, "employee.view"):
        for fa in (
            db.query(EmployeeFactoryApproval)
            .filter(EmployeeFactoryApproval.organization_id == org_id, EmployeeFactoryApproval.status == "PENDING")
            .order_by(EmployeeFactoryApproval.created_at.asc())
            .limit(20)
            .all()
        ):
            emp = db.query(AIEmployee).filter(AIEmployee.id == fa.employee_id).first()
            items.append({
                "id": fa.id,
                "tipo": "fabrica_empleado",
                "accion": fa.approval_kind,
                "empleado": emp.name if emp else fa.employee_id,
                "employee_id": fa.employee_id,
                "desde": fa.created_at.isoformat() if fa.created_at else None,
                "impacto": "PUBLICACION" if fa.approval_kind == "PUBLISH" else "CONFIGURACION",
                "enlace": f"/empleados/{fa.employee_id}?tab=aprobaciones",
                "gobierno_operacional": "FRONTERA_PREPARADA",
            })

    return {
        "total_pendientes": len(items),
        "items": items,
        "nota": "Integración Gobierno Operacional pendiente — sin motor paralelo",
    }


def _external_capabilities(db: Session, org_id: str) -> dict[str, Any]:
    caps = (
        db.query(EmployeeBusinessCapability)
        .filter(EmployeeBusinessCapability.organization_id == org_id, EmployeeBusinessCapability.is_active.is_(True))
        .limit(200)
        .all()
    )
    by_code: dict[str, dict[str, Any]] = {}
    for c in caps:
        entry = by_code.setdefault(c.code, {"codigo": c.code, "empleados": 0, "estado": "DISPONIBLE"})
        entry["empleados"] += 1
        if c.operation_class == "EJECUCION":
            entry["estado"] = "EN_EJECUCION"
    return {
        "disponible": True,
        "estados_canonicos": list(_CAPABILITY_STATES),
        "piiax_conectado": False,
        "nota": "PIIAX no conectado — EIAAX opera con estados declarados",
        "capacidades": list(by_code.values()),
    }


def _providers_operational(db: Session, org_id: str, permissions: set[str]) -> dict[str, Any]:
    if not _has(permissions, "llm.view"):
        return {"disponible": False, "estado": "Sin permiso llm.view"}

    since = _utcnow() - timedelta(hours=24)
    providers = db.query(LlmProviderConfig).filter(LlmProviderConfig.organization_id == org_id).all()
    items = []
    for p in providers:
        errors = (
            db.query(func.count(LlmInferenceLog.id))
            .filter(
                LlmInferenceLog.organization_id == org_id,
                LlmInferenceLog.provider == p.provider_type,
                LlmInferenceLog.status != "OK",
                LlmInferenceLog.created_at >= since,
            )
            .scalar()
            or 0
        )
        lat = (
            db.query(func.avg(LlmInferenceLog.latency_ms))
            .filter(
                LlmInferenceLog.organization_id == org_id,
                LlmInferenceLog.provider == p.provider_type,
                LlmInferenceLog.created_at >= since,
                LlmInferenceLog.latency_ms.isnot(None),
            )
            .scalar()
        )
        estado = "DISPONIBLE" if p.is_enabled and errors == 0 else ("DEGRADADO" if p.is_enabled else "NO_DISPONIBLE")
        items.append({
            "id": p.id,
            "nombre": p.name,
            "proveedor": p.provider_type,
            "modelo": p.model_default,
            "estado": estado,
            "errores_24h": errors,
            "latencia_promedio_ms": int(lat) if lat else None,
            "habilitado": p.is_enabled,
        })
    return {"disponible": True, "items": items}


def _results_frontier() -> dict[str, Any]:
    return {
        "integrado": False,
        "modulo": "inteligencia_resultados",
        "estados": ["ANTES", "PROYECTADO", "REAL"],
        "nota": "Frontera preparada para agente D — sin recalcular ROI en Centro de Control",
    }


def _dimensionamiento(db: Session, org_id: str) -> dict[str, Any]:
    since = _utcnow() - timedelta(days=30)
    plans = (
        db.query(WorkPlan)
        .filter(WorkPlan.organization_id == org_id, WorkPlan.created_at >= since)
        .all()
    )
    completed = [p for p in plans if p.status == "COMPLETED"]
    failed = [p for p in plans if p.status == "FAILED"]
    durations = []
    for p in completed:
        if p.started_at and p.completed_at:
            durations.append((p.completed_at - p.started_at).total_seconds())
    avg_duration = sum(durations) / len(durations) if durations else None
    return {
        "volumen_30d": len(plans),
        "completadas": len(completed),
        "fallidas": len(failed),
        "duracion_promedio_seg": round(avg_duration, 1) if avg_duration else None,
        "concurrencia_max_estimada": (
            db.query(func.count(WorkPlan.id))
            .filter(WorkPlan.organization_id == org_id, WorkPlan.status.in_(["RUNNING", "PARTIAL"]))
            .scalar()
            or 0
        ),
        "productividad_liberable": "Estimación pendiente de línea base",
        "redistribucion_posible": "Requiere Inteligencia de Resultados",
        "reduccion_personal_verificada": None,
        "nota": "No convertir métricas en reducción de personal sin evidencia",
    }


def _extra_attention(db: Session, org_id: str, permissions: set[str]) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    prio_base = 100

    if _has(permissions, "employee.view"):
        errores = (
            db.query(AIEmployee)
            .filter(
                AIEmployee.organization_id == org_id,
                AIEmployee.lifecycle_status == EmployeeLifecycleStatus.FAILED_TEST,
                AIEmployee.is_template.is_(False),
            )
            .limit(5)
            .all()
        )
        for emp in errores:
            prio_base += 1
            extra.append({
                "prioridad": prio_base,
                "tipo": "empleado_error",
                "severidad": "ALTA",
                "titulo": f"Empleado IA con error: {emp.name}",
                "enlace": f"/empleados/{emp.id}",
                "origen": "fabrica",
            })

        for fa in (
            db.query(EmployeeFactoryApproval, AIEmployee)
            .join(AIEmployee, AIEmployee.id == EmployeeFactoryApproval.employee_id)
            .filter(EmployeeFactoryApproval.organization_id == org_id, EmployeeFactoryApproval.status == "PENDING")
            .order_by(EmployeeFactoryApproval.created_at.asc())
            .limit(5)
            .all()
        ):
            approval, emp = fa
            prio_base += 1
            extra.append({
                "prioridad": prio_base,
                "tipo": "empleado_aprobacion",
                "severidad": "MEDIA",
                "titulo": f"Aprobación pendiente: {emp.name}",
                "enlace": f"/empleados/{emp.id}?tab=aprobaciones",
                "origen": "fabrica",
            })

        if _has(permissions, "llm.view"):
            for emp in db.query(AIEmployee).filter(AIEmployee.organization_id == org_id, AIEmployee.is_template.is_(False)).limit(30).all():
                policy = db.query(EmployeeModelPolicy).filter(EmployeeModelPolicy.employee_id == emp.id).first()
                provider = policy.preferred_provider if policy else emp.model_provider
                if not provider or provider == "rule-engine":
                    continue
                cfg = (
                    db.query(LlmProviderConfig)
                    .filter(
                        LlmProviderConfig.organization_id == org_id,
                        LlmProviderConfig.provider_type == provider,
                    )
                    .first()
                )
                if not cfg or not cfg.is_enabled:
                    prio_base += 1
                    extra.append({
                        "prioridad": prio_base,
                        "tipo": "proveedor_no_disponible",
                        "severidad": "ALTA",
                        "titulo": f"Proveedor no disponible para {emp.name}",
                        "detalle": provider,
                        "enlace": f"/empleados/{emp.id}",
                        "origen": "gateway",
                    })
                    break

    return extra


def get_operational_summary(
    db: Session,
    user: User,
    org_id: str,
    *,
    periodo: str | None = "mtd",
    employee_id: str | None = None,
    proceso: str | None = None,
    estado: str | None = None,
) -> dict[str, Any]:
    permissions = user_permissions(user, db)
    period_start = _period_start(periodo)
    now = _utcnow()

    from app.services.control_center_service import _atencion_requerida

    base_attention = _atencion_requerida(db, org_id, permissions)
    extra = _extra_attention(db, org_id, permissions)
    attention = _enhance_attention(base_attention + extra)

    workforce = _workforce_summary(db, org_id, employee_id=employee_id)
    executions = _executions_summary(db, org_id, employee_id=employee_id, proceso=proceso, estado=estado)
    capacity = _capacity_summary(db, org_id, permissions)
    cost = _cost_operational(db, org_id, permissions, period_start=period_start)

    return {
        "generated_at": now.isoformat(),
        "ultima_actualizacion": now.isoformat(),
        "modo_actualizacion": "bajo_demanda",
        "nota_tiempo_real": "Actualización bajo demanda — no es streaming en tiempo real",
        "organization_id": org_id,
        "filtros": {"periodo": periodo, "employee_id": employee_id, "proceso": proceso, "estado": estado},
        "resumen_operacional": {
            "empleados_activos": workforce["activos"],
            "ejecuciones_en_curso": executions["resumen"]["en_ejecucion"],
            "requiere_atencion": len(attention),
            "aprobaciones_pendientes": _approvals_operational(db, org_id, permissions)["total_pendientes"],
            "ejecuciones_fallidas": executions["resumen"]["fallidas"],
            "concurrencia": capacity.get("concurrencia_activa"),
        },
        "fuerza_laboral": workforce,
        "ejecuciones": executions,
        "capacidad": capacity,
        "costo": cost,
        "requiere_atencion": attention,
        "aprobaciones": _approvals_operational(db, org_id, permissions),
        "capacidades_externas": _external_capabilities(db, org_id),
        "proveedores": _providers_operational(db, org_id, permissions),
        "resultados_frontera": _results_frontier(),
        "dimensionamiento": _dimensionamiento(db, org_id),
        "gobierno_operacional": {
            "estado": "FRONTERA_PREPARADA",
            "integracion_pendiente": "GENERAL — Gobierno Operacional",
        },
        "acciones_permitidas": ["ver", "abrir_detalle", "reintentar", "pausar", "solicitar_aprobacion"],
        "acciones_restringidas": "Sin bypass de Gobierno Operacional — backend autoridad",
    }


def get_execution_operational_detail(db: Session, org_id: str, plan_id: str) -> dict[str, Any]:
    try:
        detail = operations_center.get_operation_detail(db, org_id, plan_id)
    except LookupError:
        return {"not_found": True, "mensaje": "Ejecución no encontrada"}

    plan = db.query(WorkPlan).filter(WorkPlan.id == plan_id, WorkPlan.organization_id == org_id).first()
    employee = db.query(AIEmployee).filter(AIEmployee.id == plan.employee_id).first() if plan and plan.employee_id else None

    return {
        "id": detail.get("id"),
        "empleado": employee.name if employee else detail.get("empleado_ia"),
        "employee_id": plan.employee_id if plan else None,
        "organizacion_id": org_id,
        "objetivo": detail.get("objective") or detail.get("trabajo"),
        "estado": detail.get("estado"),
        "estado_codigo": detail.get("estado_codigo"),
        "inicio": detail.get("inicio").isoformat() if detail.get("inicio") else None,
        "fin": plan.completed_at.isoformat() if plan and plan.completed_at else None,
        "correlation_id": detail.get("correlation_id"),
        "consumo": detail.get("costo_metadata"),
        "resultado": detail.get("resultado") or detail.get("summary"),
        "fallo": detail.get("error"),
        "aprobaciones_pendientes": detail.get("aprobaciones_pendientes", 0),
        "acciones": detail.get("acciones", ["ver"]),
        "enlace_empleado": f"/empleados/{plan.employee_id}" if plan and plan.employee_id else None,
        "nota": "Sin prompts ni credenciales en detalle operacional",
    }
