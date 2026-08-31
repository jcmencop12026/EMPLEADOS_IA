"""Modelos — MB-03 Partners / Aliados comerciales."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


PARTNER_ESTADOS = frozenset({"BORRADOR", "ACTIVO", "INACTIVO", "SUSPENDIDO"})
GRANT_ESTADOS = frozenset({"ACTIVO", "REVOCADO", "SUSPENDIDO"})
PARTNER_USER_ROLES = frozenset({"ADMIN", "OPERADOR", "LECTOR"})
PARTNER_SCOPE_CODES = frozenset({
    "organizacion.read",
    "cc.view",
    "trabajo.view",
    "evaluacion.view",
    "oportunidades.view",
})


class Partner(Base):
    """Entidad Partner/Aliado comercial — ámbito plataforma."""

    __tablename__ = "partners"
    __table_args__ = (UniqueConstraint("codigo", name="uq_partner_codigo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    razon_social: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR", index=True)
    tipo_relacion: Mapped[str] = mapped_column(String(40), nullable=False, default="CONSULTOR")
    contacto_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contacto_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contacto_telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    alcance_descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas_internas: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class PartnerOrganizationGrant(Base):
    """Acceso explícito y revocable Partner → Organización."""

    __tablename__ = "partner_organization_grants"
    __table_args__ = (
        UniqueConstraint("partner_id", "organization_id", name="uq_partner_org_grant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    partner_id: Mapped[str] = mapped_column(String(36), ForeignKey("partners.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO", index=True)
    alcance_json: Mapped[str] = mapped_column(Text, nullable=False, default='["organizacion.read"]')
    permisos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    revoked_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class PartnerUserMembership(Base):
    """Usuario asociado a un partner con rol operativo."""

    __tablename__ = "partner_user_memberships"
    __table_args__ = (
        UniqueConstraint("partner_id", "user_id", name="uq_partner_user"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    partner_id: Mapped[str] = mapped_column(String(36), ForeignKey("partners.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="OPERADOR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PartnerAuditEvent(Base):
    """Trazabilidad de operaciones sobre partners."""

    __tablename__ = "partner_audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    partner_id: Mapped[str] = mapped_column(String(36), ForeignKey("partners.id"), nullable=False, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
