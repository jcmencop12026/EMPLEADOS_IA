"""API — Auditor determinístico de Empleados IA."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.employee_audit_models import EmployeeAuditFinding, EmployeeAuditRun
from app.models import User
from app.permissions import check_permission, require_permission
from app.services.employee_audit_service import (
    centro_control_resumen,
    execute_audit,
    get_or_create_org_policy,
    list_health,
    list_trabajo_contract,
    policy_to_dict,
    run_to_dict,
    update_org_policy,
    finding_to_dict,
)

router = APIRouter(prefix="/api/empleados-auditor", tags=["Auditor Empleados IA"])


@router.get("/politicas")
def list_policies(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.employee_audit_service import resolve_organization_id
    from app.employee_audit_models import EmployeeAuditPolicy

    org_id = resolve_organization_id(db, user, organization_id)
    rows = db.query(EmployeeAuditPolicy).filter(EmployeeAuditPolicy.organization_id == org_id).all()
    if not rows:
        rows = [get_or_create_org_policy(db, org_id)]
        db.commit()
    return [policy_to_dict(r) for r in rows]


@router.get("/politica")
def get_policy(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    row = get_or_create_org_policy(db, org_id)
    db.commit()
    return policy_to_dict(row)


@router.patch("/politica")
def patch_policy(
    body: dict,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.configure")),
):
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    row = update_org_policy(db, org_id, body)
    db.commit()
    return policy_to_dict(row)


@router.post("/ejecutar")
def ejecutar_auditoria(
    body: dict | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.execute")),
):
    payload = body or {}
    try:
        result = execute_audit(
            db,
            user,
            organization_id=payload.get("organization_id"),
            employee_id=payload.get("employee_id"),
            employee_ids=payload.get("employee_ids"),
            scope=payload.get("scope") or "ACTIVE",
            trigger_type="MANUAL",
            trigger_ref=payload.get("trigger_ref"),
        )
        if result.get("status") == "SKIPPED":
            return result
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/auditorias")
def list_auditorias(
    organization_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    runs = (
        db.query(EmployeeAuditRun)
        .filter(EmployeeAuditRun.organization_id == org_id)
        .order_by(EmployeeAuditRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [run_to_dict(db, r) for r in runs]


@router.get("/auditorias/{run_id}")
def get_auditoria(
    run_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    run = db.query(EmployeeAuditRun).filter(EmployeeAuditRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    check_permission(user, "auditor_empleados.view", db)
    if run.organization_id != user.organization_id:
        from app.permissions import user_permissions

        if "platform.organization.view" not in user_permissions(user, db):
            raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return run_to_dict(db, run)


@router.get("/hallazgos")
def list_hallazgos(
    organization_id: str | None = Query(None),
    employee_id: str | None = None,
    status: str | None = Query("ABIERTO"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    q = db.query(EmployeeAuditFinding).filter(EmployeeAuditFinding.organization_id == org_id)
    if employee_id:
        q = q.filter(EmployeeAuditFinding.employee_id == employee_id)
    if status:
        q = q.filter(EmployeeAuditFinding.status == status.upper())
    rows = q.order_by(EmployeeAuditFinding.created_at.desc()).limit(limit).all()
    return [finding_to_dict(r) for r in rows]


@router.get("/salud")
def get_salud(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    return list_health(db, user, organization_id=organization_id)


@router.get("/resumen-centro-control")
def resumen_centro_control(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    return centro_control_resumen(db, user, organization_id=organization_id)


@router.get("/contrato-trabajo")
def contrato_trabajo(
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    return list_trabajo_contract(db, org_id)


@router.get("/contrato-fabrica")
def contrato_fabrica(user: User = Depends(require_permission("auditor_empleados.view"))):
    from app.services.auditor_factory_bridge import portable_control_center_contract
    from app.services import employee_lifecycle_service

    return {
        "auditor_factory_cycle": portable_control_center_contract(),
        "factory": employee_lifecycle_service.auditor_contract(),
        "auto_execution_blocked": True,
    }


@router.get("/hallazgos/{finding_id}/accion-fabrica")
def hallazgo_accion_fabrica(
    finding_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.auditor_factory_bridge import get_finding_factory_action
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    result = get_finding_factory_action(db, org_id, user, finding_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/hallazgos/{finding_id}/iniciar-mejora")
def iniciar_mejora_hallazgo(
    finding_id: str,
    body: dict | None = None,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.auditor_factory_bridge import iniciar_mejora
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    payload = body or {}
    result = iniciar_mejora(
        db,
        org_id,
        user,
        finding_id,
        idempotency_key=payload.get("idempotency_key"),
    )
    if result.get("error"):
        code = 409 if "en curso" in result["error"].lower() else 400
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/mejoras/{trace_id}/ejecutar")
def ejecutar_mejora_fabrica(
    trace_id: str,
    body: dict | None = None,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.auditor_factory_bridge import ejecutar_operacion_fabrica
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    payload = body or {}
    result = ejecutar_operacion_fabrica(
        db,
        org_id,
        user,
        trace_id,
        operation=payload.get("operation"),
        payload=payload.get("payload"),
        idempotency_key=payload.get("idempotency_key"),
    )
    if result.get("error"):
        code = 403 if "Permiso" in result["error"] else 400
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/mejoras/{trace_id}/reauditar")
def reauditar_mejora(
    trace_id: str,
    body: dict | None = None,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.execute")),
):
    from app.services.auditor_factory_bridge import solicitar_reauditoria
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    payload = body or {}
    result = solicitar_reauditoria(
        db,
        org_id,
        user,
        trace_id,
        idempotency_key=payload.get("idempotency_key"),
    )
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/mejoras/{trace_id}/trazabilidad")
def trazabilidad_mejora(
    trace_id: str,
    organization_id: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("auditor_empleados.view")),
):
    from app.services.auditor_factory_bridge import get_traceability
    from app.services.employee_audit_service import resolve_organization_id

    org_id = resolve_organization_id(db, user, organization_id)
    result = get_traceability(db, org_id, trace_id)
    if not result:
        raise HTTPException(status_code=404, detail="Trazabilidad no encontrada")
    return result
