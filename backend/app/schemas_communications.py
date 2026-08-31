"""Esquemas — Centro de Información y Comunicaciones (MB-11)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CommChannelOut(BaseModel):
    id: str
    organization_id: str
    tipo: str
    nombre: str
    activo: bool
    config: dict[str, Any] | None = None
    secret_configured: bool = False
    estado: str
    prioridad: int
    uso_permitido: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CommChannelCreate(BaseModel):
    tipo: str
    nombre: str
    activo: bool = True
    config: dict[str, Any] | None = None
    secret_ref: str | None = None
    prioridad: int = 100
    uso_permitido: str | None = None


class CommTemplateOut(BaseModel):
    id: str
    organization_id: str
    codigo: str
    nombre: str
    tipo_comunicacion: str
    canal_tipo: str
    idioma: str
    current_version_id: str | None = None
    current_version: int | None = None


class CommTemplateVersionOut(BaseModel):
    id: str
    template_id: str
    version: int
    asunto: str | None = None
    contenido: str
    variables: list[str] = Field(default_factory=list)
    estado: str
    created_at: datetime | None = None


class CommTemplateCreate(BaseModel):
    codigo: str
    nombre: str
    tipo_comunicacion: str
    canal_tipo: str
    idioma: str = "es"
    asunto: str | None = None
    contenido: str
    variables: list[str] = Field(default_factory=list)


class CommTemplateVersionCreate(BaseModel):
    asunto: str | None = None
    contenido: str
    variables: list[str] = Field(default_factory=list)


class CommRuleOut(BaseModel):
    id: str
    organization_id: str
    nombre: str
    event_type: str
    condicion: dict[str, Any] | None = None
    destinatario_tipo: str
    destinatario_regla: str
    template_version_id: str
    channel_id: str
    accion: str
    activo: bool
    antispam_minutos: int
    obligatoria: bool = False


class CommRuleCreate(BaseModel):
    nombre: str
    event_type: str
    condicion: dict[str, Any] | None = None
    destinatario_tipo: str
    destinatario_regla: str
    template_version_id: str
    channel_id: str
    accion: str = "ENVIAR"
    activo: bool = True
    antispam_minutos: int = 15
    obligatoria: bool = False


class CommMessageOut(BaseModel):
    id: str
    organization_id: str
    estado: str
    tipo_comunicacion: str
    channel_id: str | None = None
    channel_tipo: str | None = None
    template_version_id: str | None = None
    template_version: int | None = None
    rule_id: str | None = None
    destinatario_tipo: str
    destinatario_id: str | None = None
    destinatario_externo: str | None = None
    asunto: str | None = None
    contenido: str
    idioma: str
    programada_para: datetime | None = None
    correlation_id: str | None = None
    event_id: str | None = None
    origen: str
    origen_id: str | None = None
    intentos: int
    max_intentos: int
    proximo_intento: datetime | None = None
    created_at: datetime | None = None
    enviada_at: datetime | None = None
    entregada_at: datetime | None = None
    cancelada_at: datetime | None = None


class CommMessageDetailOut(CommMessageOut):
    historial_intentos: list[dict[str, Any]] = Field(default_factory=list)


class CommMessageCreate(BaseModel):
    tipo_comunicacion: str = "MANUAL"
    channel_id: str
    template_version_id: str | None = None
    destinatario_tipo: str
    destinatario_id: str | None = None
    destinatario_externo: str | None = None
    asunto: str | None = None
    contenido: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    idioma: str = "es"
    programada_para: datetime | None = None
    enviar_ahora: bool = True
    correlation_id: str | None = None


class CommPreferenceOut(BaseModel):
    id: str | None = None
    organization_id: str
    user_id: str | None = None
    canales: list[str] = Field(default_factory=list)
    tipos: list[str] = Field(default_factory=list)
    horario: dict[str, Any] | None = None
    idioma: str = "es"


class CommPreferenceUpdate(BaseModel):
    canales: list[str] | None = None
    tipos: list[str] | None = None
    horario: dict[str, Any] | None = None
    idioma: str | None = None


class CommResumenCentroControl(BaseModel):
    pendientes: int
    fallidas: int
    enviadas: int
    tasa_fallo_pct: float | None = None
    canales_degradados: int
    reintentos_pendientes: int
    criticas_pendientes: int
    endpoint: str = "/api/comunicaciones/contrato/centro-control"


class CommContratoMiTrabajo(BaseModel):
    configuracion_faltante: int
    canales_bloqueados: int
    reintentos_agotados: int
    endpoint: str = "/api/comunicaciones/contrato/mi-trabajo"


class CommEntregaInformeCreate(BaseModel):
    channel_id: str
    destinatario_tipo: str = "USUARIO"
    destinatario_id: str | None = None
    destinatario_externo: str | None = None
    visibilidad_entrega: str = "VISIBLE_ENTIDAD"


class CommEntregaInformeOut(BaseModel):
    id: str
    informe_id: str
    informe_version: int
    message_id: str
    expediente_id: str | None = None
    destinatario_tipo: str
    destinatario_id: str | None = None
    visibilidad_entrega: str
    correlation_id: str | None = None
    created_at: str | None = None


class CommCentroInformacionResumen(CommResumenCentroControl):
    informes_entregados: int = 0
    comunicaciones_fallidas: int = 0
    programadas: int = 0
    informes_comunicacion: int = 0


class CommSolicitudInfoFaltante(BaseModel):
    expediente_id: str
    destinatario_id: str
