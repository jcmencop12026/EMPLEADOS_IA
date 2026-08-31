"""Esquemas — Continuidad comercial y operacional (1720)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ConvertirImplementacionIn(BaseModel):
    condiciones: str | None = None


class CambioAlcanceCreate(BaseModel):
    proposal_id: str
    proyecto_id: str | None = None
    contract_id: str | None = None
    solicitud: str


class CambioAlcanceAvanzar(BaseModel):
    accion: str
    analisis: str | None = None
    impacto: dict[str, Any] | None = None
    decision: str | None = None
    aprobado: bool | None = None
    rechazado: bool | None = None
    crear_version_comercial: bool = False


class CierreContratoCreate(BaseModel):
    motivo: str
    pendientes: list[str] | None = None
    empleados_retirar: list[str] | None = None
    accesos_retirar: list[str] | None = None
    exportaciones: list[str] | None = None
    observaciones: str | None = None


class CierreContratoConfirmar(BaseModel):
    confirmacion: bool = True


class EntregableCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    responsable_id: str | None = None
    fecha_objetivo: datetime | None = None
    documento_id: str | None = None
    version_referencia: str | None = None


class EntregableUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    estado: str | None = None
    evidencia: str | None = None
    aceptacion: str | None = None
    observaciones: str | None = None


class TareaCompletar(BaseModel):
    evidencia: str | None = None
    resultado: str | None = None


class BloqueadorResolver(BaseModel):
    observaciones: str | None = None


class RenovacionContinuidadCreate(BaseModel):
    proyecto_id: str
    plan_id: str | None = None
    fecha_renovacion: datetime | None = None
    notas: str | None = None
    crear_oportunidad: bool = False
    titulo_oportunidad: str | None = None


class ExpansionContinuidadCreate(BaseModel):
    proyecto_id: str
    tipo: str
    descripcion: str
    recomendacion: str | None = None
    crear_oportunidad: bool = False
    titulo_oportunidad: str | None = None
