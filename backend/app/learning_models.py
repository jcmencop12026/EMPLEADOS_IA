"""Modelos — Aprendizaje, retroalimentación y repriorización (Bloque 1260)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ESTADOS_CICLO = ("ABIERTO", "EVALUADO", "CERRADO")
TIPOS_EXPLICACION = ("CONFIRMADA", "PROBABLE", "HIPOTESIS")
CALIDAD_RECOMENDACION = ("EXCELENTE", "ACEPTABLE", "DEBIL", "DEFICIENTE")
ESTADOS_RECALIBRACION = ("SUGERIDA", "APROBADA", "RECHAZADA", "APLICADA")
TIPOS_PATRON = ("DESVIACION_IMPACTO", "DESVIACION_VALOR", "DESVIACION_COSTO", "DESVIACION_TIEMPO", "CALIDAD_RECOMENDACION")


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CicloAprendizaje(Base):
    """Ciclo esperado vs real sobre una oportunidad/ejecución."""

    __tablename__ = "ciclos_aprendizaje"
    __table_args__ = (
        Index("ix_ciclo_aprendizaje_org_opp", "organization_id", "opportunity_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=True)
    diagnostic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostics.id"), nullable=True)
    valuation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunity_valuations.id"), nullable=True)
    linea_base_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("lineas_base.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="ABIERTO")
    # Esperado
    impacto_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    costo_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    tiempo_esperado_dias: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Real
    impacto_real: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_real: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    costo_real: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    tiempo_real_dias: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Desviaciones calculadas (snapshot)
    desviaciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    calidad_recomendacion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    prioridad_anterior: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    prioridad_propuesta: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    explicacion_prioridad_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    referencias_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    evaluado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Retroalimentacion(Base):
    """Retroalimentación estructurada sobre una evaluación."""

    __tablename__ = "retroalimentaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ciclo_id: Mapped[str] = mapped_column(String(36), ForeignKey("ciclos_aprendizaje.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    tipo_explicacion: Mapped[str] = mapped_column(String(30), nullable=False, default="PROBABLE")
    calidad_recomendacion: Mapped[str] = mapped_column(String(30), nullable=False)
    resumen: Mapped[str] = mapped_column(String(500), nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    lecciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Recalibracion(Base):
    """Propuesta de ajuste con control humano."""

    __tablename__ = "recalibraciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ciclo_id: Mapped[str] = mapped_column(String(36), ForeignKey("ciclos_aprendizaje.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="SUGERIDA", index=True)
    campo: Mapped[str] = mapped_column(String(60), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(String(200), nullable=True)
    valor_nuevo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    justificacion: Mapped[str] = mapped_column(Text, nullable=False)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    factores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sugerida_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    sugerida_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    decidida_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    decidida_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aplicada_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    aplicada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)


class PatronAprendizaje(Base):
    """Patrón repetido detectado a nivel organizacional."""

    __tablename__ = "patrones_aprendizaje"
    __table_args__ = (
        Index("ix_patron_aprendizaje_org_tipo", "organization_id", "tipo_patron", "clave_patron"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo_patron: Mapped[str] = mapped_column(String(40), nullable=False)
    clave_patron: Mapped[str] = mapped_column(String(200), nullable=False)
    dominio: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tipo_oportunidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ocurrencias: Mapped[int] = mapped_column(nullable=False, default=1)
    resumen: Mapped[str] = mapped_column(String(500), nullable=False)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ultima_deteccion_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class AprendizajeAuditoria(Base):
    """Historial auditable del bloque 1260."""

    __tablename__ = "aprendizaje_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ciclo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ciclos_aprendizaje.id"), nullable=True, index=True)
    recalibracion_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("recalibraciones.id"), nullable=True, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True, index=True)
    accion: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
