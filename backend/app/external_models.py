"""Modelos — Inteligencia externa y oportunidades estratégicas (1240)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationExternalContext(Base):
    """Contexto parametrizable de la empresa para evaluar relevancia externa."""

    __tablename__ = "organization_external_context"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False, unique=True, index=True
    )
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mercado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    productos_servicios: Mapped[str | None] = mapped_column(Text, nullable=True)
    geografias: Mapped[str | None] = mapped_column(Text, nullable=True)
    clientes_objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    procesos_clave: Mapped[str | None] = mapped_column(Text, nullable=True)
    estrategia: Mapped[str | None] = mapped_column(Text, nullable=True)
    dominios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    freshness_recent_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    freshness_stale_days: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ExternalSource(Base):
    """Catálogo de fuentes externas — enriquece SignalSource cuando aplica."""

    __tablename__ = "external_sources"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_external_source_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    signal_source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("signal_sources.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    ingestion_channel: Mapped[str] = mapped_column(String(40), nullable=False)
    url_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pais_region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    frecuencia_esperada: Mapped[str | None] = mapped_column(String(60), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVA")
    confiabilidad: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.5)
    ultima_actualizacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ExternalSignalExtension(Base):
    """Extensión 1:1 de ProactiveSignal para inteligencia externa."""

    __tablename__ = "external_signal_extensions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("proactive_signals.id"), nullable=False, unique=True, index=True
    )
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    external_source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("external_sources.id"), nullable=True)
    ambito: Mapped[str] = mapped_column(String(20), nullable=False, default="EXTERNO")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    freshness_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SIN FECHA VERIFICABLE")
    classification: Mapped[str] = mapped_column(String(30), nullable=False, default="INFORMACIÓN")
    relevance: Mapped[str] = mapped_column(String(30), nullable=False, default="POSIBLEMENTE RELEVANTE")
    hecho_observado: Mapped[str | None] = mapped_column(Text, nullable=True)
    interpretacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    hipotesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    oportunidad_propuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.5)
    is_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    competitor_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    technology_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    demand_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    valuation_contract_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    diagnostic_contract_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ExternalEvidence(Base):
    """Evidencia estructurada — conserva procedencia del dato externo."""

    __tablename__ = "external_evidence"
    __table_args__ = (UniqueConstraint("organization_id", "dedupe_hash", name="uq_external_evidence_dedupe"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    signal_id: Mapped[str] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    external_source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("external_sources.id"), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    structured_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
