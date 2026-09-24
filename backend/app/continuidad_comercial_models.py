"""Modelos — Continuidad comercial y operacional EIAAX (1720)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContinuidadCambioAlcance(Base):
    """Solicitud de cambio de alcance post-contrato."""

    __tablename__ = "continuidad_cambios_alcance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    proyecto_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=True, index=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_contract_records.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="SOLICITADO", index=True)
    solicitud: Mapped[str] = mapped_column(Text, nullable=False)
    analisis: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    negociacion_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("negocio_negotiation_entries.id"), nullable=True
    )
    nueva_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("negocio_proposal_versions.id"), nullable=True
    )
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class NegocioContractClosure(Base):
    """Cierre contractual / offboarding mínimo empresarial."""

    __tablename__ = "negocio_contract_closures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(String(36), ForeignKey("negocio_contract_records.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False)
    proyecto_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=True)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="INICIADO")
    pendientes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    empleados_retirar_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    accesos_retirar_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    exportaciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmacion: Mapped[bool] = mapped_column(Boolean, default=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
