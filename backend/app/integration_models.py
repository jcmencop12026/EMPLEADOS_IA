"""Modelos — Integraciones reales y conectores (1330)."""

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


class IntegrationConnector(Base):
    """Conector empresarial configurable por organización."""

    __tablename__ = "integration_connectors"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_integration_connector_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    connector_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR", index=True)
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="NINGUNA")
    secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapping_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    destination_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    signal_source_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trigger_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    retry_max: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    retry_delay_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=30000)
    max_response_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=5_242_880)
    circuit_breaker_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    circuit_breaker_cooldown_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    circuit_open_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    webhook_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gov_catalog_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("gov_catalog_entries.id"), nullable=True, index=True
    )
    allow_internal_urls: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class IntegrationExecution(Base):
    """Historial de ejecución de conector."""

    __tablename__ = "integration_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    connector_id: Mapped[str] = mapped_column(String(36), ForeignKey("integration_connectors.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    trigger_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_valid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    result_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


class IntegrationWebhookEvent(Base):
    """Evento webhook entrante con deduplicación."""

    __tablename__ = "integration_webhook_events"
    __table_args__ = (UniqueConstraint("organization_id", "dedupe_key", name="uq_webhook_dedupe"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    connector_id: Mapped[str] = mapped_column(String(36), ForeignKey("integration_connectors.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RECIBIDO")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
