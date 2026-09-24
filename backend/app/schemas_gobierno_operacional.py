"""Esquemas Pydantic — gobierno operacional EIAAX."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AccionPolicyIn(BaseModel):
    tipo_accion: str
    recurso_tipo: str | None = None
    criticidad: str = "MEDIUM"
    requiere_aprobacion_humana: bool = False
    rol_aprobador: str | None = None
    capacidad_externa: str | None = None
    empleado_ia_id: str | None = None
    auto_ejecutar: bool = True
    config: dict[str, Any] | None = None


class AccionPolicyOut(BaseModel):
    id: str
    organization_id: str
    tipo_accion: str
    recurso_tipo: str | None
    criticidad: str
    requiere_aprobacion_humana: bool
    rol_aprobador: str | None
    capacidad_externa: str | None
    empleado_ia_id: str | None
    auto_ejecutar: bool
    activo: bool
    config: dict[str, Any] | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AccionSolicitudIn(BaseModel):
    tipo_accion: str
    recurso_tipo: str
    recurso_id: str | None = None
    criticidad: str = "MEDIUM"
    descripcion: str
    motivo_solicitud: str | None = None
    payload: dict[str, Any] | None = None
    actor_tipo: str = "HUMANO"
    correlation_id: str | None = None


class AccionSolicitudDecideIn(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|cancel)$")
    motivo: str | None = None


class AccionSolicitudOut(BaseModel):
    id: str
    organization_id: str
    correlation_id: str
    tipo_accion: str
    recurso_tipo: str
    recurso_id: str | None
    criticidad: str
    descripcion: str
    payload: dict[str, Any] | None = None
    estado: str
    actor_tipo: str
    solicitado_por: str
    aprobado_por: str | None
    rechazado_por: str | None
    motivo_solicitud: str | None
    motivo_decision: str | None
    resultado: dict[str, Any] | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None
    executed_at: datetime | None = None

    model_config = {"from_attributes": True}


class VisibilidadIn(BaseModel):
    dominio: str
    contexto_id: str | None = None
    objeto_tipo: str
    objeto_id: str
    visible: bool
    correlation_id: str | None = None


class VisibilidadLogOut(BaseModel):
    id: str
    dominio: str
    contexto_id: str | None
    objeto_tipo: str
    objeto_id: str
    visible: bool
    changed_by: str
    correlation_id: str | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class IaPolicyIn(BaseModel):
    nombre: str
    proveedores_permitidos: list[str] | None = None
    modelos_permitidos: list[str] | None = None
    acciones_permitidas: list[str] | None = None
    herramientas_permitidas: list[str] | None = None
    limites: dict[str, Any] | None = None
    requiere_aprobacion_humana: dict[str, bool] | None = None
    datos_permitidos: list[str] | None = None
    auto_ejecutar: bool = False


class IaPolicyOut(BaseModel):
    id: str
    organization_id: str
    nombre: str
    proveedores_permitidos: list[str] | None = None
    modelos_permitidos: list[str] | None = None
    acciones_permitidas: list[str] | None = None
    herramientas_permitidas: list[str] | None = None
    limites: dict[str, Any] | None = None
    requiere_aprobacion_humana: dict[str, bool] | None = None
    datos_permitidos: list[str] | None = None
    auto_ejecutar: bool
    activo: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class IaPolicyCheckIn(BaseModel):
    proveedor: str | None = None
    modelo: str | None = None
    tipo_accion: str | None = None
    herramienta: str | None = None


class IaPolicyCheckOut(BaseModel):
    permitido: bool
    requiere_aprobacion: bool
    auto_ejecutar: bool
    razones: list[str]


class ConfianzaControlOut(BaseModel):
    id: str
    nombre: str
    estado: str
    evidencia: str | None = None
    detalle: dict[str, Any] | None = None


class ConfianzaCentroOut(BaseModel):
    organization_id: str
    generado_en: str
    controles: list[ConfianzaControlOut]
    resumen: dict[str, Any]


class GobiernoEventoOut(BaseModel):
    id: str
    correlation_id: str | None
    actor_tipo: str
    actor_id: str | None
    accion: str
    recurso_tipo: str | None
    recurso_id: str | None
    decision: str | None
    aprobacion_id: str | None
    resultado: str | None
    detalle: dict[str, Any] | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class EvaluarAccionIn(BaseModel):
    tipo_accion: str
    recurso_tipo: str | None = None
    criticidad: str = "MEDIUM"
    capacidad_externa: str | None = None
    empleado_ia_id: str | None = None


class EvaluarAccionOut(BaseModel):
    tipo_accion: str
    requiere_aprobacion_humana: bool
    auto_ejecutar: bool
    politica_id: str | None = None
    motivo: str | None = None
