"""Modelos — Segmentación, paquetes y catálogo comercial (1310)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CommercialSector(Base):
    """Sector/vertical configurable — no hardcodeado en lógica."""

    __tablename__ = "commercial_sectors"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_commercial_sector_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommercialSegment(Base):
    """Segmento de cliente con dimensiones configurables."""

    __tablename__ = "commercial_segments"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_commercial_segment_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    sector_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_sectors.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimensions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class OrganizationCommercialProfile(Base):
    """Perfil comercial de una organización."""

    __tablename__ = "organization_commercial_profiles"
    __table_args__ = (UniqueConstraint("organization_id", name="uq_org_commercial_profile"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    segment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_segments.id"), nullable=True)
    sector_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_sectors.id"), nullable=True)
    subsector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tamano: Mapped[str | None] = mapped_column(String(40), nullable=True)
    madurez_digital: Mapped[str | None] = mapped_column(String(40), nullable=True)
    complejidad_operativa: Mapped[str | None] = mapped_column(String(40), nullable=True)
    num_usuarios: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_empleados_ia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volumen_operaciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_integraciones: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consumo_ia_estimado: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nivel_soporte: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sla_requerido: Mapped[str | None] = mapped_column(String(40), nullable=True)
    riesgo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    potencial_valor: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    presupuesto_estimado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommercialCapability(Base):
    """Capacidad estructurada del catálogo."""

    __tablename__ = "commercial_capabilities"
    __table_args__ = (UniqueConstraint("code", name="uq_commercial_capability_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialPackage(Base):
    """Paquete comercial — combina límites y capacidades sobre un plan base."""

    __tablename__ = "commercial_packages"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_commercial_package_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_plans.id"), nullable=True)
    segment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_segments.id"), nullable=True)
    sector_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_sectors.id"), nullable=True)
    base_package_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_packages.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    empleados_ia_incluidos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usuarios_incluidos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    automatizaciones_incluidas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consumo_ia_incluido_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    presupuesto_ia_incluido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    integraciones_incluidas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    almacenamiento_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_nivel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    soporte_nivel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    excedente_ia_por_millon: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    alerta_consumo_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    bloqueo_excedente: Mapped[bool] = mapped_column(Boolean, default=False)
    credential_modes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    capabilities_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    servicios_incluidos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    servicios_opcionales_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_overrides_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_estimado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CommercialPackageVersion(Base):
    """Snapshot versionado de un paquete."""

    __tablename__ = "commercial_package_versions"
    __table_args__ = (UniqueConstraint("package_id", "version_number", name="uq_package_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    package_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_packages.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialPlanVersion(Base):
    """Snapshot versionado de un plan."""

    __tablename__ = "commercial_plan_versions"
    __table_args__ = (UniqueConstraint("plan_id", "version_number", name="uq_plan_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("commercial_plans.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CommercialDiscount(Base):
    """Descuento controlado con trazabilidad."""

    __tablename__ = "commercial_discounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_descuento: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    valor_original: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    valor_final: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
