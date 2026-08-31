"""API de fuentes y señales reales — Bloque 1120."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.permissions import require_permission
from app.services import signal_ingestion_service as sig_svc

router = APIRouter(prefix="/api/senales", tags=["Señales"])

_SOURCE_TYPE_MAP = {
    "api": "API",
    "base_datos": "DATABASE",
    "archivo": "FILE",
    "evento": "EVENT",
    "automatizacion": "AUTOMATION",
    "integracion_externa": "EXTERNAL_FUTURE",
}


class SourceCreateBody(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=255)
    tipo_fuente: str = Field(..., description="api|base_datos|archivo|evento|automatizacion|integracion_externa")
    descripcion: str | None = None
    configuracion: dict[str, Any] | None = None


class RealSignalIngestBody(BaseModel):
    source_code: str = Field(..., min_length=2, max_length=64)
    tipo: str = Field(..., min_length=2, max_length=64)
    dominio: str = Field(..., min_length=2, max_length=64)
    evento: str = Field(..., min_length=2, max_length=120)
    referencia: str = Field(..., min_length=2, max_length=255)
    proceso: str | None = Field(None, max_length=128)
    metrica: str | None = Field(None, max_length=128)
    valor: float | None = None
    unidad: str | None = Field(None, max_length=32)
    dimension: str | None = Field(None, max_length=128)
    evidencia_resumen: str | None = Field(None, max_length=2000)
    metadata: dict[str, Any] | None = None
    fecha: str | None = Field(None, description="ISO8601 opcional")
    idempotency_key: str | None = Field(None, max_length=128)
    titulo: str | None = None
    tipo_oportunidad: str | None = None
    indicadores: dict[str, Any] | None = None
    impacto_estimado: float | None = None
    valor_potencial: float | None = None
    urgencia: str | None = None
    regla_analisis: str | None = None


def _normalize_source_type(raw: str) -> str:
    key = raw.strip().lower()
    if key in _SOURCE_TYPE_MAP:
        return _SOURCE_TYPE_MAP[key]
    upper = raw.strip().upper()
    if upper in sig_svc.SOURCE_TYPES:
        return upper
    raise HTTPException(status_code=422, detail="Tipo de fuente no válido")


def _ingest_payload(body: RealSignalIngestBody) -> dict[str, Any]:
    return {
        "source_code": body.source_code,
        "tipo": body.tipo,
        "dominio": body.dominio,
        "evento": body.evento,
        "referencia": body.referencia,
        "proceso": body.proceso,
        "metrica": body.metrica,
        "valor": body.valor,
        "unidad": body.unidad,
        "dimension": body.dimension,
        "evidencia_resumen": body.evidencia_resumen,
        "metadata": body.metadata,
        "fecha": body.fecha,
        "idempotency_key": body.idempotency_key,
        "titulo": body.titulo,
        "tipo_oportunidad": body.tipo_oportunidad,
        "indicadores": body.indicadores,
        "impacto_estimado": body.impacto_estimado,
        "valor_potencial": body.valor_potencial,
        "urgencia": body.urgencia,
        "regla_analisis": body.regla_analisis,
        "modo_ingesta": "REAL",
    }


@router.get("/fuentes")
def list_sources(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    rows = sig_svc.list_sources(db, user.organization_id)
    return [sig_svc.source_to_dict(row) for row in rows]


@router.post("/fuentes", status_code=201)
def create_source(
    body: SourceCreateBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.manage")),
):
    src = sig_svc.create_source(
        db,
        organization_id=user.organization_id,
        code=body.code,
        name=body.name,
        tipo_fuente=_normalize_source_type(body.tipo_fuente),
        descripcion=body.descripcion,
        configuracion=body.configuracion,
        user_id=user.id,
    )
    db.commit()
    return sig_svc.source_to_dict(src)


@router.post("/ingesta", status_code=201)
def ingest_signal(
    body: RealSignalIngestBody,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.manage")),
):
    result = sig_svc.ingest_real_signal(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        data=_ingest_payload(body),
    )
    db.commit()
    return result


@router.get("")
def list_signals(
    limit: int = Query(50, ge=1, le=200),
    modo: str | None = Query(None, description="REAL|SINTETICO|PRUEBA"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    rows = sig_svc.list_recent_signals(
        db,
        user.organization_id,
        limit=limit,
        modo_ingesta=modo.upper() if modo else None,
    )
    return [sig_svc.signal_to_dict(row) for row in rows]


@router.get("/{signal_id}/trazabilidad")
def signal_trace(
    signal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("oportunidades.view")),
):
    return sig_svc.get_signal_trace(db, user.organization_id, signal_id)
