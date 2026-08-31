"""Modelos de línea base, medición posterior e impacto — Bloque 1200."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

DIRECCION_INDICADOR = ("MAYOR_ES_MEJOR", "MENOR_ES_MEJOR", "INFORMATIVO")
ESTADOS_LINEA_BASE = ("BORRADOR", "ACTIVA", "EN_MEDICION", "VALIDADA", "CERRADA")
ESTADOS_MEDICION = ("REGISTRADA", "VALIDADA")
ATRIBUCION_NIVELES = ("NO_ATRIBUIBLE", "PARCIALMENTE_ATRIBUIBLE", "ATRIBUIBLE")
TIPOS_IMPACTO = ("IMPACTO_ESPERADO", "IMPACTO_REAL", "CAMBIO_OBSERVADO", "VALOR_ATRIBUIDO")
EVALUACIONES = ("MEJORA", "DETERIORO", "SIN_CAMBIO", "INFORMATIVO")
FUENTES_MEDICION = ("MANUAL", "API", "ARCHIVO", "AUTOMATIZACION", "BASE_DATOS", "SENAL")


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LineaBase(Base):
    __tablename__ = "lineas_base"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    indicador: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    unidad: Mapped[str] = mapped_column(String(40), nullable=False, default="unidad")
    valor_base: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    fecha_inicio_base: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin_base: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fuente: Mapped[str] = mapped_column(String(60), nullable=False, default="MANUAL")
    metodo_calculo: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    direccion_indicador: Mapped[str] = mapped_column(String(30), nullable=False, default="MAYOR_ES_MEJOR")
    impacto_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="BORRADOR")
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    accion_referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)
    valor_economico_tipo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class LineaBaseMedicion(Base):
    __tablename__ = "lineas_base_mediciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    linea_base_id: Mapped[str] = mapped_column(String(36), ForeignKey("lineas_base.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    valor_posterior: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    periodo_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    periodo_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fuente: Mapped[str] = mapped_column(String(60), nullable=False, default="MANUAL")
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="REGISTRADA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


class LineaBaseImpacto(Base):
    """Instantánea de comparación — inmutable tras validación."""

    __tablename__ = "lineas_base_impactos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    linea_base_id: Mapped[str] = mapped_column(String(36), ForeignKey("lineas_base.id"), nullable=False, index=True)
    medicion_id: Mapped[str] = mapped_column(String(36), ForeignKey("lineas_base_mediciones.id"), nullable=False, unique=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    valor_base: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    valor_posterior: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    variacion_absoluta: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    variacion_porcentual: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    evaluacion: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo_impacto: Mapped[str] = mapped_column(String(40), nullable=False, default="CAMBIO_OBSERVADO")
    atribucion_nivel: Mapped[str] = mapped_column(String(40), nullable=False, default="NO_ATRIBUIBLE")
    atribucion_porcentaje: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    atribucion_justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    atribucion_evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_esperado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    impacto_real: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    congelado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class LineaBaseHistorial(Base):
    __tablename__ = "lineas_base_historial"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    linea_base_id: Mapped[str] = mapped_column(String(36), ForeignKey("lineas_base.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
