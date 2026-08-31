"""Modelos — Centro de Información y Comunicaciones (MB-11)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class CommChannel(Base):
    __tablename__ = "comm_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO", nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    uso_permitido: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (UniqueConstraint("organization_id", "nombre", name="uq_comm_channel_org_nombre"),)


class CommTemplate(Base):
    __tablename__ = "comm_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(60), nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    tipo_comunicacion: Mapped[str] = mapped_column(String(60), nullable=False)
    canal_tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    idioma: Mapped[str] = mapped_column(String(10), default="es", nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (UniqueConstraint("organization_id", "codigo", name="uq_comm_template_org_codigo"),)


class CommTemplateVersion(Base):
    __tablename__ = "comm_template_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("comm_templates.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    asunto: Mapped[str | None] = mapped_column(String(300), nullable=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVA", nullable=False)
    vigencia_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creador_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_comm_template_version"),
    )


class CommRule(Base):
    __tablename__ = "comm_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    condicion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    destinatario_tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    destinatario_regla: Mapped[str] = mapped_column(String(120), nullable=False)
    template_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("comm_template_versions.id"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(36), ForeignKey("comm_channels.id"), nullable=False)
    accion: Mapped[str] = mapped_column(String(30), default="ENVIAR", nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    antispam_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    obligatoria: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommMessage(Base):
    __tablename__ = "comm_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), default="BORRADOR", nullable=False)
    tipo_comunicacion: Mapped[str] = mapped_column(String(60), nullable=False)
    channel_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comm_channels.id"), nullable=True)
    template_version_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comm_template_versions.id"), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comm_rules.id"), nullable=True)
    destinatario_tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    destinatario_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    destinatario_externo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    asunto: Mapped[str | None] = mapped_column(String(300), nullable=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    idioma: Mapped[str] = mapped_column(String(10), default="es", nullable=False)
    programada_para: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    origen: Mapped[str] = mapped_column(String(30), default="MANUAL", nullable=False)
    origen_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_intentos: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    proximo_intento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    creador_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    enviada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entregada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_comm_msg_idempotency"),
    )


class CommDeliveryAttempt(Base):
    __tablename__ = "comm_delivery_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("comm_messages.id"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    intento_num: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    causa: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommPreference(Base):
    __tablename__ = "comm_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    canales_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    horario_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    idioma: Mapped[str] = mapped_column(String(10), default="es", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_comm_pref_org_user"),
    )


class CommDedup(Base):
    __tablename__ = "comm_dedup"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(128), nullable=False)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("comm_messages.id"), nullable=False)
    ventana_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "dedup_key", name="uq_comm_dedup_org_key"),
    )
