"""Esquemas — Centro de Negocios EIAAX."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PropuestaDesdeExpedienteIn(BaseModel):
    evaluacion_id: str
    opportunity_id: str | None = None
    titulo: str | None = None
    modelo_comercial: str | None = None


class PropuestaTransicionIn(BaseModel):
    nuevo_estado: str
    motivo: str | None = None


class PrecioDecisionIn(BaseModel):
    action: str = Field(..., description="ACEPTAR | MODIFICAR | DESCARTAR")
    precio_decidido: float | None = None
    justificacion: str | None = None


class NegociacionIn(BaseModel):
    version_presentada: int | None = None
    fecha_presentacion: datetime | None = None
    interlocutor: str | None = None
    observaciones: str | None = None
    cambios_solicitados: str | None = None
    proximo_paso: str | None = None
    estado: str = "ABIERTA"
    crear_nueva_version: bool = False


class IaConsumoIn(BaseModel):
    consumo_incluido_tokens: int | None = None
    consumo_incluido_usd: float | None = None
    consumo_variable: bool = True
    proveedor: str | None = None
    modelo: str | None = None
    credential_mode: str | None = None
    infraestructura_licencias: str | None = None
    excedente_overage: str | None = None


class PerspectivaUpdateIn(BaseModel):
    perspectiva: str
    contenido: dict[str, Any]


class ApprovalLevelIn(BaseModel):
    nivel: str
    comentario: str | None = None


class ContractIn(BaseModel):
    condiciones: str | None = None
    version_id: str | None = None


class ApprovalPolicyIn(BaseModel):
    levels: list[str]
    enabled: bool = True


class SyncIn(BaseModel):
    direction: str = "both"
