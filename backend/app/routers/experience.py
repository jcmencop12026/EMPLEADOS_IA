"""API experiencia transversal del core — ORQUESTADOR-EXPERIENCIA-1010."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import check_permission
from app.services.experience_core import (
    actualizar_resultado_experiencia,
    buscar_experiencias_similares,
    crear_experiencia,
    registrar_feedback_experiencia,
)
from app.services.orchestrator_selection import select_team

router = APIRouter(prefix="/api/experiencia", tags=["experiencia"])


class CrearExperienciaRequest(BaseModel):
    employee_id: str
    dominio: str
    tipo_problema: str
    contexto: dict | None = None
    senales: dict | None = None
    hipotesis: str | None = None
    decision: str | None = None
    accion: str | None = None
    resultado_esperado: str | None = None


class ActualizarResultadoRequest(BaseModel):
    resultado_real: str
    estado: str = Field(pattern="^(EXITO|PARCIAL|FRACASO|INDETERMINADO)$")
    kpi_despues: dict | None = None
    valor_obtenido: float | None = None
    condiciones_exito: list | None = None
    condiciones_fracaso: list | None = None


class FeedbackExperienciaRequest(BaseModel):
    feedback: str


class SeleccionEquipoRequest(BaseModel):
    solicitud: str
    available_data: list[str] | None = None
    contexto: dict | None = None


@router.post("/registros")
def crear_registro(
    body: CrearExperienciaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    record = crear_experiencia(
        db, user.organization_id,
        employee_id=body.employee_id,
        dominio=body.dominio,
        tipo_problema=body.tipo_problema,
        contexto=body.contexto,
        senales=body.senales,
        hipotesis=body.hipotesis,
        decision=body.decision,
        accion=body.accion,
        resultado_esperado=body.resultado_esperado,
    )
    db.commit()
    return {"id": record.id, "peso_calidad": record.peso_calidad, "estado": record.estado}


@router.patch("/registros/{record_id}/resultado")
def actualizar_resultado(
    record_id: str,
    body: ActualizarResultadoRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    record = actualizar_resultado_experiencia(
        db, user.organization_id, record_id,
        resultado_real=body.resultado_real,
        estado=body.estado,
        kpi_despues=body.kpi_despues,
        valor_obtenido=body.valor_obtenido,
        condiciones_exito=body.condiciones_exito,
        condiciones_fracaso=body.condiciones_fracaso,
    )
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiencia no encontrada")
    db.commit()
    return {"id": record.id, "estado": record.estado, "peso_calidad": record.peso_calidad}


@router.post("/registros/{record_id}/feedback")
def feedback_experiencia(
    record_id: str,
    body: FeedbackExperienciaRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    record = registrar_feedback_experiencia(db, user.organization_id, record_id, body.feedback)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Experiencia no encontrada")
    db.commit()
    return {"id": record.id, "feedback": record.feedback_humano, "peso_calidad": record.peso_calidad}


@router.get("/similares")
def listar_similares(
    dominio: str | None = None,
    tipo_problema: str | None = None,
    employee_id: str | None = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    return buscar_experiencias_similares(
        db, user.organization_id,
        dominio=dominio,
        tipo_problema=tipo_problema,
        employee_id=employee_id,
        limit=limit,
    )


@router.post("/seleccion-equipo")
def seleccion_equipo(
    body: SeleccionEquipoRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_permission(user, "salud.administrar_experiencia", db)
    plan = select_team(
        db, user.organization_id,
        body.solicitud,
        available_data=body.available_data,
        contexto=body.contexto,
    )
    db.commit()
    return plan
