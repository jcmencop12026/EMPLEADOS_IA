"""Esquemas — Inteligencia económica EIAAX (1740)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompararEscenariosIn(BaseModel):
    personas: int = 10
    personas_escenario: int | None = None
    horas_por_persona_mes: float = 160
    valor_hora: float = 25
    costo_hora: float = 18
    empleados_ia: int = 0
    automatizacion_pct: float = 0.35
    days: int = 30
    escenarios: list[str] | None = None
    persistir: bool = False
    titulo: str | None = None
    scope_type: str = "ORGANIZACION"
    scope_id: str | None = None


class DimensionarIn(BaseModel):
    personas_actual: int = 10
    personas_escenario: int = 7
    empleados_ia: int = 1
    automatizacion_pct: float = 0.35
    horas_por_persona_mes: float = 160
    modo: str = "CAPACIDAD_LIBERADA"


class RecomendarPrecioValorIn(BaseModel):
    fraccion_valor: float = Field(0.4, ge=0.05, le=0.95)
    attributable_value: float | None = None
    proposal_id: str | None = None
    margen_min: float = Field(0.2, ge=0, le=0.9)
