"""Esquemas — Bandeja unificada de trabajo humano."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EstadoPresentacion = Literal[
    "PENDIENTE",
    "EN_CURSO",
    "REQUIERE_APROBACION",
    "VENCIDA",
    "COMPLETADA",
    "FALLIDA",
]

SemanticKind = Literal["HECHO", "INFERENCIA", "RECOMENDACION"]


class TrabajoAccion(BaseModel):
    codigo: str
    etiqueta: str
    permiso: str | None = None
    href: str | None = None
    payload: dict[str, Any] | None = None


class TrabajoItem(BaseModel):
    id: str
    source_id: str
    tipo: str
    asunto: str
    modulo: str
    organization_id: str
    organization_name: str | None = None
    prioridad: str
    prioridad_orden: int = Field(ge=1, le=4)
    estado_dominio: str
    estado_presentacion: EstadoPresentacion
    responsable_id: str | None = None
    responsable_nombre: str | None = None
    created_at: datetime | None = None
    fecha_limite: datetime | None = None
    antiguedad_horas: float | None = None
    vencida: bool = False
    correlation_id: str | None = None
    requires_action: bool = False
    informativa: bool = False
    semantic_kind: SemanticKind | None = None
    detalle: str | None = None
    enlace: str
    trazabilidad_enlace: str | None = None
    acciones: list[TrabajoAccion] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrabajoResumen(BaseModel):
    organization_id: str
    pendientes: int
    vencidas: int
    requieren_aprobacion: int
    total_visible: int


class TrabajoItemsResponse(BaseModel):
    items: list[TrabajoItem]
    total: int
    filtros_aplicados: dict[str, Any] = Field(default_factory=dict)
