"""Contrato inteligencia externa — evidencia autorizada sin scraping."""

from __future__ import annotations

from typing import Any, TypedDict


class EvidenciaExternaContrato(TypedDict, total=False):
    fuente_id: str
    fuente_nombre: str
    dominio: str
    fecha_observacion: str
    confianza: float
    trazabilidad_enlace: str
    contenido_resumen: str
    autorizado: bool


DOMINIOS_EXTERNOS = frozenset({
    "mercado",
    "competencia",
    "regulacion",
    "tecnologia",
    "tendencias",
    "precios",
    "oportunidades_externas",
})


def normalizar_evidencia_externa(raw: dict[str, Any]) -> EvidenciaExternaContrato:
    """Fail-closed: sin autorización explícita no se incorpora como hecho."""
    autorizado = bool(raw.get("autorizado") and raw.get("fuente_id"))
    return {
        "fuente_id": raw.get("fuente_id"),
        "fuente_nombre": raw.get("fuente_nombre"),
        "dominio": raw.get("dominio"),
        "fecha_observacion": raw.get("fecha_observacion"),
        "confianza": float(raw.get("confianza") or 0),
        "trazabilidad_enlace": raw.get("trazabilidad_enlace") or f"/inteligencia-externa/senales/{raw.get('senal_id', '')}",
        "contenido_resumen": (raw.get("contenido_resumen") or "")[:500],
        "autorizado": autorizado,
    }
