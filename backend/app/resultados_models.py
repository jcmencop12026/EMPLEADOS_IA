"""Inteligencia de resultados EIAAX — indicadores, informes, plan de mejoramiento."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

TIPOS_MEDICION = frozenset({"ANTES", "PROYECTADO", "REAL"})
TIPOS_ANALITICA = frozenset({"DESCRIPTIVA", "DIAGNOSTICA", "COMPARATIVA", "PREDICTIVA", "PRESCRIPTIVA"})
TIPOS_INFORME = frozenset({"EJECUTIVO", "SEGUIMIENTO", "IMPACTO", "MEJORAMIENTO", "INSTITUCIONAL"})
VISIBILIDAD_INFORME = frozenset({"INTERNO", "VISIBLE_ENTIDAD"})
ESTADOS_PLAN = frozenset({"PENDIENTE", "EN_CURSO", "COMPLETADA", "CANCELADA"})


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResultadoIndicador(Base):
    """Indicador vinculable a evaluación, hallazgo, oportunidad o línea base."""

    __tablename__ = "resultados_indicadores"
    __table_args__ = (Index("ix_res_ind_org_exp", "organization_id", "expediente_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    definicion: Mapped[str | None] = mapped_column(Text, nullable=True)
    unidad: Mapped[str] = mapped_column(String(40), nullable=False, default="unidad")
    fuente: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")
    dimension_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    periodo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    valor_antes: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_proyectado: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_real: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    meta: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    fecha_medicion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidencia_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    calidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tipo_analitica: Mapped[str] = mapped_column(String(20), nullable=False, default="DESCRIPTIVA")
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True, index=True)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_hallazgos.id"), nullable=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    linea_base_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("lineas_base.id"), nullable=True)
    proceso: Mapped[str | None] = mapped_column(String(120), nullable=True)
    visible_entidad: Mapped[bool] = mapped_column(Boolean, default=False)
    notas_internas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ResultadoDimensionNodo(Base):
    """Nodo genérico de drill-down (sector-agnóstico)."""

    __tablename__ = "resultados_dimension_nodos"
    __table_args__ = (Index("ix_res_dim_ind_nivel", "indicador_id", "nivel"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    indicador_id: Mapped[str] = mapped_column(String(36), ForeignKey("resultados_indicadores.id"), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resultados_dimension_nodos.id"), nullable=True)
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ResultadoEvidencia(Base):
    """Evidencia vinculada a indicador o informe."""

    __tablename__ = "resultados_evidencias"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    indicador_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resultados_indicadores.id"), nullable=True)
    informe_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resultados_informes.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fuente: Mapped[str] = mapped_column(String(80), nullable=False, default="MANUAL")
    referencia: Mapped[str | None] = mapped_column(String(300), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ResultadoInformeImpacto(Base):
    """Informe de impacto versionable con narrativa determinística."""

    __tablename__ = "resultados_informes"
    __table_args__ = (Index("ix_res_inf_org_exp_ver", "organization_id", "expediente_id", "version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="IMPACTO")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    visibilidad: Mapped[str] = mapped_column(String(20), nullable=False, default="INTERNO")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    contenido_json: Mapped[str] = mapped_column(Text, nullable=False)
    narrativa: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ResultadoPlanAccion(Base):
    """Plan de mejoramiento: hallazgo → acción → seguimiento."""

    __tablename__ = "resultados_plan_acciones"
    __table_args__ = (Index("ix_res_plan_exp", "expediente_id", "estado"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    expediente_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=False, index=True)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_hallazgos.id"), nullable=True)
    indicador_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resultados_indicadores.id"), nullable=True)
    causa: Mapped[str | None] = mapped_column(Text, nullable=True)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    fecha_meta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    evidencia_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    seguimiento_notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
