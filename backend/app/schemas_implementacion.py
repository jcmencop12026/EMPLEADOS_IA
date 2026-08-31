"""Esquemas Pydantic — Implementación y éxito del cliente (1340)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProyectoCreate(BaseModel):
    titulo: str
    proposal_id: str | None = None
    plan_id: str | None = None
    responsable_id: str | None = None
    fecha_inicio: datetime | None = None
    fecha_objetivo: datetime | None = None
    alcance: str | None = None
    objetivos: str | None = None


class ProyectoUpdate(BaseModel):
    estado: str | None = None
    avance_pct: float | None = None
    alcance: str | None = None
    objetivos: str | None = None


class FaseCreate(BaseModel):
    nombre: str
    orden: int = 0
    responsable_id: str | None = None
    responsabilidad: str = "NUESTRO_EQUIPO"
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    criterio_entrada: str | None = None
    criterio_salida: str | None = None
    dependencias: list[str] = Field(default_factory=list)


class HitoCreate(BaseModel):
    codigo: str | None = None
    nombre: str
    fase_id: str | None = None
    responsable_id: str | None = None
    responsabilidad: str = "NUESTRO_EQUIPO"
    proveedor_id: str | None = None
    fecha_objetivo: datetime | None = None
    dependencias: list[str] = Field(default_factory=list)


class HitoCompletar(BaseModel):
    evidencia: str | None = None
    fecha_real: datetime | None = None


class TareaCreate(BaseModel):
    titulo: str
    fase_id: str | None = None
    descripcion: str | None = None
    responsable_id: str | None = None
    responsabilidad: str = "NUESTRO_EQUIPO"
    proveedor_id: str | None = None
    prioridad: str = "MEDIA"
    fecha_objetivo: datetime | None = None
    dependencias: list[str] = Field(default_factory=list)


class RequisitoCreate(BaseModel):
    tipo: str
    descripcion: str
    responsable_id: str | None = None
    responsabilidad: str = "CLIENTE"
    proveedor_id: str | None = None
    fecha_requerida: datetime | None = None
    bloqueante: bool = False


class ReadinessCreate(BaseModel):
    dimensiones: dict[str, Any]


class BloqueadorCreate(BaseModel):
    tipo: str
    descripcion: str
    impacto: str = "ALTO"
    responsable_id: str | None = None
    accion: str | None = None
    critico: bool = False


class RiesgoCreate(BaseModel):
    descripcion: str
    probabilidad: str = "MEDIA"
    impacto: str = "MEDIO"
    mitigacion: str | None = None
    responsable_id: str | None = None
    referencia_externa: str | None = None


class PilotoCreate(BaseModel):
    alcance: str | None = None
    usuarios: list[str] = Field(default_factory=list)
    procesos: list[str] = Field(default_factory=list)
    empleados_ia: list[str] = Field(default_factory=list)
    duracion_dias: int | None = None
    metricas_objetivo: list[dict[str, Any]] = Field(default_factory=list)
    criterios_exito: str | None = None
    criterios_suspension: str | None = None


class PilotoResultado(BaseModel):
    resultado: str
    explicacion: str | None = None
    evidencia: str | None = None


class PilotoAprobarProduccion(BaseModel):
    observaciones: str | None = None


class GoLiveAprobacion(BaseModel):
    checklist: dict[str, bool]
    observaciones: str | None = None


class AdopcionCreate(BaseModel):
    periodo: str | None = None
    metricas: dict[str, Any]


class PlanAdopcionCreate(BaseModel):
    tipo_accion: str
    descripcion: str
    responsable_id: str | None = None
    fecha_objetivo: datetime | None = None


class CapacitacionCreate(BaseModel):
    tema: str
    grupo: str | None = None
    fecha: datetime | None = None
    asistentes: int | None = None
    resultado: str | None = None
    evidencia: str | None = None


class ExitoPlanCreate(BaseModel):
    proyecto_id: str
    titulo: str
    valor_esperado: float | None = None
    periodicidad_revision: str = "MENSUAL"
    responsable_id: str | None = None


class ExitoObjetivoCreate(BaseModel):
    nombre: str
    indicador: str | None = None
    valor_esperado: float | None = None
    opportunity_id: str | None = None


class ExitoObjetivoMedir(BaseModel):
    valor_medido: float


class ExitoPlanAccionCreate(BaseModel):
    causa: str
    accion: str
    objetivo_id: str | None = None
    responsable_id: str | None = None
    fecha_objetivo: datetime | None = None
    impacto_esperado: str | None = None


class ExitoRevisionCreate(BaseModel):
    fecha: datetime
    periodicidad: str = "MENSUAL"
    indicadores: dict[str, Any] | None = None
    valor: dict[str, Any] | None = None
    riesgos: list[str] | None = None
    bloqueos: list[str] | None = None
    acciones: list[str] | None = None
    decisiones: str | None = None


class RenovacionCreate(BaseModel):
    proyecto_id: str
    plan_id: str | None = None
    fecha_renovacion: datetime | None = None


class ExpansionCreate(BaseModel):
    proyecto_id: str
    tipo: str
    descripcion: str
    recomendacion: str | None = None


class EntregableCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    responsable_id: str | None = None
    fecha_objetivo: datetime | None = None
    documento_id: str | None = None
    version_referencia: str | None = None


class EntregableUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    estado: str | None = None
    evidencia: str | None = None
    aceptacion: str | None = None
    observaciones: str | None = None


class TareaCompletar(BaseModel):
    evidencia: str | None = None
    resultado: str | None = None


class BloqueadorResolver(BaseModel):
    observaciones: str | None = None
