"""Puente de preparación EIAAX ↔ PIIAX — delega en adaptador desacoplado."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import Organization
from app.services.evaluacion_proveedor_externo_service import (
    PiiaxAdapter,
    listar_proveedores,
    solicitar_capacidad_externa,
)

CAPACIDAD_LABELS: dict[str, str] = {
    "consultar_datos": "Consultar datos",
    "enviar_informacion": "Enviar información",
    "validar_registros": "Validar registros",
    "sincronizar": "Sincronizar",
    "transformar": "Transformar",
    "obtener_documento": "Obtener documento",
    "ejecutar_proceso": "Ejecutar proceso",
    "notificar": "Notificar",
    "consultar_estado": "Consultar estado",
}

CAPACIDAD_DESCRIPCIONES: dict[str, str] = {
    "consultar_datos": "Obtener información desde fuentes externas para enriquecer el expediente.",
    "enviar_informacion": "Remitir datos o resultados hacia un sistema externo.",
    "validar_registros": "Verificar integridad o consistencia de registros externos.",
    "sincronizar": "Alinear información entre EIAAX y sistemas conectados vía PIIAX.",
    "transformar": "Aplicar transformación técnica sobre datos (resuelto en PIIAX).",
    "obtener_documento": "Recuperar un documento o evidencia desde fuente externa.",
    "ejecutar_proceso": "Disparar un proceso automatizado externo (requiere aprobación).",
    "notificar": "Enviar notificación a sistema o canal externo.",
    "consultar_estado": "Consultar estado de una ejecución externa previa.",
}

TIPO_ACCION_LABELS: dict[str, str] = {
    "LECTURA": "Lectura",
    "ANALISIS": "Análisis",
    "PROPUESTA": "Propuesta",
    "EJECUCION": "Ejecución",
}

TIPO_REQUIERE_APROBACION = frozenset({"PROPUESTA", "EJECUCION"})


def _org_piiax_config(db: Session, organization_id: str) -> dict[str, Any]:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org or not org.config_json:
        return {}
    try:
        cfg = json.loads(org.config_json)
        return cfg.get("piiax", {}) if isinstance(cfg, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_piiax_status(db: Session, organization_id: str) -> dict[str, Any]:
    """Estado PIIAX vía adaptador — EIAAX funciona igual si no está disponible."""
    adapter = PiiaxAdapter()
    disponible = adapter.disponible(db, organization_id)
    org_cfg = _org_piiax_config(db, organization_id)
    proveedores = listar_proveedores(db, organization_id)
    piiax_prov = next((p for p in proveedores if p["codigo"] == "PIIAX"), None)

    return {
        "disponible": disponible,
        "estado_es": piiax_prov["estado_es"] if piiax_prov else ("DISPONIBLE" if disponible else "NO DISPONIBLE"),
        "mensaje": (
            "PIIAX conectado y listo para resolver capacidades técnicas."
            if disponible
            else "PIIAX no está conectado. EIAAX continúa operando con capacidades propias."
        ),
        "detalle_tecnico_url": org_cfg.get("detalle_url") if disponible else None,
        "modo": "conectado" if disponible else "no_conectado",
        "proveedores": proveedores,
    }


def list_capacidades_catalog() -> list[dict[str, str]]:
    from app.evaluacion_models import CAPACIDADES_EXTERNAS

    return [
        {
            "codigo": code,
            "etiqueta": CAPACIDAD_LABELS.get(code, code),
            "descripcion": CAPACIDAD_DESCRIPCIONES.get(code, ""),
        }
        for code in sorted(CAPACIDADES_EXTERNAS)
    ]


def solicitar_ejecucion_piiax(
    *,
    db: Session,
    organization_id: str,
    capacidad: str,
    tipo_accion: str,
    correlation_id: str,
    parametros: dict[str, Any] | None,
    piiax_disponible: bool | None = None,
) -> dict[str, Any]:
    """Delega en capa de proveedores — no simula ejecución exitosa sin PIIAX real."""
    return solicitar_capacidad_externa(
        db,
        organization_id,
        capacidad=capacidad,
        tipo_accion=tipo_accion,
        correlation_id=correlation_id,
        parametros=parametros,
        proveedor_preferido="PIIAX",
    )


def get_detalle_tecnico_link(referencia_externa: str | None, org_cfg: dict[str, Any]) -> str | None:
    if not referencia_externa:
        return None
    base = org_cfg.get("detalle_url")
    if not base:
        return None
    return f"{base.rstrip('/')}?ref={referencia_externa}"
