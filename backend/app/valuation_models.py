"""Modelos — Valoración económica y ROI por oportunidad (1210)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OpportunityValuation(Base):
    """Valoración económica principal de una oportunidad."""

    __tablename__ = "opportunity_valuations"
    __table_args__ = (
        UniqueConstraint("organization_id", "opportunity_id", name="uq_valuation_org_opp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    value_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="INTERNO")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OpportunityValuationExpected(Base):
    """Valor esperado — cálculo determinístico valor bruto × probabilidad."""

    __tablename__ = "opportunity_valuation_expected"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    valuation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunity_valuations.id"), nullable=False, unique=True, index=True
    )
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    gross_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(7, 6), nullable=True)
    execution_cost_expected: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adjusted_expected: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    value_nature: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADA")
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OpportunityValuationScenario(Base):
    """Escenario conservador / base / optimista."""

    __tablename__ = "opportunity_valuation_scenarios"
    __table_args__ = (
        UniqueConstraint("valuation_id", "scenario_type", name="uq_valuation_scenario_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    valuation_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunity_valuations.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(7, 6), nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adjusted_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OpportunityValuationReal(Base):
    """Valor materializado y atribuible — compatible con medición real (bloque 1200)."""

    __tablename__ = "opportunity_valuation_real"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    valuation_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunity_valuations.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    materialized_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    attributable_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    value_nature: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADO")
    attribution_level: Mapped[str] = mapped_column(String(30), nullable=False, default="NO ATRIBUIBLE")
    attribution_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_measurement_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OpportunityExecutionCost(Base):
    """Costos de ejecución adicionales (no solo IA FinOps)."""

    __tablename__ = "opportunity_execution_costs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    valuation_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunity_valuations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    cost_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    finops_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recorded_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class OpportunityValuationHistory(Base):
    """Histórico de versiones — no sobrescribe evidencia económica."""

    __tablename__ = "opportunity_valuation_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    valuation_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunity_valuations.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
