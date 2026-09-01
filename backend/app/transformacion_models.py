"""Arquitecto de Transformación Empresarial — dossier persistente y motor de decisión."""

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


DOSSIER_ETAPAS = frozenset({
    "PROSPECTO", "EVALUACION", "DIAGNOSTICO", "OPORTUNIDADES",
    "PROPUESTA", "CLIENTE", "IMPLEMENTACION", "OPERACION", "MEDICION",
})

MAPA_TIPOS = frozenset({
    "AREA", "PROCESO", "SUBPROCESO", "ACTIVIDAD", "ROL", "SISTEMA",
    "FUENTE_INFO", "INDICADOR", "PROBLEMA", "DEPENDENCIA",
})

CAUSA_TIPOS = frozenset({"SINTOMA", "PROBLEMA", "CAUSA_PROBABLE", "CAUSA_VALIDADA"})

ALTERNATIVA_TIPOS = frozenset({
    "ELIMINAR", "SIMPLIFICAR", "ESTANDARIZAR", "REORGANIZAR", "DIGITALIZAR",
    "INTEGRAR", "AUTOMATIZAR", "APLICAR_IA", "EMPLEADO_IA", "CAPACIDAD_EXTERNA",
    "REDISENAR_CONTROL", "MEDIR", "MANTENER_HUMANO",
})

INICIATIVA_CLASES = frozenset({"RAPIDA", "TACTICA", "ESTRATEGICA"})
ESCENARIO_TIPOS = frozenset({"ACTUAL", "MEJORADO", "TRANSFORMADO"})
CALIDAD_NIVELES = frozenset({"ALTA", "MEDIA", "BAJA"})
FUENTE_TIPOS = frozenset({
    "captura_guiada", "carga_manual", "documento", "archivo", "base_datos",
    "api", "expediente", "diagnostico", "conocimiento", "externa_pendiente",
})


class DossierEmpresarial(Base):
    """Dossier empresarial persistente — acompaña a la organización en el ciclo de vida."""

    __tablename__ = "dossier_empresarial"
    __table_args__ = (UniqueConstraint("organization_id", name="uq_dossier_org"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    etapa_actual: Mapped[str] = mapped_column(String(30), nullable=False, default="PROSPECTO")
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza_global: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    porcentaje_completitud: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expediente_activo_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True,
    )
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DossierConocimientoItem(Base):
    """Conocimiento reutilizable — evita volver a preguntar información válida."""

    __tablename__ = "dossier_conocimiento_items"
    __table_args__ = (
        Index("ix_dossier_conoc_dossier_campo", "dossier_id", "campo"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    campo: Mapped[str] = mapped_column(String(80), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[str | None] = mapped_column(Text, nullable=True)
    fuente: Mapped[str] = mapped_column(String(40), nullable=False, default="captura_guiada")
    calidad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True)
    explicacion_calidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DossierMapaNodo(Base):
    """Mapa empresarial progresivo — incompleto por diseño."""

    __tablename__ = "dossier_mapa_nodos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("dossier_mapa_nodos.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DossierCausa(Base):
    """Cadena síntoma → problema → causa con evidencia."""

    __tablename__ = "dossier_causas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_hallazgos.id"), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("dossier_causas.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    explicacion_confianza: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TransformacionAlternativa(Base):
    """Alternativa de transformación evaluada por el motor de decisión."""

    __tablename__ = "transformacion_alternativas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    expediente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("evaluaciones_expediente.id"), nullable=True)
    causa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("dossier_causas.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    costo: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    esfuerzo: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    riesgo: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    tiempo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    complejidad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    reversibilidad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    madurez: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recomendada: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TransformacionIniciativa(Base):
    """Iniciativa priorizada en la cartera de transformación."""

    __tablename__ = "transformacion_iniciativas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    alternativa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transformacion_alternativas.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    clasificacion: Mapped[str] = mapped_column(String(20), nullable=False, default="TACTICA")
    prioridad_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    impacto_vs_esfuerzo_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PROPUESTA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TransformacionEscenario(Base):
    """Escenario comparativo — proyecciones claramente marcadas."""

    __tablename__ = "transformacion_escenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    proyeccion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_proyectado: Mapped[bool] = mapped_column(Boolean, default=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmpleadoIARequerimiento(Base):
    """Requerimiento estructurado para la Fábrica de Empleados IA (consumo futuro)."""

    __tablename__ = "empleado_ia_requerimientos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    iniciativa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transformacion_iniciativas.id"), nullable=True)
    alternativa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transformacion_alternativas.id"), nullable=True)
    objetivo: Mapped[str] = mapped_column(Text, nullable=False)
    responsabilidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    entradas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    salidas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    herramientas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    frecuencia: Mapped[str | None] = mapped_column(String(40), nullable=True)
    riesgo: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    supervision: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicadores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CapacidadExternaNecesidad(Base):
    """Necesidad empresarial para integración/automatización — contrato preparado para GENERAL."""

    __tablename__ = "capacidad_externa_necesidades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    dossier_id: Mapped[str] = mapped_column(String(36), ForeignKey("dossier_empresarial.id"), nullable=False, index=True)
    alternativa_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("transformacion_alternativas.id"), nullable=True)
    necesidad_empresarial: Mapped[str] = mapped_column(Text, nullable=False)
    contrato_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
