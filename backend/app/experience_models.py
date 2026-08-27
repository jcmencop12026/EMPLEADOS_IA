"""Experiencia transversal del core — ORQUESTADOR-EXPERIENCIA-1010."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmployeeExperienceRecord(Base):
    """Registro estructurado de experiencia (sin conversaciones completas)."""

    __tablename__ = "employee_experience_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    dominio: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    tipo_problema: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    contexto_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    senales_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    hipotesis: Mapped[str | None] = mapped_column(String(300), nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    accion: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado_esperado: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado_real: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_antes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    kpi_despues_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_esperado: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_obtenido: Mapped[float | None] = mapped_column(Float, nullable=True)
    tiempo_esperado_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    tiempo_real_horas: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback_humano: Mapped[str | None] = mapped_column(String(60), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="INDETERMINADO", index=True)
    confianza: Mapped[float | None] = mapped_column(Float, nullable=True)
    peso_calidad: Mapped[float | None] = mapped_column(Float, nullable=True)
    condiciones_exito_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    condiciones_fracaso_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    caso_origen_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    trazabilidad_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    resultado_actualizado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExperienceSelectionLog(Base):
    """Trazabilidad de selección dinámica de empleados IA."""

    __tablename__ = "experience_selection_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    solicitud: Mapped[str | None] = mapped_column(Text, nullable=True)
    dominio_principal: Mapped[str | None] = mapped_column(String(80), nullable=True)
    candidatos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    factores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    experiencia_consultada_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    seleccionados_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    roles_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    razon_seleccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    caso_origen_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
