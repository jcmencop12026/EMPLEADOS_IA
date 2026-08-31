"""Modelos — Centro de Negocios EIAAX (extensión 1280 sin motor paralelo)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text
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
    precio_presentado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_contratado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    approval_policy_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    pdf_document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_documents.id"), nullable=True)
    presented_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    precio_presentado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
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


class NegocioApprovalPolicy(Base):
    __tablename__ = "negocio_approval_policies"

    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), primary_key=True)
    levels_json: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class NegocioApprovalRecord(Base):
    __tablename__ = "negocio_approval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nivel: Mapped[str] = mapped_column(String(40), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NegocioProposalDocument(Base):
    __tablename__ = "negocio_proposal_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_versions.id"), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False, default="application/pdf")
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    generated_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NegocioContractRecord(Base):
    __tablename__ = "negocio_contract_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_versions.id"), nullable=True)
    version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_documents.id"), nullable=True)
    precio_contratado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    modelo_comercial: Mapped[str | None] = mapped_column(String(40), nullable=True)
    condiciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    proximo_paso: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fecha_contratacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


class NegocioSyncLog(Base):
    __tablename__ = "negocio_sync_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=True, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String(30), nullable=False)
    field_name: Mapped[str] = mapped_column(String(80), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NegocioPricePhaseRecord(Base):
    __tablename__ = "negocio_price_phase_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    fase: Mapped[str] = mapped_column(String(20), nullable=False)
    monto: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
