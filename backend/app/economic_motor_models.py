"""Modelos — Motor Económico EIAAX (capa unificada sobre FinOps existente)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EconomicCostEntry(Base):
    """Registro unificado de costo — enlaza FinOps cuando aplica."""

    __tablename__ = "economic_cost_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    cost_class: Mapped[str] = mapped_column(String(30), nullable=False, default="DIRECTO")
    amount_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="REAL")
    cost_source: Mapped[str] = mapped_column(String(40), nullable=False, default="OTRO")
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ORGANIZACION")
    scope_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    evaluacion_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    finops_record_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("finops_records.id"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EconomicValueEntry(Base):
    """Registro unificado de valor — POTENCIAL nunca cuenta como realizado."""

    __tablename__ = "economic_value_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    value_type: Mapped[str] = mapped_column(String(60), nullable=False)
    value_nature: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADO")
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ORGANIZACION")
    scope_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    evaluacion_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    finops_value_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("finops_values.id"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EconomicPrivateEconomy(Base):
    """Economía privada operador — NO expuesta en Vista Entidad por defecto."""

    __tablename__ = "economic_private_economy"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    period_label: Mapped[str] = mapped_column(String(40), nullable=False, default="MENSUAL")
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    real_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    time_hours: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    resources_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    ia_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    infra_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    services_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    support_cost: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    client_value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    suggested_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    margin: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    roi: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    payback_months: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    commercial_risk_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EconomicPriceRecommendation(Base):
    """Recomendación de precio — siempre borrador hasta publicación manual."""

    __tablename__ = "economic_price_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ORGANIZACION")
    scope_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    recommended_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    margin_estimate: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    factors_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
