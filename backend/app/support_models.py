"""Modelos — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SupportSlaPolicy(Base):
    __tablename__ = "support_sla_policies"
    __table_args__ = (UniqueConstraint("organization_id", "nombre", name="uq_support_sla_org_nombre"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    prioridad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    minutos_primera_respuesta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minutos_resolucion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    horario_servicio_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SupportCase(Base):
    __tablename__ = "support_cases"
    __table_args__ = (
        UniqueConstraint("organization_id", "numero", name="uq_support_case_org_numero"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(80), nullable=True)
    asunto: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    prioridad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    impacto: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIO")
    urgencia: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="NUEVO", index=True)
    solicitante_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    grupo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    modulo_relacionado: Mapped[str | None] = mapped_column(String(60), nullable=True)
    entidad_relacionada: Mapped[str | None] = mapped_column(String(120), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    origen_tipo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    origen_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resolucion: Mapped[str | None] = mapped_column(Text, nullable=True)
    sla_policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("support_sla_policies.id"), nullable=True)
    primera_respuesta_limite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolucion_limite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    primera_respuesta_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_limite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resuelto_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cerrado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidencia_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class SupportCaseHistory(Base):
    __tablename__ = "support_case_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("support_cases.id"), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    usuario_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SupportCaseComment(Base):
    __tablename__ = "support_case_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("support_cases.id"), nullable=False, index=True)
    usuario_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    es_interno: Mapped[bool] = mapped_column(Boolean, default=False)
    evidencia_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SupportAutoDedup(Base):
    """Ventana de deduplicación para origen automático."""

    __tablename__ = "support_auto_dedup"
    __table_args__ = (
        UniqueConstraint("organization_id", "dedup_key", name="uq_support_dedup_org_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dedup_key: Mapped[str] = mapped_column(String(128), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("support_cases.id"), nullable=False)
    origen_tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    origen_id: Mapped[str] = mapped_column(String(120), nullable=False)
    ventana_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
