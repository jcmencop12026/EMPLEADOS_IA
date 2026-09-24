"""Modelos — Optimización, priorización avanzada y recomendaciones (Bloque 1290)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

OBJETIVOS_OPTIMIZACION = (
    "MAXIMIZAR_VALOR",
    "MAXIMIZAR_ROI",
    "MAXIMIZAR_IMPACTO",
    "MINIMIZAR_RIESGO",
    "RESULTADO_EQUILIBRADO",
)
ESTADOS_RECOMENDACION = ("PROPUESTA", "REVISADA", "APROBADA", "RECHAZADA", "EJECUTADA", "RECALCULADA", "FALLIDA")
TIPOS_EJECUCION = ("AUTOMATICA", "HUMANA_EXTERNA")
ESTADOS_EJECUCION = ("PENDIENTE_EJECUCION_HUMANA", "EJECUTADA", "FALLIDA", "CANCELADA")


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OptimizacionConfiguracion(Base):
    """Pesos y preferencias por organización."""

    __tablename__ = "optimizacion_configuraciones"
    __table_args__ = (Index("ix_opt_config_org", "organization_id", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    objetivo_default: Mapped[str] = mapped_column(String(40), nullable=False, default="RESULTADO_EQUILIBRADO")
    pesos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OptimizacionRecomendacion(Base):
    """Recomendación de portafolio priorizado."""

    __tablename__ = "optimizacion_recomendaciones"
    __table_args__ = (Index("ix_opt_rec_org_estado", "organization_id", "estado"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PROPUESTA", index=True)
    objetivo: Mapped[str] = mapped_column(String(40), nullable=False)
    es_simulacion: Mapped[bool] = mapped_column(Boolean, default=False)
    grupo_comparacion_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    restricciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    explicacion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprendizaje_influencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    trazabilidad_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    factible: Mapped[bool] = mapped_column(Boolean, default=True)
    conflicto_restricciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_esperado_total: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    costo_esperado_total: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    impacto_esperado_total: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    riesgo_promedio: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    confianza_promedio: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    roi_esperado: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    tiempo_esperado_total: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    justificacion_aprobacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    recomendacion_origen_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("optimizacion_recomendaciones.id"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decidida_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decidida_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OptimizacionItem(Base):
    """Oportunidad evaluada dentro de una recomendación."""

    __tablename__ = "optimizacion_items"
    __table_args__ = (Index("ix_opt_item_rec_opp", "recomendacion_id", "opportunity_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recomendacion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("optimizacion_recomendaciones.id"), nullable=False, index=True
    )
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    seleccionado: Mapped[bool] = mapped_column(Boolean, default=False)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    puntuacion_total: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    factores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusion_razon: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    costo_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    impacto_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    riesgo: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    confianza: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    probabilidad_exito: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    tiempo_esperado_dias: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    aprendizaje_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class OptimizacionAuditoria(Base):
    """Auditoría del bloque 1290."""

    __tablename__ = "optimizacion_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    recomendacion_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("optimizacion_recomendaciones.id"), nullable=True, index=True
    )
    accion: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
