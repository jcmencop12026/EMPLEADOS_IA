"""Modelos — Centro de Negocios EIAAX (extensión 1280 sin motor paralelo)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NegocioProposalExtension(Base):
    """Extensión 1:1 de propuesta comercial — perspectivas, origen, IA, economía."""

    __tablename__ = "negocio_proposal_extensions"

    proposal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commercial_proposals.id"), primary_key=True
    )
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True, index=True)
    evaluacion_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    modelo_comercial: Mapped[str | None] = mapped_column(String(40), nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    proximo_paso: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    perspectivas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    documento_cliente_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    documento_interno_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ia_consumo_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    economic_recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("economic_price_recommendations.id"), nullable=True
    )
    implementacion_proyecto_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class NegocioProposalVersion(Base):
    """Versión inmutable de propuesta — no modifica silenciosamente lo presentado."""

    __tablename__ = "negocio_proposal_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False)
    estado_comercial: Mapped[str] = mapped_column(String(30), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    documento_cliente_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NegocioNegotiationEntry(Base):
    """Registro de negociación — no CRM completo."""

    __tablename__ = "negocio_negotiation_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    version_presentada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_presentacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interlocutor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    cambios_solicitados: Mapped[str | None] = mapped_column(Text, nullable=True)
    nueva_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_versions.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="ABIERTA")
    proximo_paso: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NegocioPriceDecision(Base):
    """Decisión humana sobre precio recomendado del Motor Económico."""

    __tablename__ = "negocio_price_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    recommendation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("economic_price_recommendations.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    precio_recomendado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_decidido: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
