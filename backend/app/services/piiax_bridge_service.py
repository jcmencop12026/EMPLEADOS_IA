"""Puente de preparación EIAAX ↔ PIIAX — sin implementar PIIAX ni conectores."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Organization

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
    """Estado de disponibilidad PIIAX — sin llamar endpoints concretos."""
    org_cfg = _org_piiax_config(db, organization_id)
    enabled_env = getattr(settings, "piiax_bridge_enabled", False)
    enabled_org = bool(org_cfg.get("enabled"))
    disponible = enabled_env or enabled_org

    return {
        "disponible": disponible,
        "mensaje": (
            "PIIAX conectado y listo para resolver capacidades técnicas."
            if disponible
            else "PIIAX no está conectado. Las solicitudes quedarán en estado controlado hasta la integración."
        ),
        "detalle_tecnico_url": org_cfg.get("detalle_url") if disponible else None,
        "modo": "conectado" if disponible else "no_conectado",
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
    capacidad: str,
    tipo_accion: str,
    correlation_id: str,
    parametros: dict[str, Any] | None,
    piiax_disponible: bool,
) -> dict[str, Any]:
    """Simula handoff a PIIAX — no ejecuta conectores reales."""
    if not piiax_disponible:
        return {
            "enviado": False,
            "estado": "PIIAX_NO_DISPONIBLE",
            "referencia_externa": None,
            "mensaje": "PIIAX no conectado. La solicitud queda registrada en EIAAX para ejecución posterior.",
        }
    return {
        "enviado": True,
        "estado": "SOLICITADA",
        "referencia_externa": f"piiax-prep-{correlation_id[:8]}",
        "mensaje": "Solicitud enviada a PIIAX para resolución técnica.",
    }


def get_detalle_tecnico_link(referencia_externa: str | None, org_cfg: dict[str, Any]) -> str | None:
    """URL desacoplada para ver detalle técnico en PIIAX — plantilla configurable."""
    if not referencia_externa:
        return None
    base = org_cfg.get("detalle_url")
    if not base:
        return None
    return f"{base.rstrip('/')}?ref={referencia_externa}"
