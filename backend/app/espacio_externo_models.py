"""Espacio externo controlado — empresa/prospecto/cliente (V1)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


ESTADOS_RELACION = frozenset({
    "PROSPECTO_EVALUACION",
    "PROSPECTO_RESULTADOS",
    "CLIENTE_CONTRATADO",
})

ESTADOS_PUBLICACION = frozenset({
    "PRIVADO",
    "PREPARADO_PRESENTAR",
    "PUBLICADO_EMPRESA",
})

PAQUETES_PUBLICACION = frozenset({
    "INICIO",
    "INFORMACION",
    "RESULTADOS",
    "PROPUESTA",
    "IMPLEMENTACION",
    "EMPLEADOS_IA",
    "INFORMES",
    "SOPORTE",
})

# Alcance de audiencia sobre una misma publicación/version — NO duplica datos.
AUDIENCIAS_PUBLICACION = frozenset({
    "GERENCIA",
    "OPERACION",
    "SISTEMAS",
    "FINANCIERO",
})

CAPACIDADES_CONTRATO_CLIENTE = frozenset({
    "IMPLEMENTACION",
    "EMPLEADOS_IA",
    "RESULTADOS",
    "INFORMES",
    "SOPORTE",
})

ROLES_ACCESO_EXTERNO = frozenset({"PROSPECTO", "CLIENTE"})

FUENTES_INFORMACION = frozenset({
    "SUMINISTRADA_EMPRESA",
    "PUBLICA_EXTERNA",
    "INFERIDA_EIAAX",
    "ESTIMADA",
    "VALIDADA",
})

ESTADOS_VALIDACION_EXTERNA = frozenset({
    "RECIBIDO",
    "EN_VALIDACION",
    "VALIDADO",
    "REQUIERE_COMPLEMENTO",
})


class EntidadEmpresa(Base):
    """Empresa/prospecto/cliente vinculada a un expediente — evoluciona sin duplicar."""

    __tablename__ = "entidades_empresa"
    __table_args__ = (
        UniqueConstraint("organization_id", "expediente_id", name="uq_entidad_expediente"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    contacto_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado_relacion: Mapped[str] = mapped_column(String(30), nullable=False, default="PROSPECTO_EVALUACION", index=True)
    contrato_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    proyecto_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    capacidades_contrato_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EntidadEmpresaAcceso(Base):
    """Acceso limitado de usuario externo a un espacio empresa."""

    __tablename__ = "entidades_empresa_acceso"
    __table_args__ = (
        UniqueConstraint("entidad_id", "user_id", name="uq_entidad_user_acceso"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    entidad_id: Mapped[str] = mapped_column(String(36), ForeignKey("entidades_empresa.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rol_externo: Mapped[str] = mapped_column(String(20), nullable=False, default="PROSPECTO")
    capacidades_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    invited_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    revoked_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmpresaPublicacion(Base):
    """Estado de publicación por paquete — versionado e inmutable al compartir."""

    __tablename__ = "empresa_publicaciones"
    __table_args__ = (
        Index("ix_emp_pub_exp_paquete", "expediente_id", "paquete"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    entidad_id: Mapped[str] = mapped_column(String(36), ForeignKey("entidades_empresa.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    paquete: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PRIVADO", index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    destinatario: Mapped[str | None] = mapped_column(String(300), nullable=True)
    audiencia: Mapped[str | None] = mapped_column(String(30), nullable=True)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    publicado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    publicado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmpresaPublicacionHistorial(Base):
    """Historial de transiciones de publicación."""

    __tablename__ = "empresa_publicacion_historial"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    publicacion_id: Mapped[str] = mapped_column(String(36), ForeignKey("empresa_publicaciones.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    destinatario: Mapped[str | None] = mapped_column(String(300), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EvaluacionEntregaExterna(Base):
    """Flujo solicitud → entrega → validación para información externa."""

    __tablename__ = "evaluacion_entregas_externas"
    __table_args__ = (
        Index("ix_entrega_ext_exp", "expediente_id", "solicitado_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    entidad_id: Mapped[str] = mapped_column(String(36), ForeignKey("entidades_empresa.id"), nullable=False, index=True)
    informacion_item_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_informacion.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="SOLICITADO")
    fuente_tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contenido: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    solicitado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    entregado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    validado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    solicitado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    entregado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suficiencia_minima_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
