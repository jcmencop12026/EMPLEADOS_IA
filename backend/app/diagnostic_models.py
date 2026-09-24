"""Modelos transversales — Diagnóstico multidominio (1220)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


DIAGNOSTIC_DOMAINS = frozenset({
    "FINANCIERO",
    "OPERATIVO",
    "COMERCIAL",
    "SERVICIO",
    "CALIDAD",
    "TALENTO_HUMANO",
    "TECNOLOGIA",
    "LOGISTICA",
    "CUMPLIMIENTO",
    "ASISTENCIAL_SALUD",
    "EXTERNO_MERCADO",
    "EXTERNO_REGULACION",
    "EXTERNO_TECNOLOGIA",
    "EXTERNO_DEMANDA",
    "OTRO",
})

FINDING_CONTENT_TYPES = frozenset({"HECHO", "INTERPRETACION"})
CAUSE_TYPES = frozenset({"CONFIRMADA", "PROBABLE", "HIPOTESIS"})
DIAGNOSTIC_STATES = frozenset({"BORRADOR", "GENERADO", "VALIDADO", "ARCHIVADO"})
DIRECTION_TYPES = frozenset({"SUBIR", "BAJAR", "ESTABLE", "CUALQUIERA"})


class DiagnosticIndicatorDefinition(Base):
    """Definición parametrizable de indicador — genérica por dominio/proceso."""

    __tablename__ = "diagnostic_indicator_defs"
    __table_args__ = (
        Index("ix_diag_ind_def_org_code", "organization_id", "code", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dominio: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subproceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    direccion_esperada: Mapped[str] = mapped_column(String(20), nullable=False, default="CUALQUIERA")
    periodicidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    umbral_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    umbral_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    fuente_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DiagnosticIndicatorValue(Base):
    """Valor consolidado de indicador a partir de señales."""

    __tablename__ = "diagnostic_indicator_values"
    __table_args__ = (
        Index("ix_diag_ind_val_org_metric", "organization_id", "dominio", "metrica"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    indicator_def_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostic_indicator_defs.id"), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=True)
    dominio: Mapped[str] = mapped_column(String(60), nullable=False)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metrica: Mapped[str] = mapped_column(String(120), nullable=False)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    periodo_referencia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DiagnosticFinding(Base):
    """Hallazgo estructurado — hecho u interpretación."""

    __tablename__ = "diagnostic_findings"
    __table_args__ = (
        Index("ix_diag_finding_org_codigo", "organization_id", "codigo"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo_contenido: Mapped[str] = mapped_column(String(20), nullable=False, default="HECHO")
    que_ocurre: Mapped[str] = mapped_column(String(500), nullable=False)
    donde: Mapped[str | None] = mapped_column(String(200), nullable=True)
    desde_cuando: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    magnitud: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    confianza: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.7)
    dominio: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicadores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    signal_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("signal_sources.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="DETECTADO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DiagnosticCorrelation(Base):
    """Correlación entre hallazgos/indicadores — no implica causalidad."""

    __tablename__ = "diagnostic_correlations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicator_value_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.6)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_causal: Mapped[bool] = mapped_column(Boolean, default=False)
    nota_causalidad: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="Correlación observada; no implica causalidad demostrada",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DiagnosticProbableCause(Base):
    """Causa confirmada, probable o hipótesis."""

    __tablename__ = "diagnostic_probable_causes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostic_findings.id"), nullable=True)
    diagnostic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostics.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="HIPOTESIS")
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.5)
    fuentes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Diagnostic(Base):
    """Diagnóstico transversal consolidado — versionable y auditable."""

    __tablename__ = "diagnostics"
    __table_args__ = (
        Index("ix_diag_org_codigo_ver", "organization_id", "codigo", "version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    periodo_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    periodo_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="GENERADO", index=True)
    dominios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    procesos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    prioridad_score: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    explicacion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    validated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DiagnosticItem(Base):
    """Ítem priorizado dentro de un diagnóstico."""

    __tablename__ = "diagnostic_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    diagnostic_id: Mapped[str] = mapped_column(String(36), ForeignKey("diagnostics.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostic_findings.id"), nullable=True)
    causa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostic_probable_causes.id"), nullable=True)
    prioridad_score: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    impacto_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    accion_recomendada_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DiagnosticOpportunityLink(Base):
    """Trazabilidad diagnóstico → hallazgo → señal → oportunidad."""

    __tablename__ = "diagnostic_opportunity_links"
    __table_args__ = (
        Index("ix_diag_opp_link_dedupe", "organization_id", "dedupe_key", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    diagnostic_id: Mapped[str] = mapped_column(String(36), ForeignKey("diagnostics.id"), nullable=False, index=True)
    finding_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("diagnostic_findings.id"), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("proactive_signals.id"), nullable=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
