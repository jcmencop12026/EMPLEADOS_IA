"""Modelos — Presentación ejecutiva real y configuración de informes comerciales (V1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


ESTADOS_PUBLICACION = frozenset({
    "PRIVADO",
    "PREPARADO_PARA_PRESENTAR",
    "PUBLICADO_A_EMPRESA",
})


class PresentacionPublicacion(Base):
    """Estado de publicación de presentación ejecutiva — adapter fail-closed."""

    __tablename__ = "presentacion_publicacion"
    __table_args__ = (
        UniqueConstraint("organization_id", "expediente_id", name="uq_pres_pub_org_exp"),
        Index("ix_pres_pub_org_estado", "organization_id", "estado"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    expediente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(40), nullable=False, default="PRIVADO")
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    publicado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class InformeComercialConfig(Base):
    """Configuración de informes periódicos comerciales — integración MB-11."""

    __tablename__ = "informes_comerciales_config"
    __table_args__ = (Index("ix_inf_com_org_activo", "organization_id", "activo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    expediente_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True
    )
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    audiencia: Mapped[str] = mapped_column(String(30), nullable=False, default="GERENCIA")
    periodicidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MENSUAL")
    destinatarios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    enlace_seguro: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comm_rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comm_rules.id"), nullable=True)
    ultimo_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proximo_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="PENDIENTE_INTEGRACION", nullable=False)
    error_ultimo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
