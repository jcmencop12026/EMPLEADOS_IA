"""Modelos — Implementación y éxito del cliente (1340)."""

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


class ImplementacionProyecto(Base):
    """Proyecto de implementación post-venta."""

    __tablename__ = "impl_proyectos"
    __table_args__ = (UniqueConstraint("organization_id", "codigo", name="uq_impl_proyecto_org_codigo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PLANIFICACION", index=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_proposals.id"), nullable=True)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("commercial_plans.id"), nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alcance: Mapped[str | None] = mapped_column(Text, nullable=True)
    objetivos: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgos_resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    avance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    valor_compromiso_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    go_live_aprobado: Mapped[bool] = mapped_column(Boolean, default=False)
    go_live_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    go_live_aprobado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    go_live_checklist_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    go_live_observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ImplementacionFase(Base):
    __tablename__ = "impl_fases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    responsabilidad: Mapped[str] = mapped_column(String(20), nullable=False, default="NUESTRO_EQUIPO")
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criterio_entrada: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterio_salida: Mapped[str | None] = mapped_column(Text, nullable=True)
    dependencias_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionHito(Base):
    __tablename__ = "impl_hitos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    fase_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("impl_fases.id"), nullable=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(60), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    responsabilidad: Mapped[str] = mapped_column(String(20), nullable=False, default="NUESTRO_EQUIPO")
    proveedor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=True)
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    dependencias_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionTarea(Base):
    __tablename__ = "impl_tareas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    fase_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("impl_fases.id"), nullable=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    responsabilidad: Mapped[str] = mapped_column(String(20), nullable=False, default="NUESTRO_EQUIPO")
    proveedor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=True)
    prioridad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dependencias_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionRequisito(Base):
    __tablename__ = "impl_requisitos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    responsabilidad: Mapped[str] = mapped_column(String(20), nullable=False, default="CLIENTE")
    proveedor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tco_proveedores_aliados.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    fecha_requerida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_recibida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bloqueante: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionReadiness(Base):
    __tablename__ = "impl_readiness"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    dimensiones_json: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(String(30), nullable=False)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionBloqueador(Base):
    __tablename__ = "impl_bloqueadores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    impacto: Mapped[str] = mapped_column(String(20), nullable=False, default="ALTO")
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    accion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTO")
    critico: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    resuelto_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImplementacionRiesgo(Base):
    __tablename__ = "impl_riesgos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    probabilidad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    impacto: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    nivel: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIO")
    mitigacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTO")
    referencia_externa: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionPiloto(Base):
    __tablename__ = "impl_pilotos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    alcance: Mapped[str | None] = mapped_column(Text, nullable=True)
    usuarios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    procesos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    empleados_ia_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metricas_objetivo_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterios_exito: Mapped[str | None] = mapped_column(Text, nullable=True)
    criterios_suspension: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsables_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    resultado_explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprobado_produccion: Mapped[bool] = mapped_column(Boolean, default=False)
    aprobado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    aprobado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PLANIFICADO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionAdopcion(Base):
    __tablename__ = "impl_adopcion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    periodo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metricas_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionPlanAdopcion(Base):
    __tablename__ = "impl_plan_adopcion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    tipo_accion: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionCapacitacion(Base):
    __tablename__ = "impl_capacitaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    tema: Mapped[str] = mapped_column(String(200), nullable=False)
    grupo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    asistentes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClientePlan(Base):
    __tablename__ = "exito_planes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    valor_esperado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_compromiso_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    periodicidad_revision: Mapped[str] = mapped_column(String(20), nullable=False, default="MENSUAL")
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    proxima_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClienteObjetivo(Base):
    __tablename__ = "exito_objetivos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("exito_planes.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    indicador: Mapped[str | None] = mapped_column(String(120), nullable=True)
    valor_esperado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    valor_medido: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    estado_valor: Mapped[str] = mapped_column(String(30), nullable=False, default="NO_MEDIDO")
    opportunity_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("opportunities.id"), nullable=True)
    linea_base_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    valuation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClienteRevision(Base):
    __tablename__ = "exito_revisiones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("exito_planes.id"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    periodicidad: Mapped[str] = mapped_column(String(20), nullable=False)
    indicadores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    bloqueos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    acciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    decisiones: Mapped[str | None] = mapped_column(Text, nullable=True)
    revisado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClientePlanAccion(Base):
    __tablename__ = "exito_planes_accion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("exito_planes.id"), nullable=False, index=True)
    objetivo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("exito_objetivos.id"), nullable=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    causa: Mapped[str] = mapped_column(String(40), nullable=False)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    impacto_esperado: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClienteRenovacion(Base):
    __tablename__ = "exito_renovaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("exito_planes.id"), nullable=True)
    fecha_renovacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    valor_acumulado: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    adopcion_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    salud: Mapped[str | None] = mapped_column(String(20), nullable=True)
    riesgos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClienteExpansion(Base):
    __tablename__ = "exito_expansiones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    recomendacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PROPUESTA")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ExitoClienteSalud(Base):
    __tablename__ = "exito_salud"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    puntuacion: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    factores_json: Mapped[str] = mapped_column(Text, nullable=False)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionAlerta(Base):
    __tablename__ = "impl_alertas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    proyecto_id: Mapped[str] = mapped_column(String(36), ForeignKey("impl_proyectos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ImplementacionAuditoria(Base):
    __tablename__ = "impl_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
