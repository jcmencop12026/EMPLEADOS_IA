"""Modelos — Planificador de consumo y capacidad IA (MB-07)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

CONSUMPTION_CLASSES = frozenset({"DIRECTO", "TRANSVERSAL_ATRIBUIBLE", "PLATAFORMA"})
ACTIVATION_TYPES = frozenset(
    {"PERIODICO", "POR_EVENTO", "MANUAL", "CONTINUO_DETERMINISTICO", "BAJO_DEMANDA"}
)
CREDENTIAL_MODES = frozenset({"IA_ADMINISTRADA", "CREDENCIALES_PROPIAS"})
AMOUNT_KINDS = frozenset({"ESTIMADO", "REAL", "PROYECTADO"})


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConsumptionPlannerOrgConfig(Base):
    """Configuración de planificación por organización."""

    __tablename__ = "consumption_planner_org_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, unique=True, index=True
    )
    credential_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="IA_ADMINISTRADA")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    included_consumption_usd: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    client_price_monthly: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    capacity_total_units: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    max_concurrency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    executions_per_employee_per_day: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=5.0)
    tokens_in_avg: Mapped[int] = mapped_column(Integer, nullable=False, default=1500)
    tokens_out_avg: Mapped[int] = mapped_column(Integer, nullable=False, default=800)
    model_distribution_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_thresholds_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ConsumptionPlannerTransversal(Base):
    """Capacidad transversal configurable por organización."""

    __tablename__ = "consumption_planner_transversal"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    capability_code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    consumption_class: Mapped[str] = mapped_column(String(30), nullable=False, default="TRANSVERSAL_ATRIBUIBLE")
    activation_type: Mapped[str] = mapped_column(String(30), nullable=False, default="PERIODICO")
    is_deterministic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    executions_per_period: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    tokens_in_avg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out_avg: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tools_cost_estimated: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    infra_cost_estimated: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ConsumptionPlannerSimulation(Base):
    """Escenarios guardados (simulador)."""

    __tablename__ = "consumption_planner_simulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
