"""Abstracción de proveedores de capacidades externas — EIAAX desacoplado de PIIAX."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Organization

# Estados de capacidad externa en español (contrato UX)
ESTADOS_CAPACIDAD_ES = frozenset({
    "NO DISPONIBLE",
    "DISPONIBLE",
    "PENDIENTE",
    "EN COLA",
    "EJECUTANDO",
    "ESPERANDO APROBACION",
    "COMPLETADO",
    "FALLIDO",
    "CANCELADO",
})

MAPEO_ESTADO_INTERNO_A_ES: dict[str, str] = {
    "BORRADOR": "PENDIENTE",
    "PENDIENTE_APROBACION": "ESPERANDO APROBACION",
    "APROBADA": "PENDIENTE",
    "RECHAZADA": "CANCELADO",
    "SOLICITADA": "EN COLA",
    "EN_PROCESO": "EJECUTANDO",
    "PIIAX_NO_DISPONIBLE": "NO DISPONIBLE",
    "COMPLETADA": "COMPLETADO",
    "ERROR": "FALLIDO",
    "CANCELADA": "CANCELADO",
}


def estado_capacidad_es(estado_interno: str, proveedor_disponible: bool = True) -> str:
    if estado_interno == "PIIAX_NO_DISPONIBLE" or not proveedor_disponible:
        return "NO DISPONIBLE"
    return MAPEO_ESTADO_INTERNO_A_ES.get(estado_interno, "PENDIENTE")


def _org_config(db: Session, organization_id: str) -> dict[str, Any]:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org or not org.config_json:
        return {}
    try:
        cfg = json.loads(org.config_json)
        return cfg if isinstance(cfg, dict) else {}
    except json.JSONDecodeError:
        return {}


class ProveedorExternoAdapter(ABC):
    """Interfaz para adaptadores de capacidades externas (PIIAX u otros)."""

    codigo: str
    nombre: str
    preferente: bool = False

    @abstractmethod
    def disponible(self, db: Session, organization_id: str) -> bool:
        ...

    @abstractmethod
    def listar_capacidades(self, db: Session, organization_id: str) -> list[str]:
        ...

    @abstractmethod
    def solicitar_ejecucion(
        self,
        *,
        capacidad: str,
        tipo_accion: str,
        correlation_id: str,
        parametros: dict[str, Any] | None,
    ) -> dict[str, Any]:
        ...

    def consultar_estado(self, referencia_externa: str) -> dict[str, Any]:
        return {"estado": "PENDIENTE", "mensaje": "Consulta de estado no implementada para este adaptador."}

    def cancelar(self, referencia_externa: str) -> dict[str, Any]:
        return {"cancelado": False, "mensaje": "Cancelación no implementada para este adaptador."}

    def trazabilidad_resumida(self, referencia_externa: str) -> dict[str, Any]:
        return {"referencia": referencia_externa, "eventos": []}

    def detalle_tecnico_url(self, db: Session, organization_id: str, referencia_externa: str | None) -> str | None:
        return None


class PiiaxAdapter(ProveedorExternoAdapter):
    codigo = "PIIAX"
    nombre = "PIIAX"
    preferente = True

    def disponible(self, db: Session, organization_id: str) -> bool:
        org_cfg = _org_config(db, organization_id).get("piiax", {})
        enabled_env = getattr(settings, "piiax_bridge_enabled", False)
        return bool(enabled_env or org_cfg.get("enabled"))

    def listar_capacidades(self, db: Session, organization_id: str) -> list[str]:
        from app.evaluacion_models import CAPACIDADES_EXTERNAS

        if not self.disponible(db, organization_id):
            return []
        return sorted(CAPACIDADES_EXTERNAS)

    def solicitar_ejecucion(
        self,
        *,
        capacidad: str,
        tipo_accion: str,
        correlation_id: str,
        parametros: dict[str, Any] | None,
    ) -> dict[str, Any]:
        # Sin simular ejecución exitosa cuando no está conectado
        return {
            "enviado": False,
            "estado": "PIIAX_NO_DISPONIBLE",
            "estado_es": "NO DISPONIBLE",
            "referencia_externa": None,
            "proveedor": self.codigo,
            "mensaje": "PIIAX no conectado. La solicitud queda registrada en EIAAX para ejecución posterior.",
        }

    def solicitar_ejecucion_conectado(
        self,
        *,
        capacidad: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        return {
            "enviado": True,
            "estado": "SOLICITADA",
            "estado_es": "EN COLA",
            "referencia_externa": f"piiax-prep-{correlation_id[:8]}",
            "proveedor": self.codigo,
            "mensaje": "Solicitud enviada a PIIAX para resolución técnica.",
        }

    def detalle_tecnico_url(self, db: Session, organization_id: str, referencia_externa: str | None) -> str | None:
        if not referencia_externa:
            return None
        base = _org_config(db, organization_id).get("piiax", {}).get("detalle_url")
        if not base:
            return None
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}ref={referencia_externa}"


_ADAPTERS: dict[str, ProveedorExternoAdapter] = {
    "PIIAX": PiiaxAdapter(),
}


def registrar_adaptador(adapter: ProveedorExternoAdapter) -> None:
    _ADAPTERS[adapter.codigo] = adapter


def listar_proveedores(db: Session, organization_id: str) -> list[dict[str, Any]]:
    items = []
    for code, adapter in sorted(_ADAPTERS.items()):
        disp = adapter.disponible(db, organization_id)
        items.append({
            "codigo": code,
            "nombre": adapter.nombre,
            "preferente": adapter.preferente,
            "disponible": disp,
            "estado_es": "DISPONIBLE" if disp else "NO DISPONIBLE",
            "capacidades": adapter.listar_capacidades(db, organization_id) if disp else [],
        })
    return items


def resolver_proveedor(
    db: Session,
    organization_id: str,
    *,
    capacidad: str,
    preferido: str | None = None,
) -> ProveedorExternoAdapter | None:
    if preferido and preferido in _ADAPTERS:
        adapter = _ADAPTERS[preferido]
        if adapter.disponible(db, organization_id):
            caps = adapter.listar_capacidades(db, organization_id)
            if not caps or capacidad in caps:
                return adapter
        return None

    # Preferente primero, luego otros disponibles
    ordenados = sorted(_ADAPTERS.values(), key=lambda a: (not a.preferente, a.codigo))
    for adapter in ordenados:
        if adapter.disponible(db, organization_id):
            caps = adapter.listar_capacidades(db, organization_id)
            if not caps or capacidad in caps:
                return adapter
    return None


def solicitar_capacidad_externa(
    db: Session,
    organization_id: str,
    *,
    capacidad: str,
    tipo_accion: str,
    correlation_id: str,
    parametros: dict[str, Any] | None,
    proveedor_preferido: str | None = None,
) -> dict[str, Any]:
    adapter = resolver_proveedor(
        db, organization_id, capacidad=capacidad, preferido=proveedor_preferido,
    )
    if not adapter:
        return {
            "enviado": False,
            "estado": "PIIAX_NO_DISPONIBLE",
            "estado_es": "NO DISPONIBLE",
            "referencia_externa": None,
            "proveedor": None,
            "mensaje": "Ningún proveedor externo disponible. La solicitud queda registrada en EIAAX.",
        }

    if isinstance(adapter, PiiaxAdapter) and adapter.disponible(db, organization_id):
        # Stub conectado: encolar sin simular éxito de ejecución real
        if getattr(settings, "piiax_bridge_enabled", False) or _org_config(db, organization_id).get("piiax", {}).get("enabled"):
            return adapter.solicitar_ejecucion_conectado(capacidad=capacidad, correlation_id=correlation_id)

    result = adapter.solicitar_ejecucion(
        capacidad=capacidad,
        tipo_accion=tipo_accion,
        correlation_id=correlation_id,
        parametros=parametros,
    )
    result.setdefault("estado_es", estado_capacidad_es(result.get("estado", "PENDIENTE"), adapter.disponible(db, organization_id)))
    result.setdefault("proveedor", adapter.codigo)
    return result
