"""Esquemas API — Segmentación y planes verticales (1310)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SectorCreate(BaseModel):
    code: str
    name: str
    descripcion: str | None = None
    lifecycle_status: str = "ACTIVO"
    organization_id: str | None = None


class SegmentCreate(BaseModel):
    code: str
    name: str
    descripcion: str | None = None
    sector_id: str | None = None
    dimensions: dict[str, Any] | None = None
    lifecycle_status: str = "ACTIVO"
    organization_id: str | None = None


class ProfileUpsert(BaseModel):
    segment_id: str | None = None
    sector_id: str | None = None
    subsector: str | None = None
    tamano: str | None = None
    madurez_digital: str | None = None
    complejidad_operativa: str | None = None
    num_usuarios: int | None = None
    num_empleados_ia: int | None = None
    volumen_operaciones: int | None = None
    num_integraciones: int | None = None
    consumo_ia_estimado: int | None = None
    nivel_soporte: str | None = None
    sla_requerido: str | None = None
    riesgo: str | None = None
    potencial_valor: float | None = None
    presupuesto_estimado: float | None = None
    observaciones: str | None = None


class PackageCreate(BaseModel):
    code: str
    name: str
    descripcion: str | None = None
    plan_id: str | None = None
    segment_id: str | None = None
    sector_id: str | None = None
    base_package_id: str | None = None
    lifecycle_status: str = "BORRADOR"
    is_custom: bool = False
    empleados_ia_incluidos: int | None = None
    usuarios_incluidos: int | None = None
    automatizaciones_incluidas: int | None = None
    consumo_ia_incluido_tokens: int | None = None
    presupuesto_ia_incluido: float | None = None
    integraciones_incluidas: int | None = None
    almacenamiento_gb: int | None = None
    sla_nivel: str | None = None
    soporte_nivel: str | None = None
    excedente_ia_por_millon: float | None = None
    alerta_consumo_pct: float | None = None
    bloqueo_excedente: bool = False
    credential_modes: list[str] | None = None
    capabilities: dict[str, Any] | None = None
    servicios_incluidos: list[str] | None = None
    servicios_opcionales: list[str] | None = None
    precio_estimado: float | None = None
    organization_id: str | None = None


class PackageCompareRequest(BaseModel):
    package_ids: list[str] = Field(..., min_length=2)


class CustomPackageRequest(BaseModel):
    base_package_id: str
    overrides: dict[str, Any]
    code: str | None = None
    name: str | None = None


class DiscountRequest(BaseModel):
    target_type: str = "paquete"
    target_id: str
    tipo: str = "PORCENTAJE"
    valor_descuento: float
    valor_original: float
    motivo: str | None = None
    piso_economico: float | None = None
    bloquear_bajo_piso: bool = True


class ScalingRequest(BaseModel):
    num_usuarios: int | None = None
    num_empleados_ia: int | None = None
    num_integraciones: int | None = None
    consumo_ia_estimado: int | None = None


class PackagePriceRequest(BaseModel):
    valor_atribuible: float
    costo_total: float | None = None
