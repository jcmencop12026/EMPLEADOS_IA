"""Modelos — Continuidad operativa y resiliencia (1360)."""

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


class ContinuidadServicioCritico(Base):
    __tablename__ = "cont_servicios_criticos"
    __table_args__ = (UniqueConstraint("organization_id", "codigo", name="uq_cont_servicio_org_codigo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, default="OTRO")
    criticidad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    justificacion_criticidad: Mapped[str | None] = mapped_column(Text, nullable=True)
    rto_valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rto_unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rpo_valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rpo_unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    proveedor_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estado_operacional: Mapped[str] = mapped_column(String(20), nullable=False, default="DESCONOCIDO")
    ultima_comprobacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadDependencia(Base):
    __tablename__ = "cont_dependencias"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_origen_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    servicio_destino_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="REQUIERE")
    critica: Mapped[bool] = mapped_column(Boolean, default=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadPlan(Base):
    __tablename__ = "cont_planes"
    __table_args__ = (UniqueConstraint("organization_id", "codigo", name="uq_cont_plan_org_codigo"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    alcance: Mapped[str | None] = mapped_column(Text, nullable=True)
    servicios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsables_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    riesgos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    activadores: Mapped[str | None] = mapped_column(Text, nullable=True)
    rto_valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rto_unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rpo_valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rpo_unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="BORRADOR")
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ContinuidadBackupPolitica(Base):
    __tablename__ = "cont_backup_politicas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=True)
    recurso: Mapped[str] = mapped_column(String(200), nullable=False)
    frecuencia: Mapped[str] = mapped_column(String(30), nullable=False, default="DIARIA")
    retencion_dias: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ubicacion_logica: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETO")
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    cifrado_requerido: Mapped[bool] = mapped_column(Boolean, default=True)
    verificacion_requerida: Mapped[bool] = mapped_column(Boolean, default=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PROGRAMADO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadBackupEjecucion(Base):
    __tablename__ = "cont_backup_ejecuciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    politica_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_backup_politicas.id"), nullable=False, index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recurso: Mapped[str] = mapped_column(String(200), nullable=False)
    estado_registro: Mapped[str] = mapped_column(String(20), nullable=False, default="EJECUTADO")
    resultado: Mapped[str] = mapped_column(String(20), nullable=False, default="EXITOSO")
    tamano_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hash_referencia: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ubicacion_logica: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_seguro: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadBackupVerificacion(Base):
    __tablename__ = "cont_backup_verificaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ejecucion_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_backup_ejecuciones.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    existe: Mapped[bool] = mapped_column(Boolean, default=False)
    tamano_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    integridad_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    vigente: Mapped[bool] = mapped_column(Boolean, default=False)
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    verificado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadRestorePrueba(Base):
    __tablename__ = "cont_restore_pruebas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ejecucion_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_backup_ejecuciones.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="SIMULADA")
    entorno_destino: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracion_minutos: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False, default="EXITOSO")
    datos_validados: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidencia: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadIncidente(Base):
    __tablename__ = "cont_incidentes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=True)
    severidad: Mapped[str] = mapped_column(String(10), nullable=False, default="SEV3")
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="DETECTADO", index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deteccion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recuperacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    causa: Mapped[str | None] = mapped_column(Text, nullable=True)
    causa_raiz_tipo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_planes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadContingenciaActivacion(Base):
    __tablename__ = "cont_contingencia_activaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_planes.id"), nullable=False)
    incidente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_incidentes.id"), nullable=True)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    acciones_activadas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    autorizado_por: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadModoDegradado(Base):
    __tablename__ = "cont_modo_degradado"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    funciones_continuan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    funciones_bloqueadas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    funciones_limitadas_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadFallback(Base):
    __tablename__ = "cont_fallbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    proveedor_principal_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    proveedor_alternativo_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadSlo(Base):
    __tablename__ = "cont_slos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    objetivo_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    medido_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    periodo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    incumplido: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadDisponibilidad(Base):
    __tablename__ = "cont_disponibilidad"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    tiempo_disponible_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    tiempo_caido_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    disponibilidad_pct: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadEscalamiento(Base):
    __tablename__ = "cont_escalamientos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    severidad: Mapped[str] = mapped_column(String(10), nullable=False)
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    tiempo_max_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    siguiente_nivel: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadRunbook(Base):
    __tablename__ = "cont_runbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    servicio_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_servicios_criticos.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    pasos_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadPrueba(Base):
    __tablename__ = "cont_pruebas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_planes.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    escenario: Mapped[str] = mapped_column(String(100), nullable=False)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    rto_obtenido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rpo_obtenido: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    hallazgos: Mapped[str | None] = mapped_column(Text, nullable=True)
    acciones_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadPostIncidente(Base):
    __tablename__ = "cont_post_incidentes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    incidente_id: Mapped[str] = mapped_column(String(36), ForeignKey("cont_incidentes.id"), nullable=False)
    que_ocurrio: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto: Mapped[str | None] = mapped_column(Text, nullable=True)
    causa: Mapped[str | None] = mapped_column(Text, nullable=True)
    causa_raiz_tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="NO_DETERMINADA")
    que_funciono: Mapped[str | None] = mapped_column(Text, nullable=True)
    que_fallo: Mapped[str | None] = mapped_column(Text, nullable=True)
    aprendizaje_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadAccionCorrectiva(Base):
    __tablename__ = "cont_acciones_correctivas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    post_incidente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_post_incidentes.id"), nullable=True)
    incidente_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cont_incidentes.id"), nullable=True)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    prioridad: Mapped[str] = mapped_column(String(10), nullable=False, default="MEDIA")
    fecha_objetivo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    resultado: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadAlerta(Base):
    __tablename__ = "cont_alertas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    entidad_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resuelta: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ContinuidadAuditoria(Base):
    __tablename__ = "cont_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    accion: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detalle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
