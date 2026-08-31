"""Esquemas Pydantic — capa transversal empresa seguridad y gobierno de datos."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClasificacionAsignarIn(BaseModel):
    objeto_tipo: str
    objeto_id: str
    codigo_clasificacion: str = Field(..., description="PUBLICA|INTERNA|CONFIDENCIAL|RESTRINGIDA o PUBLICO|INTERNO|...")
    motivo: str | None = None
    catalog_entry_id: str | None = None


class ClasificacionOut(BaseModel):
    id: str
    objeto_tipo: str
    objeto_id: str
    codigo: str | None
    nombre: str | None
    sensibilidad: int | None
    motivo: str | None = None
    catalog_entry_id: str | None = None
    asignado_por: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class VisibilidadNivelIn(BaseModel):
    dominio: str
    contexto_id: str | None = None
    objeto_tipo: str
    objeto_id: str
    nivel_visibilidad: str
    motivo: str | None = None
    correlation_id: str | None = None


class EvidenciaVinculoIn(BaseModel):
    tipo_evidencia: str
    referencia: str
    objeto_tipo: str
    objeto_id: str
    rol_vinculo: str = "SOPORTE"
    descripcion: str | None = None
    correlation_id: str | None = None


class EvidenciaVinculoOut(BaseModel):
    id: str
    tipo_evidencia: str
    referencia: str
    descripcion: str | None
    objeto_tipo: str
    objeto_id: str
    rol_vinculo: str
    correlation_id: str | None
    creado_por: str | None
    created_at: datetime | None = None


class AuditoriaConsultaOut(BaseModel):
    fuente: str
    id: str
    accion: str
    accion_etiqueta: str
    usuario_id: str | None
    usuario: str | None
    organizacion_id: str | None
    detalle: str | None
    correlation_id: str | None
    resultado: str | None
    fecha: str | None


class TrazabilidadOut(BaseModel):
    organization_id: str
    correlation_id: str
    cadena: list[dict[str, Any]]
    total_etapas: int


class ControlConfianzaOut(BaseModel):
    id: str
    nombre: str
    grupo: str
    grupo_etiqueta: str
    estado: str
    estado_etiqueta: str
    evidencia: str | None = None
    detalle: dict[str, Any] | None = None


class CentroConfianzaEmpresarialOut(BaseModel):
    organization_id: str
    generado_en: str
    controles: list[ControlConfianzaOut]
    grupos: list[dict[str, Any]]
    resumen: dict[str, Any]


class GobiernoObjetoOut(BaseModel):
    objeto_tipo: str
    objeto_id: str
    clasificacion: dict[str, Any] | None
    catalogo: dict[str, Any] | None
    evidencias: list[dict[str, Any]]
    visibilidad: list[dict[str, Any]]
