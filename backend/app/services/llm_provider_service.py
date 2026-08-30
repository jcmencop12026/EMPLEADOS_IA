"""Servicio de administración de proveedores IA — Bloque 1270."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit
from app.gateway.providers import (
    KNOWN_LLM_PROVIDERS,
    PROVIDER_LABELS_ES,
    PROVIDER_MODES,
    is_executable_llm_provider,
    normalize_provider_type,
)
from app.gateway.secrets import build_env_secret_ref, mask_secret, resolve_secret, secret_configured
from app.llm_models import LlmInferenceLog, LlmModelCatalog, LlmProviderConfig, LlmRoutingPolicy
from app.schemas_llm import LlmModelCatalogCreate, LlmProviderCreate, LlmProviderUpdate, LlmRoutingPolicyCreate, LlmRoutingPolicyUpdate
from app.services.llm_health_service import assess_provider_health


def _serialize_provider(db: Session, organization_id: str, config: LlmProviderConfig) -> dict[str, Any]:
    secret_value = resolve_secret(config.secret_ref)
    health = assess_provider_health(db, organization_id, config)
    ptype = normalize_provider_type(config.provider_type)
    return {
        "id": config.id,
        "organization_id": config.organization_id,
        "name": config.name,
        "provider_type": config.provider_type,
        "provider_label": PROVIDER_LABELS_ES.get(ptype, ptype),
        "adapter_mode": PROVIDER_MODES.get(ptype).value if PROVIDER_MODES.get(ptype) else None,
        "model_default": config.model_default,
        "endpoint": config.endpoint,
        "timeout_seconds": config.timeout_seconds,
        "priority": config.priority,
        "is_enabled": config.is_enabled,
        "is_fallback": config.is_fallback,
        "secret_ref": config.secret_ref,
        "secret_configured": secret_configured(config.secret_ref) or ptype == "ollama",
        "secret_masked": mask_secret(secret_value) if secret_value else None,
        "config_json": json.loads(config.config_json) if config.config_json else None,
        "health_status": health["estado"],
        "health_detail": health["detalle"],
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
    return [_serialize_provider(db, organization_id, r) for r in rows if is_executable_llm_provider(r.provider_type)]


def get_provider(db: Session, organization_id: str, provider_id: str) -> dict[str, Any] | None:
    row = (
        db.query(LlmProviderConfig)
        .filter(LlmProviderConfig.id == provider_id, LlmProviderConfig.organization_id == organization_id)
        .first()
    )
    return _serialize_provider(db, organization_id, row) if row else None


def create_provider(
    db: Session,
    organization_id: str,
    data: LlmProviderCreate,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    provider_type = normalize_provider_type(data.provider_type)
    if provider_type not in KNOWN_LLM_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de proveedor no reconocido.")
    if not is_executable_llm_provider(provider_type):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Proveedor sin adaptador implementado.")
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
    return _serialize_provider(db, organization_id, row)


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
    return _serialize_provider(db, organization_id, row)


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


def update_inference_log_cost(
    db: Session,
    organization_id: str,
    trace_id: str,
    *,
    cost: float | None,
    currency: str | None,
) -> None:
    row = (
        db.query(LlmInferenceLog)
        .filter(LlmInferenceLog.organization_id == organization_id, LlmInferenceLog.trace_id == trace_id)
        .first()
    )
    if row:
        row.cost = cost
        row.currency = currency
        db.flush()


def list_model_catalog(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LlmModelCatalog)
        .filter(LlmModelCatalog.organization_id == organization_id)
        .order_by(LlmModelCatalog.priority.asc(), LlmModelCatalog.display_name.asc())
        .all()
    )
    return [
        {
            "id": r.id,
            "provider_type": r.provider_type,
            "model_id": r.model_id,
            "display_name": r.display_name,
            "estado": r.estado,
            "capabilities": json.loads(r.capabilities_json) if r.capabilities_json else {},
            "context_window": r.context_window,
            "modalities": json.loads(r.modalities_json) if r.modalities_json else [],
            "cost_hint": json.loads(r.cost_hint_json) if r.cost_hint_json else None,
            "priority": r.priority,
            "is_enabled": r.is_enabled,
        }
        for r in rows
    ]


def create_model_catalog_entry(
    db: Session,
    organization_id: str,
    data: LlmModelCatalogCreate,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    row = LlmModelCatalog(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        provider_type=normalize_provider_type(data.provider_type),
        model_id=data.model_id,
        display_name=data.display_name,
        estado=data.estado,
        capabilities_json=json.dumps(data.capabilities, ensure_ascii=False) if data.capabilities else None,
        context_window=data.context_window,
        modalities_json=json.dumps(data.modalities, ensure_ascii=False) if data.modalities else None,
        cost_hint_json=json.dumps(data.cost_hint, ensure_ascii=False) if data.cost_hint else None,
        priority=data.priority,
        is_enabled=data.is_enabled,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="llm.model.create", organization_id=organization_id, user_id=user_id, detail=row.model_id)
    db.commit()
    return list_model_catalog(db, organization_id)[-1]


def list_routing_policies(db: Session, organization_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LlmRoutingPolicy)
        .filter(LlmRoutingPolicy.organization_id == organization_id)
        .order_by(LlmRoutingPolicy.priority.asc())
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "preferred_provider": r.preferred_provider,
            "preferred_model": r.preferred_model,
            "required_capability": r.required_capability,
            "fallback_allowed": r.fallback_allowed,
            "max_cost_per_1k_tokens": r.max_cost_per_1k_tokens,
            "credential_scope": r.credential_scope,
            "priority": r.priority,
            "is_active": r.is_active,
        }
        for r in rows
    ]


def create_routing_policy(
    db: Session,
    organization_id: str,
    data: LlmRoutingPolicyCreate,
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    row = LlmRoutingPolicy(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        name=data.name,
        preferred_provider=normalize_provider_type(data.preferred_provider) if data.preferred_provider else None,
        preferred_model=data.preferred_model,
        required_capability=data.required_capability,
        fallback_allowed=data.fallback_allowed,
        max_cost_per_1k_tokens=data.max_cost_per_1k_tokens,
        credential_scope=data.credential_scope,
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(row)
    db.flush()
    write_audit(db, action="llm.routing.create", organization_id=organization_id, user_id=user_id, detail=row.name)
    db.commit()
    return list_routing_policies(db, organization_id)[-1]


def update_routing_policy(
    db: Session,
    organization_id: str,
    policy_id: str,
    data: LlmRoutingPolicyUpdate,
    *,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    row = (
        db.query(LlmRoutingPolicy)
        .filter(LlmRoutingPolicy.id == policy_id, LlmRoutingPolicy.organization_id == organization_id)
        .first()
    )
    if not row:
        return None
    if data.name is not None:
        row.name = data.name
    if data.preferred_provider is not None:
        row.preferred_provider = normalize_provider_type(data.preferred_provider) if data.preferred_provider else None
    if data.preferred_model is not None:
        row.preferred_model = data.preferred_model
    if data.required_capability is not None:
        row.required_capability = data.required_capability
    if data.fallback_allowed is not None:
        row.fallback_allowed = data.fallback_allowed
    if data.max_cost_per_1k_tokens is not None:
        row.max_cost_per_1k_tokens = data.max_cost_per_1k_tokens
    if data.credential_scope is not None:
        row.credential_scope = data.credential_scope
    if data.priority is not None:
        row.priority = data.priority
    if data.is_active is not None:
        row.is_active = data.is_active
    write_audit(db, action="llm.routing.update", organization_id=organization_id, user_id=user_id, detail=row.name)
    db.commit()
    return next((p for p in list_routing_policies(db, organization_id) if p["id"] == policy_id), None)
