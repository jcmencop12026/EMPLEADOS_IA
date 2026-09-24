"""Modelos — Flujo comercial V1 EIAAX (1730)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ComercialPresentacionEjecutiva(Base):
    """Presentación ejecutiva interna — selección de hallazgos y oportunidades."""

    __tablename__ = "comercial_presentaciones_ejecutivas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    evaluacion_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=True, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    hallazgos_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    oportunidades_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    secciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ComercialInstrumentoContractual(Base):
    """Instrumento contractual modular — no software jurídico completo."""

    __tablename__ = "comercial_instrumentos_contractuales"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    contract_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_contract_records.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    contenido_resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    documento_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("negocio_proposal_documents.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ComercialCompromisoGarantia(Base):
    """Compromiso/garantía clasificado — sin garantizar resultados externos."""

    __tablename__ = "comercial_compromisos_garantia"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=False, index=True)
    tipo_compromiso: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    baseline: Mapped[str | None] = mapped_column(Text, nullable=True)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencias_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    atribucion: Mapped[str | None] = mapped_column(Text, nullable=True)
    cumplimiento_estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
