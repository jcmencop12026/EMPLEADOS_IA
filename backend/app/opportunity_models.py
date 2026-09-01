"""Modelos transversales — Inteligencia proactiva y oportunidades (1030)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProactiveSignal(Base):
    """Señal transversal — origen de detección proactiva."""

    __tablename__ = "proactive_signals"
    __table_args__ = (
        Index("ix_signal_dedupe", "organization_id", "dedupe_key"),
        Index("ix_signal_source_ref", "organization_id", "source_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("signal_sources.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    dominio: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    origen: Mapped[str] = mapped_column(String(60), nullable=False)
    modo_ingesta: Mapped[str] = mapped_column(String(20), nullable=False, default="REAL", index=True)
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evento: Mapped[str] = mapped_column(String(120), nullable=False)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metrica: Mapped[str | None] = mapped_column(String(120), nullable=True)
    valor_metrica: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dimension: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidencia_resumen: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    confianza: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.5)
    dedupe_key: Mapped[str] = mapped_column(String(200), nullable=False)
    estado_procesamiento: Mapped[str] = mapped_column(String(30), nullable=False, default="RECIBIDA", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    procesada: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    signal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SignalSource(Base):
    """Fuente parametrizable de señales reales — sin conector específico."""

    __tablename__ = "signal_sources"
    __table_args__ = (
        Index("ix_signal_sources_org_code", "organization_id", "code", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_fuente: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuracion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Opportunity(Base):
    """Oportunidad detectada — motor transversal de valor."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    dominio: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    contexto_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_estimado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    urgencia: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    riesgo: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIO")
    probabilidad: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    esfuerzo: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIO")
    costo_estimado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_potencial: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_potencial_certidumbre: Mapped[str] = mapped_column(String(30), nullable=False, default="ESTIMADO")
    origen_comercial: Mapped[str] = mapped_column(String(20), nullable=False, default="SOLICITADA", index=True)
    presentar_cliente: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    valor_materializado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    confianza: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.5)
    pertinencia: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pertinencia_razon: Mapped[str | None] = mapped_column(Text, nullable=True)
    momento: Mapped[str | None] = mapped_column(String(30), nullable=True)
    prioridad_score: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    prioridad_componentes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(40), nullable=False, default="DETECTADA", index=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    equipo_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    siguiente_accion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    operation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    finops_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    atribucion_nivel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    atribucion_razon: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    fecha_deteccion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    fecha_revaluacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resultado_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OpportunityTransition(Base):
    """Transición de estado — máquina de estados auditable."""

    __tablename__ = "opportunity_transitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    estado_anterior: Mapped[str] = mapped_column(String(40), nullable=False)
    estado_nuevo: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OpportunityTracking(Base):
    """Seguimiento activo post-activación."""

    __tablename__ = "opportunity_tracking"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    accion: Mapped[str] = mapped_column(String(200), nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    bloqueo: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_inicial_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_objetivo_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_actual_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalamiento: Mapped[str | None] = mapped_column(String(200), nullable=True)
    proxima_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OpportunityTrace(Base):
    """Trazabilidad — cadena señal → oportunidad → acción → resultado."""

    __tablename__ = "opportunity_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    etapa: Mapped[str] = mapped_column(String(60), nullable=False)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
