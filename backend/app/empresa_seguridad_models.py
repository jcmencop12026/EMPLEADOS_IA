"""Modelos transversales — clasificación, evidencia y extensiones de visibilidad."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Alias conceptuales → códigos persistidos en gov_classification_levels
CLASIFICACION_ALIASES: dict[str, str] = {
    "PUBLICA": "PUBLICO",
    "INTERNA": "INTERNO",
    "CONFIDENCIAL": "CONFIDENCIAL",
    "RESTRINGIDA": "RESTRINGIDO",
    "PUBLICO": "PUBLICO",
    "INTERNO": "INTERNO",
    "RESTRINGIDO": "RESTRINGIDO",
}

NIVELES_VISIBILIDAD = frozenset(
    {"INTERNO_EIAAX", "VISIBLE_ENTIDAD", "COMPARTIDO_ESPECIFICO", "RESTRINGIDO"}
)

TIPOS_OBJETO_CLASIFICABLE = frozenset(
    {
        "documento",
        "evidencia",
        "informe",
        "resultado",
        "dato",
        "artefacto",
        "salida_ia",
        "hallazgo",
        "indicador",
        "catalogo",
    }
)

TIPOS_EVIDENCIA = frozenset(
    {"documento", "referencia", "hallazgo", "autorizacion", "registro", "enlace_externo"}
)

ROLES_VINCULO_EVIDENCIA = frozenset(
    {"SOPORTE", "HALLAZGO", "INDICADOR", "DECISION", "APROBACION", "ACCION", "RESULTADO", "INFORME"}
)


class EmpresaObjetoClasificacion(Base):
    """Clasificación transversal asociada a cualquier objeto de negocio."""

    __tablename__ = "empresa_objeto_clasificacion"
    __table_args__ = (
        UniqueConstraint("organization_id", "objeto_tipo", "objeto_id", name="uq_emp_cls_obj"),
        Index("ix_emp_cls_tipo", "objeto_tipo", "objeto_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    objeto_tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    objeto_id: Mapped[str] = mapped_column(String(36), nullable=False)
    classification_level_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("gov_classification_levels.id"), nullable=False
    )
    asignado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmpresaEvidenciaVinculo(Base):
    """Vínculo de evidencia a objetos de decisión/acción — sin duplicar almacenamiento."""

    __tablename__ = "empresa_evidencia_vinculo"
    __table_args__ = (
        Index("ix_emp_evid_obj", "objeto_tipo", "objeto_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo_evidencia: Mapped[str] = mapped_column(String(40), nullable=False)
    referencia: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    objeto_tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    objeto_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rol_vinculo: Mapped[str] = mapped_column(String(40), default="SOPORTE")
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    creado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
