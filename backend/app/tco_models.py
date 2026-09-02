"""Modelos — TCO y ecosistema de aliados (1320)."""

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


class TcoCategoriaCosto(Base):
    """Catálogo parametrizable de categorías de costo."""

    __tablename__ = "tco_categorias_costo"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_tco_categoria_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_global: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoProveedorAliado(Base):
    """Proveedor o aliado externo — distinto de organización cliente."""

    __tablename__ = "tco_proveedores_aliados"
    __table_args__ = (
        UniqueConstraint("organization_id", "codigo", name="uq_tco_proveedor_org_codigo"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    contacto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgo_nivel: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    riesgo_criterio: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgo_justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgo_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    riesgo_responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TcoContratoCondicion(Base):
    """Condiciones contractuales simplificadas de un proveedor."""

    __tablename__ = "tco_contratos_condiciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proveedor_id: Mapped[str] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=False, index=True)
    moneda: Mapped[str] = mapped_column(String(8), nullable=False, default="COP")
    tipo_tarifa: Mapped[str | None] = mapped_column(String(30), nullable=True)
    minimo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    maximo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    compromiso: Mapped[str | None] = mapped_column(Text, nullable=True)
    descuento_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    condiciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    sla: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="VIGENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TcoTarifa(Base):
    """Tarifa de un proveedor — soporta tramos por volumen."""

    __tablename__ = "tco_tarifas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proveedor_id: Mapped[str] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    unidad: Mapped[str] = mapped_column(String(40), nullable=False, default="unidad")
    moneda: Mapped[str] = mapped_column(String(8), nullable=False, default="COP")
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="UNIDAD")
    monto_base: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    periodicidad: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vigente_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigente_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="VIGENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TcoTarifaTramo(Base):
    """Tramo escalonado de tarifa por volumen."""

    __tablename__ = "tco_tarifa_tramos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    tarifa_id: Mapped[str] = mapped_column(String(36), ForeignKey("tco_tarifas.id"), nullable=False, index=True)
    desde_unidades: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    hasta_unidades: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    precio_unidad: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TcoCosto(Base):
    """Línea de costo — fijo, variable o único; estimado, real o proyectado."""

    __tablename__ = "tco_costos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    categoria_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_categorias_costo.id"), nullable=True)
    proveedor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_costo: Mapped[str] = mapped_column(String(20), nullable=False, default="FIJO")
    naturaleza: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADO")
    periodicidad: Mapped[str] = mapped_column(String(30), nullable=False, default="MENSUAL")
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cantidad: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    moneda: Mapped[str] = mapped_column(String(8), nullable=False, default="COP")
    tasa_conversion: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    tasa_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monto_convertido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    moneda_destino: Mapped[str | None] = mapped_column(String(8), nullable=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=True)
    finops_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    integracion_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    periodo_ref: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vigente_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigente_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TcoCostoHistorico(Base):
    """Histórico de cambios de costo — no sobrescribe silenciosamente."""

    __tablename__ = "tco_costos_historico"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    costo_id: Mapped[str] = mapped_column(String(36), ForeignKey("tco_costos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoDistribucion(Base):
    """Distribución de costo compartido entre entidades."""

    __tablename__ = "tco_distribuciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    costo_id: Mapped[str] = mapped_column(String(36), ForeignKey("tco_costos.id"), nullable=False, index=True)
    metodo: Mapped[str] = mapped_column(String(30), nullable=False)
    criterio_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    asignaciones_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoSnapshot(Base):
    """Snapshot de TCO por organización, período o escenario."""

    __tablename__ = "tco_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    periodo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    escenario: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="ESTIMADO")
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    desglose_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingreso: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    margen_bruto: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    margen_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    punto_equilibrio: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    finops_ia: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    finops_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    proveedores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    concentracion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    alertas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=True)
    es_simulacion: Mapped[bool] = mapped_column(Boolean, default=False)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoAlianza(Base):
    """Alianza estratégica con proveedor o tercero."""

    __tablename__ = "tco_alianzas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proveedor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    alcance: Mapped[str | None] = mapped_column(Text, nullable=True)
    vigencia_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vigencia_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    beneficios_esperados: Mapped[str | None] = mapped_column(Text, nullable=True)
    costos_esperados: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    responsabilidades: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PROPUESTA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class TcoSimulacion(Base):
    """Simulación no destructiva de escenarios de costo."""

    __tablename__ = "tco_simulaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    parametros_json: Mapped[str] = mapped_column(Text, nullable=False)
    resultado_json: Mapped[str] = mapped_column(Text, nullable=False)
    confirmada: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoAlertaEconomica(Base):
    """Alerta económica preparada — sin motor paralelo de notificaciones."""

    __tablename__ = "tco_alertas_economicas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    datos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TcoAuditoria(Base):
    """Auditoría de acciones TCO y ecosistema."""

    __tablename__ = "tco_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
