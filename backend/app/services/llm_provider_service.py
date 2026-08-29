"""Servicio de administración de proveedores IA."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gateway.providers import is_executable_llm_provider
from app.gateway.secrets import build_env_secret_ref, mask_secret, resolve_secret, secret_configured
from app.llm_models import LlmInferenceLog, LlmProviderConfig
from app.schemas_llm import LlmProviderCreate, LlmProviderUpdate


def _serialize_provider(config: LlmProviderConfig) -> dict[str, Any]:
    secret_value = resolve_secret(config.secret_ref)
    return {
        "id": config.id,
        "organization_id": config.organization_id,
        "name": config.name,
        "provider_type": config.provider_type,
        "model_default": config.model_default,
        "endpoint": config.endpoint,
        "timeout_seconds": config.timeout_seconds,
        "priority": config.priority,
        "is_enabled": config.is_enabled,
        "is_fallback": config.is_fallback,
        "secret_ref": config.secret_ref,
        "secret_configured": secret_configured(config.secret_ref),
        "secret_masked": mask_secret(secret_value) if secret_value else None,
        "config_json": json.loads(config.config_json) if config.config_json else None,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


def list_providers(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.organization_id == organization_id)
        .order_by(LlmProviderConfig.priority.asc(), LlmProviderConfig.name.asc())
        .all()
    )
    return [_serialize_provider(r) for r in rows if is_executable_llm_provider(r.provider_type)]


def get_provider(db: Session, organization_id: str, provider_id: str) -> dict[str, Any] | None:
    row = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.id == provider_id, LlmProviderConfig.organization_id == organization_id)
        .first()
    )
    return _serialize_provider(row) if row else None


def create_provider(
    db: Session,
    organization_id: str,
    data: LlmProviderCreate,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    provider_type = data.provider_type.lower().strip()
    if not is_executable_llm_provider(provider_type):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Proveedor no ejecutable en V1. Solo openai u ollama están disponibles.",
        )
    secret_ref = build_env_secret_ref(data.secret_env_var) if data.secret_env_var else None
    row = LlmProviderConfig(
        organization_id=organization_id,
        name=data.name,
        provider_type=provider_type,
        model_default=data.model_default,
        endpoint=data.endpoint,
        timeout_seconds=data.timeout_seconds,
        priority=data.priority,
        is_enabled=data.is_enabled,
        is_fallback=data.is_fallback,
        secret_ref=secret_ref,
        config_json=json.dumps(data.config_json, ensure_ascii=False) if data.config_json else None,
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        action="llm.provider.create",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"Proveedor IA creado: {row.name} ({row.provider_type})",
    )
    db.commit()
    db.refresh(row)
    return _serialize_provider(row)


def update_provider(
    db: Session,
    organization_id: str,
    provider_id: str,
    data: LlmProviderUpdate,
    *,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    row = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.id == provider_id, LlmProviderConfig.organization_id == organization_id)
        .first()
    )
    if not row:
        return None

    if data.name is not None:
        row.name = data.name
    if data.model_default is not None:
        row.model_default = data.model_default
    if data.endpoint is not None:
        row.endpoint = data.endpoint
    if data.timeout_seconds is not None:
        row.timeout_seconds = data.timeout_seconds
    if data.priority is not None:
        row.priority = data.priority
    if data.is_enabled is not None:
        row.is_enabled = data.is_enabled
    if data.is_fallback is not None:
        row.is_fallback = data.is_fallback
    if data.secret_env_var is not None:
        row.secret_ref = build_env_secret_ref(data.secret_env_var) if data.secret_env_var else None
    if data.config_json is not None:
        row.config_json = json.dumps(data.config_json, ensure_ascii=False)

    write_audit(
        db,
        action="llm.provider.update",
        organization_id=organization_id,
        user_id=user_id,
        detail=f"Proveedor IA actualizado: {row.name}",
    )
    db.commit()
    db.refresh(row)
    return _serialize_provider(row)


def list_inference_logs(
    db: Session,
    organization_id: str,
    *,
    limit: int = 50,
) -> list[LlmInferenceLog]:
    return (
        db.query(LlmInferenceLog)
        .filter(LlmInferenceLog.organization_id == organization_id)
        .order_by(LlmInferenceLog.created_at.desc())
        .limit(limit)
        .all()
    )
