"""Modelos — Empleado IA 2.0 (evolución aislada, sin duplicar fábrica)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmployeeLaborProfile(Base):
    """Ficha laboral extendida — 1:1 con ai_employees."""

    __tablename__ = "employee_labor_profiles"
    __table_args__ = (UniqueConstraint("employee_id", name="uq_emp_labor_profile_employee"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    mision: Mapped[str | None] = mapped_column(Text, nullable=True)
    funciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsabilidades_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    procesos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    empresa_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    supervisor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    limites_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    horario_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    autonomy_level: Mapped[str] = mapped_column(String(40), nullable=False, default="EJECUTA_CON_APROBACION")
    indicadores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterios_exito_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterios_escalamiento_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmployeeSupervisionLog(Base):
    """Registro de supervisión operativa del empleado."""

    __tablename__ = "employee_supervision_logs"
    __table_args__ = (Index("ix_emp_sup_org_emp", "organization_id", "employee_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    metricas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    calidad_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    duracion_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeePerformanceIndicator(Base):
    """Indicador esperado vs real por empleado."""

    __tablename__ = "employee_performance_indicators"
    __table_args__ = (Index("ix_emp_perf_org_emp", "organization_id", "employee_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    unidad: Mapped[str] = mapped_column(String(40), default="%", nullable=False)
    valor_esperado: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_real: Mapped[float | None] = mapped_column(Float, nullable=True)
    periodo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    alerta: Mapped[str | None] = mapped_column(String(60), nullable=True)
    evidencia_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmployeeLearningProposal(Base):
    """Aprendizaje controlado — sin autoeditar configuración productiva."""

    __tablename__ = "employee_learning_proposals"
    __table_args__ = (Index("ix_emp_learn_org_emp", "organization_id", "employee_id", "estado"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PROPUESTA")
    observacion: Mapped[str] = mapped_column(Text, nullable=False)
    causa_probable: Mapped[str | None] = mapped_column(Text, nullable=True)
    propuesta: Mapped[str] = mapped_column(Text, nullable=False)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_esperado: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aprobado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    aprobado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmployeeResultLink(Base):
    """Contrato empleado → ejecución → resultado → indicador (sin economía duplicada)."""

    __tablename__ = "employee_result_links"
    __table_args__ = (Index("ix_emp_res_org_emp", "organization_id", "employee_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_tasks.id"), nullable=True)
    resultado_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    indicador_codigo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    valor_ref: Mapped[float | None] = mapped_column(Float, nullable=True)
    valor_economico_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
