"""Esquemas Pydantic — TCO y ecosistema de aliados (1320)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CategoriaCostoCreate(BaseModel):
    code: str
    nombre: str
    descripcion: str | None = None
    es_global: bool = False


class ProveedorAliadoCreate(BaseModel):
    codigo: str | None = None
    nombre: str
    tipo: str
    contacto: str | None = None
    descripcion: str | None = None
    riesgo_nivel: str = "MEDIO"
    riesgo_criterio: str | None = None
    riesgo_justificacion: str | None = None


class RiesgoProveedorUpdate(BaseModel):
    riesgo_nivel: str
    riesgo_criterio: str | None = None
    riesgo_justificacion: str | None = None


class ContratoCondicionCreate(BaseModel):
    proveedor_id: str
    moneda: str = "COP"
    tipo_tarifa: str | None = None
    minimo: float | None = None
    maximo: float | None = None
    compromiso: str | None = None
    descuento_pct: float | None = None
    condiciones: str | None = None
    sla: str | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None


class TarifaTramoCreate(BaseModel):
    desde_unidades: float = 0
    hasta_unidades: float | None = None
    precio_unidad: float
    orden: int = 0


class TarifaCreate(BaseModel):
    proveedor_id: str
    nombre: str
    unidad: str = "unidad"
    moneda: str = "COP"
    tipo: str = "UNIDAD"
    monto_base: float | None = None
    periodicidad: str | None = None
    vigente_desde: datetime | None = None
    vigente_hasta: datetime | None = None
    tramos: list[TarifaTramoCreate] = Field(default_factory=list)


class CostoCreate(BaseModel):
    categoria_id: str | None = None
    categoria_code: str | None = None
    proveedor_id: str | None = None
    nombre: str
    tipo_costo: str = "FIJO"
    naturaleza: str = "ESTIMADO"
    periodicidad: str = "MENSUAL"
    unidad: str | None = None
    cantidad: float | None = None
    monto: float
    moneda: str = "COP"
    tasa_conversion: float | None = None
    tasa_fecha: datetime | None = None
    moneda_destino: str | None = None
    proposal_id: str | None = None
    finops_record_id: str | None = None
    employee_id: str | None = None
    integracion_ref: str | None = None
    periodo_ref: str | None = None
    notas: str | None = None


class CostoUpdate(BaseModel):
    nombre: str | None = None
    monto: float | None = None
    naturaleza: str | None = None
    cantidad: float | None = None
    notas: str | None = None
    motivo: str | None = None


class DistribucionCreate(BaseModel):
    costo_id: str
    metodo: str
    criterio: dict[str, Any] | None = None
    asignaciones: list[dict[str, Any]]


class TcoCalcularRequest(BaseModel):
    periodo: str | None = None
    escenario: str | None = None
    tipo: str = "ESTIMADO"
    moneda_destino: str = "COP"
    tasa_conversion: float | None = None
    proposal_id: str | None = None
    incluir_finops: bool = True
    margen_minimo_pct: float | None = None
    ingreso: float | None = None
    guardar_snapshot: bool = False


class SimulacionRequest(BaseModel):
    tipo: str
    parametros: dict[str, Any] = Field(default_factory=dict)


class CompararProveedoresRequest(BaseModel):
    proveedor_ids: list[str]
    unidades: float = 1_000_000


class MakeOrBuyRequest(BaseModel):
    costo_interno: float
    costo_tercero: float
    tiempo_interno_meses: float = 6
    tiempo_tercero_meses: float = 3
    riesgo_interno: str = "MEDIO"
    riesgo_tercero: str = "BAJO"
    mantenimiento_interno_anual: float = 0
    mantenimiento_tercero_anual: float = 0


class SustitucionProveedorRequest(BaseModel):
    proveedor_actual_id: str
    proveedor_alternativo_id: str
    unidades_mensuales: float = 1_000_000
    sla_actual: str | None = None
    sla_alternativo: str | None = None


class AlianzaCreate(BaseModel):
    nombre: str
    tipo: str
    proveedor_id: str | None = None
    opportunity_id: str | None = None
    objetivo: str | None = None
    alcance: str | None = None
    vigencia_desde: datetime | None = None
    vigencia_hasta: datetime | None = None
    beneficios_esperados: str | None = None
    costos_esperados: float | None = None
    responsabilidades: str | None = None


class AlianzaEstadoUpdate(BaseModel):
    estado: str
    justificacion: str | None = None


class RentabilidadRequest(BaseModel):
    periodo: str | None = None
    ingreso_estimado: float | None = None
    ingreso_real: float | None = None
