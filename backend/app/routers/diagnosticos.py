"""API — Diagnóstico transversal multidominio (1220)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.diagnostic_models import DIAGNOSTIC_DOMAINS
from app.models import User
from app.permissions import require_permission
from app.services import diagnostic_service as diag_svc

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnósticos"])


class IndicatorDefCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=2, max_length=200)
    dominio: str
    proceso: str | None = None
    subproceso: str | None = None
    unidad: str | None = None
    direccion_esperada: str = "CUALQUIERA"
    periodicidad: str | None = None
    umbral_min: float | None = None
    umbral_max: float | None = None
    fuente_code: str | None = None
    metadata: dict[str, Any] | None = None


class GenerateDiagnosticBody(BaseModel):
    periodo_inicio: str | None = Field(None, description="ISO8601")
    periodo_fin: str | None = Field(None, description="ISO8601")
    dominios: list[str] | None = None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.get("/dominios")
def list_domains(user: User = Depends(require_permission("diagnosticos.view"))):
    return sorted(DIAGNOSTIC_DOMAINS)


@router.get("/config/indicadores")
def list_indicators(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.view")),
):
    rows = diag_svc.list_indicator_definitions(db, user.organization_id)
    return [diag_svc.indicator_def_to_dict(r) for r in rows]


@router.post("/config/indicadores", status_code=201)
def create_indicator(
    body: IndicatorDefCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.manage")),
):
    row = diag_svc.create_indicator_definition(
        db,
        organization_id=user.organization_id,
        code=body.code,
        name=body.name,
        dominio=body.dominio,
        proceso=body.proceso,
        subproceso=body.subproceso,
        unidad=body.unidad,
        direccion_esperada=body.direccion_esperada,
        periodicidad=body.periodicidad,
        umbral_min=body.umbral_min,
        umbral_max=body.umbral_max,
        fuente_code=body.fuente_code,
        metadata=body.metadata,
        user_id=user.id,
    )
    db.commit()
    return diag_svc.indicator_def_to_dict(row)


@router.get("")
def list_diagnostics(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.view")),
):
    rows = diag_svc.list_diagnostics(db, user.organization_id, limit=limit)
    return [diag_svc.diagnostic_to_summary(r) for r in rows]


@router.post("/generar", status_code=201)
def generate_diagnostic(
    body: GenerateDiagnosticBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.generate")),
):
    result = diag_svc.generate_diagnostic(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        periodo_inicio=_parse_dt(body.periodo_inicio),
        periodo_fin=_parse_dt(body.periodo_fin),
        dominios=body.dominios,
    )
    db.commit()
    return result


@router.get("/{diagnostic_id}")
def get_diagnostic(
    diagnostic_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.view")),
):
    return diag_svc.diagnostic_to_detail(db, user.organization_id, diagnostic_id)


@router.post("/{diagnostic_id}/validar")
def validate_diagnostic(
    diagnostic_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.validate")),
):
    result = diag_svc.validate_diagnostic(db, user.organization_id, diagnostic_id, user.id)
    db.commit()
    return result


@router.get("/{diagnostic_id}/trazabilidad")
def diagnostic_trace(
    diagnostic_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("diagnosticos.view")),
):
    return diag_svc.get_diagnostic_trace(db, user.organization_id, diagnostic_id)
