"""Motor de enrutamiento IA explicable — Bloque 1270."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.gateway.providers import is_executable_llm_provider, normalize_provider_type
from app.gateway.secrets import resolve_secret, secret_configured
from app.llm_models import LlmModelCatalog, LlmProviderConfig, LlmRoutingPolicy


@dataclass
class RoutingDecision:
    config: LlmProviderConfig
    model: str
    policy_id: str | None
    rationale: list[str]


def _parse_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def get_active_policy(db: Session, organization_id: str) -> LlmRoutingPolicy | None:
    return (
        db.query(LlmRoutingPolicy)
        .filter(LlmRoutingPolicy.organization_id == organization_id, LlmRoutingPolicy.is_active.is_(True))
        .order_by(LlmRoutingPolicy.priority.asc())
        .first()
    )


def _model_supports_capability(db: Session, organization_id: str, provider_type: str, model: str, capability: str | None) -> bool:
    if not capability:
        return True
    row = (
        db.query(LlmModelCatalog)
        .filter(
            LlmModelCatalog.organization_id == organization_id,
            LlmModelCatalog.provider_type == provider_type,
            LlmModelCatalog.model_id == model,
            LlmModelCatalog.is_enabled.is_(True),
        )
        .first()
    )
    if not row:
        return True
    caps = _parse_json(row.capabilities_json)
    return bool(caps.get(capability, True))


def _provider_is_usable(config: LlmProviderConfig) -> bool:
    if not config.is_enabled:
        return False
    if not is_executable_llm_provider(config.provider_type):
        return False
    return secret_configured(config.secret_ref) or config.provider_type == "ollama"


def list_candidate_providers(db: Session, organization_id: str, *, enabled_only: bool = True) -> list[LlmProviderConfig]:
    query = db.query(LlmProviderConfig).filter(LlmProviderConfig.organization_id == organization_id)
    if enabled_only:
        query = query.filter(LlmProviderConfig.is_enabled.is_(True))
    rows = query.order_by(LlmProviderConfig.priority.asc(), LlmProviderConfig.name.asc()).all()
    return [r for r in rows if is_executable_llm_provider(r.provider_type)]


def select_routed_provider(
    db: Session,
    organization_id: str,
    *,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
    required_capability: str | None = None,
    allow_fallback: bool = True,
    require_explicit: bool = False,
) -> RoutingDecision | None:
    policy = get_active_policy(db, organization_id)
    rationale: list[str] = []
    capability = required_capability or (policy.required_capability if policy else None)
    pref_provider = preferred_provider or (policy.preferred_provider if policy else None)
    pref_model = preferred_model or (policy.preferred_model if policy else None)
    fallback_ok = allow_fallback if policy is None else policy.fallback_allowed and allow_fallback

    candidates = list_candidate_providers(db, organization_id, enabled_only=True)
    if not candidates:
        return None

    if pref_provider:
        normalized = normalize_provider_type(pref_provider)
        rationale.append(f"Proveedor preferido solicitado: {normalized}")
        match = next((c for c in candidates if c.provider_type == normalized and not c.is_fallback), None)
        if match and _provider_is_usable(match):
            model = pref_model or match.model_default or _default_model(match.provider_type)
            if _model_supports_capability(db, organization_id, match.provider_type, model, capability):
                rationale.append("Seleccionado por preferencia explícita/política.")
                return RoutingDecision(config=match, model=model, policy_id=policy.id if policy else None, rationale=rationale)
        if require_explicit:
            return None
        rationale.append("Proveedor preferido no disponible o no configurado.")

    usable = [c for c in candidates if _provider_is_usable(c)]
    primary = next((c for c in usable if not c.is_fallback), None)
    if primary:
        model = pref_model or primary.model_default or _default_model(primary.provider_type)
        if _model_supports_capability(db, organization_id, primary.provider_type, model, capability):
            rationale.append("Seleccionado por prioridad del catálogo de proveedores.")
            return RoutingDecision(config=primary, model=model, policy_id=policy.id if policy else None, rationale=rationale)

    if fallback_ok:
        fallback = next((c for c in usable if c.is_fallback), None) or (usable[0] if usable else None)
        if fallback:
            model = pref_model or fallback.model_default or _default_model(fallback.provider_type)
            rationale.append("Fallback permitido — usando proveedor alternativo.")
            return RoutingDecision(config=fallback, model=model, policy_id=policy.id if policy else None, rationale=rationale)

    return None


def _default_model(provider_type: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "ollama": "llama3.2",
        "anthropic": "claude-3-haiku-20240307",
        "gemini": "gemini-1.5-flash",
        "azure-openai": "gpt-4o-mini",
    }
    return defaults.get(provider_type, "default")


def explain_routing(
    db: Session,
    organization_id: str,
    *,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
) -> dict[str, Any]:
    decision = select_routed_provider(
        db,
        organization_id,
        preferred_provider=preferred_provider,
        preferred_model=preferred_model,
    )
    if not decision:
        return {"seleccionado": None, "razones": ["No hay proveedores configurados y disponibles."]}
    return {
        "seleccionado": {
            "provider_id": decision.config.id,
            "provider_type": decision.config.provider_type,
            "model": decision.model,
            "policy_id": decision.policy_id,
        },
        "razones": decision.rationale,
    }
