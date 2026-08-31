"""Esquemas Pydantic — Continuidad operativa (1360)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ServicioCreate(BaseModel):
    codigo: str | None = None
    nombre: str
    tipo: str = "OTRO"
    criticidad: str = "MEDIA"
    justificacion_criticidad: str | None = None
    rto_valor: float | None = None
    rto_unidad: str | None = "minutos"
    rpo_valor: float | None = None
    rpo_unidad: str | None = "minutos"
    proveedor_ref: str | None = None


class DependenciaCreate(BaseModel):
    servicio_origen_id: str
    servicio_destino_id: str
    tipo: str = "REQUIERE"
    critica: bool = False
    descripcion: str | None = None


class PlanCreate(BaseModel):
    nombre: str
    alcance: str | None = None
    servicios: list[str] = Field(default_factory=list)
    rto_valor: float | None = None
    rto_unidad: str | None = "horas"
    rpo_valor: float | None = None
    rpo_unidad: str | None = "horas"
    activadores: str | None = None


class BackupPoliticaCreate(BaseModel):
    recurso: str
    servicio_id: str | None = None
    frecuencia: str = "DIARIA"
    retencion_dias: int | None = 30
    ubicacion_logica: str | None = None
    tipo: str = "COMPLETO"
    cifrado_requerido: bool = True
    verificacion_requerida: bool = True


class BackupEjecucionCreate(BaseModel):
    politica_id: str
    inicio: datetime
    fin: datetime | None = None
    resultado: str = "EXITOSO"
    tamano_bytes: int | None = None
    hash_referencia: str | None = None
    ubicacion_logica: str | None = None
    error_seguro: str | None = None
    catalog_entry_id: str | None = None


class BackupVerificacionCreate(BaseModel):
    ejecucion_id: str
    existe: bool = True
    tamano_ok: bool = True
    integridad_ok: bool = True
    vigente: bool = True
    explicacion: str | None = None


class RestorePruebaCreate(BaseModel):
    ejecucion_id: str
    tipo: str = "SIMULADA"
    entorno_destino: str
    fecha: datetime
    duracion_minutos: float | None = None
    resultado: str = "EXITOSO"
    datos_validados: str | None = None
    evidencia: str | None = None
    catalog_entry_id: str | None = None


class IncidenteCreate(BaseModel):
    titulo: str
    servicio_id: str | None = None
    severidad: str = "SEV3"
    descripcion: str | None = None
    impacto: dict[str, Any] | None = None
    inicio: datetime | None = None


class IncidenteEstadoUpdate(BaseModel):
    estado: str
    causa: str | None = None
    causa_raiz_tipo: str | None = None


class ContingenciaActivar(BaseModel):
    plan_id: str
    incidente_id: str | None = None
    motivo: str
    acciones: list[str] = Field(default_factory=list)


class ModoDegradadoCreate(BaseModel):
    servicio_id: str
    funciones_continuan: list[str] = Field(default_factory=list)
    funciones_bloqueadas: list[str] = Field(default_factory=list)
    funciones_limitadas: list[str] = Field(default_factory=list)


class FallbackCreate(BaseModel):
    servicio_id: str
    proveedor_principal_ref: str | None = None
    proveedor_alternativo_ref: str | None = None
    descripcion: str | None = None


class SloCreate(BaseModel):
    servicio_id: str
    nombre: str
    objetivo_pct: float
    periodo: str | None = "MENSUAL"


class SloMedir(BaseModel):
    medido_pct: float


class DisponibilidadCreate(BaseModel):
    servicio_id: str
    periodo: str
    tiempo_disponible_min: float
    tiempo_caido_min: float


class EscalamientoCreate(BaseModel):
    severidad: str
    nivel: int = 1
    responsable_id: str | None = None
    tiempo_max_min: int | None = None
    siguiente_nivel: int | None = None


class RunbookCreate(BaseModel):
    nombre: str
    servicio_id: str | None = None
    descripcion: str | None = None
    pasos: list[dict[str, Any]]


class PruebaCreate(BaseModel):
    tipo: str
    escenario: str
    plan_id: str | None = None
    objetivo: str | None = None
    resultado: str | None = None
    rto_obtenido: float | None = None
    rpo_obtenido: float | None = None
    hallazgos: str | None = None


class PostIncidenteCreate(BaseModel):
    incidente_id: str
    que_ocurrio: str | None = None
    impacto: str | None = None
    causa: str | None = None
    causa_raiz_tipo: str = "NO_DETERMINADA"
    que_funciono: str | None = None
    que_fallo: str | None = None


class AccionCorrectivaCreate(BaseModel):
    accion: str
    incidente_id: str | None = None
    post_incidente_id: str | None = None
    responsable_id: str | None = None
    prioridad: str = "MEDIA"
    fecha_objetivo: datetime | None = None
