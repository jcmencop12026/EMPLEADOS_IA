"""Esquemas Pydantic — Mesa de Ayuda y Soporte (MB-12)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SupportCaseCreate(BaseModel):
    tipo: str = Field(default="SOLICITUD", max_length=40)
    categoria: str | None = Field(default=None, max_length=80)
    asunto: str = Field(min_length=3, max_length=300)
    descripcion: str = Field(min_length=3)
    prioridad: str = Field(default="MEDIA", max_length=20)
    impacto: str = Field(default="MEDIO", max_length=20)
    urgencia: str = Field(default="MEDIA", max_length=20)
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    correlation_id: str | None = None
    evidencia_ref: str | None = Field(default=None, max_length=500)
    grupo: str | None = None


class SupportCaseAutoCreate(BaseModel):
    tipo: str
    asunto: str
    descripcion: str
    prioridad: str = "MEDIA"
    impacto: str = "MEDIO"
    urgencia: str = "MEDIA"
    origen_tipo: str
    origen_id: str
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    correlation_id: str | None = None
    solicitante_id: str | None = None


class SupportCaseAssign(BaseModel):
    responsable_id: str | None = None
    grupo: str | None = None


class SupportCaseStatusUpdate(BaseModel):
    estado: str
    nota: str | None = None


class SupportCaseResolve(BaseModel):
    resolucion: str = Field(min_length=3)
    cerrar: bool = False


class SupportCaseClose(BaseModel):
    nota: str | None = None


class SupportCommentCreate(BaseModel):
    cuerpo: str = Field(min_length=1)
    es_interno: bool = False
    evidencia_ref: str | None = Field(default=None, max_length=500)


class SupportSlaPolicyCreate(BaseModel):
    nombre: str
    prioridad: str = "MEDIA"
    minutos_primera_respuesta: int | None = None
    minutos_resolucion: int | None = None
    horario_servicio_json: dict[str, Any] | None = None


class SupportCaseOut(BaseModel):
    id: str
    organization_id: str
    numero: int
    referencia: str
    tipo: str
    categoria: str | None = None
    asunto: str
    descripcion: str
    prioridad: str
    impacto: str
    urgencia: str
    estado: str
    solicitante_id: str
    responsable_id: str | None = None
    grupo: str | None = None
    modulo_relacionado: str | None = None
    entidad_relacionada: str | None = None
    correlation_id: str | None = None
    origen: str
    origen_tipo: str | None = None
    resolucion: str | None = None
    sla_estado: str | None = None
    primera_respuesta_limite: datetime | None = None
    resolucion_limite: datetime | None = None
    fecha_limite: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resuelto_at: datetime | None = None
    cerrado_at: datetime | None = None


class SupportHistoryOut(BaseModel):
    id: str
    accion: str
    usuario_id: str | None = None
    detalle: dict[str, Any] | None = None
    correlation_id: str | None = None
    created_at: datetime | None = None


class SupportCommentOut(BaseModel):
    id: str
    usuario_id: str
    cuerpo: str
    es_interno: bool
    evidencia_ref: str | None = None
    created_at: datetime | None = None


class SupportCaseDetailOut(SupportCaseOut):
    historial: list[SupportHistoryOut] = Field(default_factory=list)
    comentarios: list[SupportCommentOut] = Field(default_factory=list)


class SupportContratoMiTrabajo(BaseModel):
    casos_asignados: int
    casos_vencidos: int
    casos_accion_requerida: int
    endpoint: str = "/api/soporte/contrato/mi-trabajo"


class SupportContratoCentroControl(BaseModel):
    casos_abiertos: int
    casos_criticos: int
    casos_vencidos: int
    tiempo_medio_respuesta_min: float | None = None
    tiempo_medio_resolucion_min: float | None = None
    principales_categorias: list[dict[str, Any]] = Field(default_factory=list)
    endpoint: str = "/api/soporte/contrato/centro-control"
