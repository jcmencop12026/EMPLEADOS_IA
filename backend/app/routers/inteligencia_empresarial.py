"""API — Inteligencia Empresarial Adaptativa (macrobloque evolución C)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.modules.inteligencia_empresarial import service as ie_svc
from app.modules.inteligencia_empresarial.evaluacion_adaptativa import ejecutar_evaluacion_adaptativa
from app.modules.inteligencia_empresarial.motor_proactivo import procesar_nueva_evidencia
from app.modules.inteligencia_empresarial.contracts import CONTRATOS_FUTUROS

router = APIRouter(prefix="/api/inteligencia-empresarial", tags=["Inteligencia Empresarial"])


class EvidenciaBody(BaseModel):
    titulo: str = Field(..., min_length=1)
    descripcion: str = Field(..., min_length=1)
    dominio: str = "procesos"
    correlation_id: str | None = None


@router.get("/contratos")
def get_contratos_futuros(
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    return {"contratos": CONTRATOS_FUTUROS}


@router.get("/panorama")
def panorama_org(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    return ie_svc.panorama_organizacion(db, user.organization_id)


@router.get("/expedientes/{expediente_id}/panorama")
def panorama_exp(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    return ie_svc.panorama_expediente(db, user.organization_id, expediente_id)


@router.get("/expedientes/{expediente_id}/suficiencia")
def suficiencia_exp(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    from app.modules.inteligencia_empresarial.suficiencia import evaluar_suficiencia_unificada
    return evaluar_suficiencia_unificada(db, user.organization_id, expediente_id)


@router.get("/expedientes/{expediente_id}/plan-adaptativo")
def plan_adaptativo(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    from app.modules.inteligencia_empresarial.evaluacion_adaptativa import plan_informacion_adaptativa
    return plan_informacion_adaptativa(db, expediente_id, user.organization_id)


@router.post("/expedientes/{expediente_id}/evaluar-adaptativo")
def evaluar_adaptativo(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.manage")),
) -> dict[str, Any]:
    result = ejecutar_evaluacion_adaptativa(db, expediente_id, user.organization_id, user_id=user.id)
    db.commit()
    return result


@router.get("/expedientes/{expediente_id}/cadena-analitica")
def cadena_exp(
    expediente_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    from app.modules.inteligencia_empresarial.cadena_analitica import construir_cadena_expediente
    return construir_cadena_expediente(db, user.organization_id, expediente_id)


@router.get("/oportunidades/{opportunity_id}/panorama")
def panorama_opp(
    opportunity_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.view")),
) -> dict[str, Any]:
    return ie_svc.panorama_oportunidad(db, user.organization_id, opportunity_id)


@router.post("/evidencia")
def registrar_evidencia(
    body: EvidenciaBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("inteligencia_empresarial.manage")),
) -> dict[str, Any]:
    result = procesar_nueva_evidencia(
        db,
        user.organization_id,
        user,
        titulo=body.titulo,
        descripcion=body.descripcion,
        dominio=body.dominio,
        correlation_id=body.correlation_id,
    )
    db.commit()
    return result
