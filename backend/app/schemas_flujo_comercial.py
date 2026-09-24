"""Esquemas — Flujo comercial V1 EIAAX (1730)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DemoIniciar(BaseModel):
    sector: str = "salud"
    area: str = "facturacion"


class SeleccionOportunidades(BaseModel):
    opportunity_ids: list[str]
    presentar: bool = True


class PresentacionEjecutivaCreate(BaseModel):
    titulo: str | None = None
    hallazgos_ids: list[str] | None = None
    oportunidades_ids: list[str] | None = None
    solucion: str | None = None
    alcance: str | None = None
    tiempo: str | None = None
    inversion: str | None = None
    dependencias: list[str] | None = None
    supuestos: list[str] | None = None
    siguiente_paso: str | None = None


class PropuestaDesdeDossier(BaseModel):
    opportunity_id: str | None = None
    titulo: str | None = None
    presentacion_id: str | None = None
    exigir_suficiencia: bool = True


class InstrumentoCreate(BaseModel):
    tipo: str
    nombre: str | None = None
    contenido_resumen: str | None = None
    estado: str | None = None
    metadata: dict[str, Any] | None = None


class CompromisoGarantiaCreate(BaseModel):
    tipo_compromiso: str = "CONTROL_NUESTRO"
    descripcion: str
    baseline: str | None = None
    objetivo: str | None = None
    dependencias: list[str] | None = None
    evidencia: str | None = None
    atribucion: str | None = None


class OportunidadClasificacionUpdate(BaseModel):
    origen_comercial: str | None = None
    presentar_cliente: bool | None = None
    clasificacion_valor: str | None = Field(None, description="VERIFICADO|ESTIMADO|POTENCIAL")
