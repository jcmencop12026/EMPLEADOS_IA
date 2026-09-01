"""Expediente de evaluación empresarial EIAAX — Bloque Producto 1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


EVALUACION_ESTADOS = frozenset({
    "BORRADOR",
    "EN_CURSO",
    "PRELIMINAR",
    "DIAGNOSTICA",
    "PROFUNDA",
    "CERRADO",
    "ARCHIVADO",
})

EVALUACION_NIVELES = frozenset({"PRELIMINAR", "DIAGNOSTICA", "PROFUNDA"})

INFO_ESTADOS = frozenset({"RECIBIDO", "INCOMPLETO", "PENDIENTE", "OPCIONAL"})

CONFIANZA_NIVELES = frozenset({"ALTA", "MEDIA", "BAJA"})

HALLAZGO_TIPOS = frozenset({"HECHO", "INFERENCIA", "PROYECCION", "RECOMENDACION"})


class EvaluacionExpediente(Base):
    """Contenedor de evaluación empresarial — orquesta motores existentes."""

    __tablename__ = "evaluaciones_expediente"
    __table_args__ = (
        Index("ix_eval_exp_org_codigo", "organization_id", "codigo", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    entidad_nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    entidad_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    necesidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="BORRADOR", index=True)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False, default="PRELIMINAR")
    confianza_global: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    porcentaje_informacion: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_potencial: Mapped[str | None] = mapped_column(String(40), nullable=True)
    diagnostic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostics.id"), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notas_internas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EvaluacionInformacionItem(Base):
    """Requisito de información adaptativo."""

    __tablename__ = "evaluaciones_informacion"
    __table_args__ = (
        Index("ix_eval_info_exp_campo", "expediente_id", "campo", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    campo: Mapped[str] = mapped_column(String(80), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    obligatorio: Mapped[bool] = mapped_column(Boolean, default=True)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    por_que: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_precision: Mapped[str | None] = mapped_column(Text, nullable=True)
    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EvaluacionHallazgo(Base):
    """Hallazgo con confianza, evidencia y visibilidad para entidad."""

    __tablename__ = "evaluaciones_hallazgos"
    __table_args__ = (
        Index("ix_eval_hall_exp", "expediente_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_contenido: Mapped[str] = mapped_column(String(20), nullable=False, default="HECHO")
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    explicacion_confianza: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    origen: Mapped[str | None] = mapped_column(String(120), nullable=True)
    impacto_resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    visible_entidad: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    es_problema_original: Mapped[bool] = mapped_column(Boolean, default=False)
    diagnostic_finding_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EvaluacionOportunidadLink(Base):
    """Vínculo expediente ↔ oportunidad existente."""

    __tablename__ = "evaluaciones_oportunidad_links"
    __table_args__ = (
        Index("ix_eval_opp_link", "expediente_id", "opportunity_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_hallazgos.id"), nullable=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="VINCULADA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvaluacionVisibilidadLog(Base):
    """Auditoría de cambios de visibilidad para entidad."""

    __tablename__ = "evaluaciones_visibilidad_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    objeto_tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    objeto_id: Mapped[str] = mapped_column(String(36), nullable=False)
    visible_entidad: Mapped[bool] = mapped_column(Boolean, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
