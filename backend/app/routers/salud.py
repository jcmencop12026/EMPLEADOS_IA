"""API del motor especializado IPS (SALUD-960)."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_current_user
from app.database import get_db
from app.models import User
from app.permissions import check_permission
from app.salud_models import IpsActionResult, IpsDataset, IpsPropuesta
from app.schemas_salud import (
    ActionPlanRequest,
    ActionResultRequest,
    AnalysisRequest,
    DatasetUploadRequest,
    FeedbackRequest,
    QuestionRequest,
    SpecialistSelectionRequest,
)
from app.services.salud_engine import create_action_plan, get_diagnostico, run_ips_analysis
from app.services.salud_experience import buscar_casos_similares, get_employee_performance, record_feedback
from app.services.salud_normalization import profile_data_quality
from app.services.salud_questions import responder_pregunta
from app.services.salud_specialist_selection import select_specialists
from app.tools.salud_analytics import ejecutar_herramienta

router = APIRouter(prefix="/api/salud", tags=["salud"])


@router.post("/datasets")
def upload_dataset(
    body: DatasetUploadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.cargar_datos", db)
    quality = profile_data_quality(body.source_type, body.records)
    ds = IpsDataset(
        organization_id=user.organization_id,
        ips_name=body.ips_name,
        source_type=body.source_type,
        filename=body.filename,
        profile_code=body.profile_code,
        records_count=len(body.records),
        data_json=json.dumps(body.records, ensure_ascii=False),
        quality_json=json.dumps(quality, ensure_ascii=False),
        created_by_id=user.id,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return {"id": ds.id, "calidad": quality}


@router.post("/analisis")
def ejecutar_analisis(
    body: AnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.ejecutar_analisis", db)
    analysis = run_ips_analysis(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        ips_name=body.ips_name,
        request_text=body.request_text,
        dataset_ids=body.dataset_ids,
        inline_datasets=body.inline_datasets,
    )
    return {"id": analysis.id, "estado": analysis.status}


@router.get("/diagnostico/{analysis_id}")
def obtener_diagnostico(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.consultar_diagnostico", db)
    result = get_diagnostico(db, user.organization_id, analysis_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


@router.post("/analisis/{analysis_id}/plan-accion")
def crear_plan_accion(
    analysis_id: str,
    body: ActionPlanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.aceptar_recomendaciones", db)
    try:
        plan = create_action_plan(
            db,
            organization_id=user.organization_id,
            analysis_id=analysis_id,
            propuesta_ids=body.propuesta_ids,
            user_id=user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "id": plan.id,
        "titulo": plan.title,
        "work_plan_id": plan.work_plan_id,
        "tareas": json.loads(plan.tasks_json),
    }


@router.post("/feedback")
def registrar_feedback(
    body: FeedbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.aceptar_recomendaciones", db)
    fb = record_feedback(
        db, user.organization_id,
        target_type=body.target_type,
        target_id=body.target_id,
        feedback_type=body.feedback_type,
        comment=body.comment,
        user_id=user.id,
    )
    db.commit()
    return {"id": fb.id, "tipo": fb.feedback_type}


@router.post("/propuestas/{propuesta_id}/resultado")
def registrar_resultado(
    propuesta_id: str,
    body: ActionResultRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.aceptar_recomendaciones", db)
    prop = (
        db.query(IpsPropuesta)
        .filter(IpsPropuesta.id == propuesta_id, IpsPropuesta.organization_id == user.organization_id)
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    result = IpsActionResult(
        organization_id=user.organization_id,
        propuesta_id=propuesta_id,
        meta=body.meta,
        resultado=body.resultado,
        outcome=body.outcome,
    )
    db.add(result)
    db.commit()
    return {"id": result.id, "outcome": result.outcome}


@router.post("/pregunta/{analysis_id}")
def responder_pregunta_natural(
    analysis_id: str,
    body: QuestionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.consultar_diagnostico", db)
    diag = get_diagnostico(db, user.organization_id, analysis_id)
    if diag.get("error"):
        raise HTTPException(status_code=404, detail=diag["error"])
    return responder_pregunta(body.pregunta, diag)


@router.post("/especialistas/seleccionar")
def seleccionar_especialistas(
    body: SpecialistSelectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.ejecutar_analisis", db)
    return select_specialists(db, user.organization_id, body.request_text, body.available_data)


@router.get("/casos-similares")
def casos_similares(
    tipo_problema: str | None = None,
    pagador: str | None = None,
    proceso: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    return buscar_casos_similares(
        db, user.organization_id,
        tipo_problema=tipo_problema, pagador=pagador, proceso=proceso,
    )


@router.get("/desempeno")
def desempeno_empleados(
    employee_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    return get_employee_performance(db, user.organization_id, employee_id)


@router.post("/herramientas/{tool_code}")
def ejecutar_herramienta_analitica(
    tool_code: str,
    datasets: dict[str, list],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.ejecutar_analisis", db)
    return ejecutar_herramienta(tool_code, datasets)


@router.get("/demo/datasets")
def demo_datasets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_permission(user, "salud.consultar_diagnostico", db)
    from app.fixtures.salud_demo import get_demo_datasets
    return get_demo_datasets()
