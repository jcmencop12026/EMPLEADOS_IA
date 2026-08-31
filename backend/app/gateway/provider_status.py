"""Estados de salud y disponibilidad de proveedores IA — Bloque 1270."""

from __future__ import annotations

from enum import StrEnum


class ProviderHealthStatus(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    DEGRADADO = "DEGRADADO"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    NO_CONFIGURADO = "NO_CONFIGURADO"


class ProviderAdapterMode(StrEnum):
    OPERATIVO = "OPERATIVO"
    PREPARADO = "PREPARADO"
    OPCIONAL = "OPCIONAL"
