"""Modelos de gobierno operacional EIAAX — acciones, aprobaciones, visibilidad e IA."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


TIPOS_ACCION = frozenset({"LECTURA", "ANALISIS", "PROPUESTA", "EJECUCION"})
ESTADOS_SOLICITUD = frozenset(
    {"SOLICITADA", "PENDIENTE", "APROBADA", "RECHAZADA", "EJECUTADA", "FALLIDA", "CANCELADA"}
)
DOMINIOS_VISIBILIDAD = frozenset(
    {"evaluacion", "hallazgo", "indicador", "oportunidad", "informe", "plan", "resultado"}
)


class GobiernoAccionPolicy(Base):
    __tablename__ = "gobierno_accion_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo_accion: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recurso_tipo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    criticidad: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    requiere_aprobacion_humana: Mapped[bool] = mapped_column(Boolean, default=False)
    rol_aprobador: Mapped[str | None] = mapped_column(String(60), nullable=True)
    capacidad_externa: Mapped[str | None] = mapped_column(String(120), nullable=True)
    empleado_ia_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    auto_ejecutar: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GobiernoAccionSolicitud(Base):
    __tablename__ = "gobierno_accion_solicitudes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tipo_accion: Mapped[str] = mapped_column(String(20), nullable=False)
    recurso_tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    recurso_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    criticidad: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="SOLICITADA", index=True)
    actor_tipo: Mapped[str] = mapped_column(String(20), default="HUMANO")
    solicitado_por: Mapped[str] = mapped_column(String(36), nullable=False)
    aprobado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    rechazado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    motivo_solicitud: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_request_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("approval_requests.id"), nullable=True)
    resultado_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GobiernoVisibilidadLog(Base):
    __tablename__ = "gobierno_visibilidad_log"
    __table_args__ = (Index("ix_gob_vis_dom_ctx", "dominio", "contexto_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dominio: Mapped[str] = mapped_column(String(40), nullable=False)
    contexto_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    objeto_tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    objeto_id: Mapped[str] = mapped_column(String(36), nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class GobiernoIaPolicy(Base):
    __tablename__ = "gobierno_ia_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    proveedores_permitidos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    modelos_permitidos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    acciones_permitidas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    herramientas_permitidas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    limites_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    requiere_aprobacion_humana_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    datos_permitidos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_ejecutar: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GobiernoEvento(Base):
    __tablename__ = "gobierno_eventos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    accion: Mapped[str] = mapped_column(String(120), nullable=False)
    recurso_tipo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    recurso_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(40), nullable=True)
    aprobacion_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gobierno_accion_solicitudes.id"), nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(40), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
