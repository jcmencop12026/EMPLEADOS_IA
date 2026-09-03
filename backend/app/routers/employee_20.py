"""API — Empleado IA 2.0 (evolución aislada)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.services import employee_20_service as svc
from app.services.employee_20_cc_adapter import collect_control_center_signals

router = APIRouter(prefix="/api/empleados-ia-20", tags=["empleados-ia-20"])


class FichaLaboralUpdate(BaseModel):
    cargo: str | None = None
    mision: str | None = None
    funciones: list[str] | None = None
    responsabilidades: list[str] | None = None
    procesos: list[str] | None = None
    empresa: str | None = None
    supervisor_user_id: str | None = None
    limites: dict[str, Any] | None = None
    horario: dict[str, Any] | None = None
    autonomia: str | None = None
    indicadores: list[dict[str, Any]] | None = None
    criterios_exito: list[str] | None = None
    criterios_escalamiento: list[str] | None = None


class SupervisionCreate(BaseModel):
    event_type: str
    descripcion: str | None = None
    work_plan_id: str | None = None
    task_id: str | None = None
    metricas: dict[str, Any] | None = None
    calidad_score: float | None = None
    duracion_ms: int | None = None


class IndicadorUpsert(BaseModel):
    codigo: str = Field(min_length=1, max_length=80)
    nombre: str = Field(min_length=1, max_length=200)
    unidad: str = "%"
    valor_esperado: float | None = None
    valor_real: float | None = None
    periodo: str | None = None


class LearningProposalCreate(BaseModel):
    observacion: str = Field(min_length=5)
    propuesta: str = Field(min_length=5)
    causa_probable: str | None = None
    evidencia: dict[str, Any] | None = None
    impacto_esperado: str | None = None


class LearningDecision(BaseModel):
    aprobar: bool
    notas: str | None = None


class ResultLinkCreate(BaseModel):
    work_plan_id: str | None = None
    task_id: str | None = None
    resultado_ref: str | None = None
    indicador_codigo: str | None = None
    valor_ref: float | None = None
    valor_economico_ref: str | None = None
    notas: str | None = None


@router.get("/inventario")
def get_inventario(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return {
        "bloque": "EMPLEADO_IA_2.0",
        "reutiliza": [
            "AIEmployee / agent_factory",
            "capabilities / tools / knowledge grants",
            "coordinator / WorkPlan / EmployeeTask",
            "ApprovalRequest / FinOpsRecord",
            "EmployeeVersion / EmployeeTestCase",
        ],
        "extensiones": [
            "employee_labor_profiles",
            "employee_supervision_logs",
            "employee_performance_indicators",
            "employee_learning_proposals",
            "employee_result_links",
            "employee_20_autonomy",
            "employee_20_cc_signals",
        ],
        "no_duplica": ["Centro Control estable", "motor economía B", "evaluaciones expediente"],
    }


@router.get("/senal-centro-control")
def senales_cc(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return collect_control_center_signals(db, user.organization_id)


@router.get("/employees/{employee_id}/ficha")
def get_ficha(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    data = svc.build_ficha_laboral(db, user.organization_id, employee_id)
    if not data:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return data


@router.put("/employees/{employee_id}/ficha")
def put_ficha(
    employee_id: str,
    body: FichaLaboralUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    try:
        result = svc.upsert_ficha_laboral(
            db, user.organization_id, employee_id, body.model_dump(exclude_unset=True)
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/employees/{employee_id}/supervision")
def get_supervision(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return {
        "resumen": svc.supervision_summary(db, user.organization_id, employee_id),
        "eventos": svc.list_supervision(db, user.organization_id, employee_id),
    }


@router.post("/employees/{employee_id}/supervision")
def post_supervision(
    employee_id: str,
    body: SupervisionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    try:
        result = svc.record_supervision(
            db,
            user.organization_id,
            employee_id,
            event_type=body.event_type,
            descripcion=body.descripcion,
            work_plan_id=body.work_plan_id,
            task_id=body.task_id,
            metricas=body.metricas,
            calidad_score=body.calidad_score,
            duracion_ms=body.duracion_ms,
            actor_user_id=user.id,
        )
        db.commit()
        return result
    except (LookupError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/employees/{employee_id}/evaluacion")
def get_evaluacion(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    try:
        return svc.evaluate_employee(db, user.organization_id, employee_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/employees/{employee_id}/indicadores")
def post_indicador(
    employee_id: str,
    body: IndicadorUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    try:
        result = svc.upsert_performance_indicator(
            db,
            user.organization_id,
            employee_id,
            codigo=body.codigo,
            nombre=body.nombre,
            unidad=body.unidad,
            valor_esperado=body.valor_esperado,
            valor_real=body.valor_real,
            periodo=body.periodo,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/employees/{employee_id}/aprendizaje")
def list_aprendizaje(employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "employee.view", db)
    return {"items": svc.list_learning_proposals(db, user.organization_id, employee_id)}


@router.post("/employees/{employee_id}/aprendizaje")
def create_aprendizaje(
    employee_id: str,
    body: LearningProposalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    try:
        result = svc.create_learning_proposal(
            db,
            user.organization_id,
            employee_id,
            user.id,
            observacion=body.observacion,
            propuesta=body.propuesta,
            causa_probable=body.causa_probable,
            evidencia=body.evidencia,
            impacto_esperado=body.impacto_esperado,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/aprendizaje/{proposal_id}/decidir")
def decidir_aprendizaje(
    proposal_id: str,
    body: LearningDecision,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.admin", db)
    try:
        result = svc.decide_learning_proposal(
            db,
            user.organization_id,
            proposal_id,
            user.id,
            aprobar=body.aprobar,
            notas=body.notas,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/employees/{employee_id}/resultados-contrato")
def get_resultados_contrato(
    employee_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    check_permission(user, "employee.view", db)
    return svc.results_contract(db, user.organization_id, employee_id)


@router.post("/employees/{employee_id}/resultados-contrato")
def post_resultado_link(
    employee_id: str,
    body: ResultLinkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "employee.edit", db)
    try:
        result = svc.link_result(
            db,
            user.organization_id,
            employee_id,
            work_plan_id=body.work_plan_id,
            task_id=body.task_id,
            resultado_ref=body.resultado_ref,
            indicador_codigo=body.indicador_codigo,
            valor_ref=body.valor_ref,
            valor_economico_ref=body.valor_economico_ref,
            notas=body.notas,
        )
        db.commit()
        return result
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
