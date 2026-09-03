"""Adapter de informes periódicos comerciales — integración MB-11 sin duplicar scheduler."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.demo_comercial_constants import AUDIENCIAS, INFORMES_PERIODICIDAD
from app.presentacion_models import InformeComercialConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _proximo_envio_desde(periodicidad: str, desde: datetime | None = None) -> datetime:
    base = desde or _utcnow()
    deltas = {
        "DIARIO": timedelta(days=1),
        "SEMANAL": timedelta(days=7),
        "MENSUAL": timedelta(days=30),
        "TRIMESTRAL": timedelta(days=90),
        "EVENTO": timedelta(days=365),
    }
    return base + deltas.get(periodicidad.upper(), timedelta(days=30))


def config_to_dict(row: InformeComercialConfig) -> dict[str, Any]:
    destinatarios: list[str] = []
    if row.destinatarios_json:
        try:
            destinatarios = json.loads(row.destinatarios_json)
        except json.JSONDecodeError:
            destinatarios = []
    return {
        "id": row.id,
        "nombre": row.nombre,
        "expediente_id": row.expediente_id,
        "audiencia": row.audiencia,
        "periodicidad": row.periodicidad,
        "destinatarios": destinatarios,
        "resumen": row.resumen,
        "enlace_seguro": row.enlace_seguro,
        "activo": row.activo,
        "ultimo_envio": row.ultimo_envio.isoformat() if row.ultimo_envio else None,
        "proximo_envio": row.proximo_envio.isoformat() if row.proximo_envio else None,
        "estado": row.estado,
        "error_ultimo": row.error_ultimo,
        "comm_rule_id": row.comm_rule_id,
        "integracion": {
            "scheduler": "MB-11 automation_scheduler + comm_rules",
            "contrato_event_type": "INFORME_COMERCIAL_PERIODICO",
            "integrado": row.comm_rule_id is not None,
            "nota": (
                "El envío real lo ejecuta Centro de Información cuando la regla MB-11 "
                "esté cableada; este adapter persiste configuración comercial."
            ),
        },
    }


def list_configs(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(InformeComercialConfig)
        .filter(InformeComercialConfig.organization_id == organization_id)
        .order_by(InformeComercialConfig.created_at.desc())
        .all()
    )
    return [config_to_dict(r) for r in rows]


def create_config(
    db: Session,
    organization_id: str,
    user_id: str,
    *,
    nombre: str,
    audiencia: str,
    periodicidad: str,
    destinatarios: list[str] | None = None,
    resumen: str | None = None,
    expediente_id: str | None = None,
    enlace_seguro: bool = True,
    activo: bool = True,
) -> dict[str, Any]:
    audiencia = audiencia.upper()
    periodicidad = periodicidad.upper()
    if audiencia not in AUDIENCIAS:
        raise ValueError(f"Audiencia no válida: {audiencia}")
    if periodicidad not in INFORMES_PERIODICIDAD:
        raise ValueError(f"Periodicidad no válida: {periodicidad}")

    now = _utcnow()
    row = InformeComercialConfig(
        organization_id=organization_id,
        expediente_id=expediente_id,
        nombre=nombre,
        audiencia=audiencia,
        periodicidad=periodicidad,
        destinatarios_json=json.dumps(destinatarios or []),
        resumen=resumen,
        enlace_seguro=enlace_seguro,
        activo=activo,
        proximo_envio=_proximo_envio_desde(periodicidad, now),
        estado="PENDIENTE_INTEGRACION",
        created_by=user_id,
    )
    db.add(row)
    db.flush()
    return config_to_dict(row)


def update_config(
    db: Session,
    organization_id: str,
    config_id: str,
    *,
    activo: bool | None = None,
    destinatarios: list[str] | None = None,
    resumen: str | None = None,
) -> dict[str, Any]:
    row = (
        db.query(InformeComercialConfig)
        .filter(
            InformeComercialConfig.id == config_id,
            InformeComercialConfig.organization_id == organization_id,
        )
        .first()
    )
    if not row:
        raise LookupError("Configuración no encontrada.")
    if activo is not None:
        row.activo = activo
    if destinatarios is not None:
        row.destinatarios_json = json.dumps(destinatarios)
    if resumen is not None:
        row.resumen = resumen
    row.updated_at = _utcnow()
    if row.activo and not row.proximo_envio:
        row.proximo_envio = _proximo_envio_desde(row.periodicidad)
    db.flush()
    return config_to_dict(row)


def plantillas_periodicas() -> list[dict[str, Any]]:
    from app.services.demo_comercial_service import informes_periodicos_plantillas

    return informes_periodicos_plantillas()
