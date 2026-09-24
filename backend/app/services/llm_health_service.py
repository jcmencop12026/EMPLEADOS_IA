"""Salud de proveedores IA — Bloque 1270."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.gateway import gateway as llm_gateway
from app.gateway.provider_status import ProviderHealthStatus
from app.gateway.providers import PROVIDER_LABELS_ES, PROVIDER_MODES, is_executable_llm_provider, normalize_provider_type
from app.gateway.secrets import secret_configured
from app.llm_models import LlmInferenceLog, LlmProviderConfig


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _recent_error_rate(db: Session, organization_id: str, provider_type: str, hours: int = 24) -> float | None:
    since = _utcnow() - timedelta(hours=hours)
    total = (
        db.query(func.count(LlmInferenceLog.id))
        .filter(
            LlmInferenceLog.organization_id == organization_id,
            LlmInferenceLog.provider == provider_type,
            LlmInferenceLog.created_at >= since,
        )
        .scalar()
        or 0
    )
    if total == 0:
        return None
    errors = (
        db.query(func.count(LlmInferenceLog.id))
        .filter(
            LlmInferenceLog.organization_id == organization_id,
            LlmInferenceLog.provider == provider_type,
            LlmInferenceLog.created_at >= since,
            LlmInferenceLog.status != "OK",
        )
        .scalar()
        or 0
    )
    return errors / total


def assess_provider_health(db: Session, organization_id: str, config: LlmProviderConfig) -> dict[str, Any]:
    ptype = normalize_provider_type(config.provider_type)
    label = PROVIDER_LABELS_ES.get(ptype, ptype)
    mode = PROVIDER_MODES.get(ptype)
    configured = secret_configured(config.secret_ref) or ptype == "ollama"

    if not is_executable_llm_provider(ptype):
        estado = ProviderHealthStatus.NO_DISPONIBLE
        detalle = "Proveedor sin adaptador."
    elif not config.is_enabled:
        estado = ProviderHealthStatus.NO_DISPONIBLE
        detalle = "Proveedor deshabilitado."
    elif not configured:
        estado = ProviderHealthStatus.NO_CONFIGURADO
        detalle = "NO CONFIGURADO — sin credenciales."
    else:
        err_rate = _recent_error_rate(db, organization_id, ptype)
        if err_rate is not None and err_rate >= 0.5:
            estado = ProviderHealthStatus.DEGRADADO
            detalle = f"Tasa de error 24h: {err_rate:.0%}"
        else:
            estado = ProviderHealthStatus.DISPONIBLE
            detalle = "Operativo según configuración."

    return {
        "provider_id": config.id,
        "provider_type": ptype,
        "nombre": config.name,
        "etiqueta": label,
        "modo": mode.value if mode else None,
        "estado": estado.value,
        "detalle": detalle,
        "habilitado": config.is_enabled,
        "configurado": configured,
        "es_fallback": config.is_fallback,
        "prioridad": config.priority,
    }


def list_providers_health(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.organization_id == organization_id)
        .order_by(LlmProviderConfig.priority.asc())
        .all()
    )
    return [assess_provider_health(db, organization_id, row) for row in rows if is_executable_llm_provider(row.provider_type)]


def test_provider_health(
    db: Session,
    organization_id: str,
    provider_id: str,
    *,
    transport: Any | None = None,
) -> dict[str, Any]:
    config = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.id == provider_id, LlmProviderConfig.organization_id == organization_id)
        .first()
    )
    if not config:
        return {"estado": ProviderHealthStatus.NO_DISPONIBLE.value, "detalle": "Proveedor no encontrado."}
    base = assess_provider_health(db, organization_id, config)
    if base["estado"] == ProviderHealthStatus.NO_CONFIGURADO.value:
        return base
    result = llm_gateway.test_provider_connection(db, organization_id, provider_id, transport=transport)
    if result.success:
        base["estado"] = ProviderHealthStatus.DISPONIBLE.value
        base["detalle"] = "Prueba de conexión exitosa."
        base["latencia_ms"] = result.latency_ms
    else:
        category = str(result.error.category) if result.error else "ERROR"
        if category in {"PROVIDER_UNAVAILABLE", "TIMEOUT"}:
            base["estado"] = ProviderHealthStatus.NO_DISPONIBLE.value
        elif category == "AUTH_ERROR":
            base["estado"] = ProviderHealthStatus.NO_CONFIGURADO.value
        else:
            base["estado"] = ProviderHealthStatus.DEGRADADO.value
        base["detalle"] = result.error.message if result.error else "Error en prueba."
    return base
