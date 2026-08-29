"""Modelos — Modelo comercial basado en valor (1280)."""

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


class CommercialPlan(Base):
    """Plan comercial parametrizable — global o por organización."""

    __tablename__ = "commercial_plans"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_commercial_plan_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    credential_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="IA_ADMINISTRADA")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    precio_base_mensual: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    margen_minimo_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0.15"))
    fraccion_valor_sugerida: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    precio_minimo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_maximo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    consumo_ia_incluido_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    presupuesto_ia_incluido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    excedente_ia_por_millon: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    alerta_consumo_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    bloqueo_excedente: Mapped[bool] = mapped_column(Boolean, default=False)
    limits_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommercialProposal(Base):
    """Propuesta comercial trazable a valor económico."""

    __tablename__ = "commercial_proposals"
    __table_args__ = (
        UniqueConstraint("organization_id", "codigo", name="uq_commercial_proposal_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="BORRADOR", index=True)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_plans.id"), nullable=True)
    credential_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="IA_ADMINISTRADA")
    escenario_recomendado: Mapped[str] = mapped_column(String(20), nullable=False, default="BASE")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    valor_total_esperado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_atribuible_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    costo_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_sugerido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_final: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    beneficio_neto_cliente: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    roi_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    payback_meses: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    pct_valor_conservado_cliente: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    pct_valor_capturado_empleados_ia: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    margen_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supuestos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    traceability_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostic_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommercialProposalValue(Base):
    """Componente de valor con naturaleza, categoría y atribución."""

    __tablename__ = "commercial_proposal_values"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    valuation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    linea_base_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    alcance: Mapped[str] = mapped_column(String(20), nullable=False, default="INTERNO")
    naturaleza: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADO")
    external_intelligence_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    valor_bruto: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    atribucion_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))
    valor_atribuible: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    criterio_atribucion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialProposalScenario(Base):
    """Escenario conservador / base / alto."""

    __tablename__ = "commercial_proposal_scenarios"
    __table_args__ = (
        UniqueConstraint("proposal_id", "scenario_type", name="uq_proposal_scenario_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_esperado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_atribuible: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    probabilidad: Mapped[Decimal | None] = mapped_column(Numeric(7, 6), nullable=True)
    costo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    periodo_meses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    riesgo_nivel: Mapped[str | None] = mapped_column(String(20), nullable=True)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_recomendado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialProposalCost(Base):
    """Desglose de costos EMPLEADOS_IA."""

    __tablename__ = "commercial_proposal_costs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    categoria: Mapped[str] = mapped_column(String(40), nullable=False)
    clase_costo: Mapped[str] = mapped_column(String(30), nullable=False, default="COSTO_INTERNO")
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    finops_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_recurrente: Mapped[bool] = mapped_column(Boolean, default=False)
    periodo_meses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialProposalPriceHistory(Base):
    """Historial precio sugerido vs final — aprobación humana."""

    __tablename__ = "commercial_proposal_price_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    precio_sugerido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_modificado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialDoubleCountAlert(Base):
    """Alerta de posible doble conteo de valor."""

    __tablename__ = "commercial_double_count_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="ADVERTENCIA")
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    value_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resuelto: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
