"""Contratos de integración futura — Inteligencia económica EIAAX (1740).

GENERAL puede sustituir adaptadores sin acoplar V1 estable.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EconomicIntelligencePort(Protocol):
    """Frontera agregada resultado económico + valor empresarial."""

    def resultado_economico(self, org_id: str, *, period_days: int = 30) -> dict[str, Any]: ...

    def valor_empresarial(self, org_id: str, *, period_days: int = 30) -> dict[str, Any]: ...


@runtime_checkable
class ScenarioSimulatorPort(Protocol):
    """Frontera simulador multi-escenario."""

    def comparar_escenarios(self, org_id: str, params: dict[str, Any]) -> dict[str, Any]: ...

    def dimensionar(self, org_id: str, params: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class EmployeeEconomicsPort(Protocol):
    def resumen_empleado(self, org_id: str, employee_id: str, *, days: int = 30) -> dict[str, Any]: ...


@runtime_checkable
class CommercialPricingIntelligencePort(Protocol):
    """Inteligencia comercial interna — nunca publica precio automáticamente."""

    def inteligencia_comercial(self, org_id: str, *, proposal_id: str | None = None) -> dict[str, Any]: ...

    def recomendar_precio_valor(
        self, org_id: str, *, fraccion_valor: float, attributable_value: float | None = None
    ) -> dict[str, Any]: ...


class LocalEconomicIntelligenceAdapter:
    """Adaptador local — reemplazable por GENERAL."""

    def __init__(self, db, user=None):
        from app.services import inteligencia_economica_service as svc

        self._db = db
        self._user = user
        self._svc = svc

    def resultado_economico(self, org_id: str, *, period_days: int = 30) -> dict[str, Any]:
        return self._svc.resultado_economico(self._db, org_id, period_days=period_days)

    def valor_empresarial(self, org_id: str, *, period_days: int = 30) -> dict[str, Any]:
        return self._svc.valor_empresarial(self._db, org_id, period_days=period_days)

    def comparar_escenarios(self, org_id: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._svc.comparar_escenarios(self._db, self._user, org_id, params)

    def dimensionar(self, org_id: str, params: dict[str, Any]) -> dict[str, Any]:
        return self._svc.dimensionar_capacidad(self._db, org_id, params)

    def resumen_empleado(self, org_id: str, employee_id: str, *, days: int = 30) -> dict[str, Any]:
        return self._svc.economia_empleado(self._db, org_id, employee_id, days=days)


def get_economic_intelligence_adapter(db, user=None) -> EconomicIntelligencePort:
    return LocalEconomicIntelligenceAdapter(db, user)
