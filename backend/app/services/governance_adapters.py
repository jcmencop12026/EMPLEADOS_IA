"""Adaptadores de preparación para convergencia 1270 y 1330 — BLOQUE 1350."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.services import governance_service as svc


@dataclass
class ProviderExportDecision:
    """Resultado para gateway IA (1270)."""

    result: str  # PERMITIDO | DENEGADO | PERMITIDO_CON_TRANSFORMACIÓN
    reasons: list[str] = field(default_factory=list)
    minimization_action: str | None = None
    policy_id: str | None = None


@dataclass
class ConnectorPolicyView:
    """Vista de política para conectores externos (1330)."""

    classification_code: str | None
    classification_name: str | None
    provider_decision: str | None
    retention_policy_id: str | None
    retention_disposition: str | None
    purpose_code: str | None
    restrictions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GovernanceProviderAdapter:
    """Interfaz para que el gateway LLM (1270) consulte salida a proveedores."""

    def __init__(self, db: Session):
        self.db = db

    def can_send_to_provider(
        self,
        organization_id: str,
        *,
        catalog_entry_id: str | None = None,
        classification_level_id: str | None = None,
        category_id: str | None = None,
        provider: str | None = None,
    ) -> ProviderExportDecision:
        raw = svc.evaluate_provider_export(
            self.db,
            organization_id,
            catalog_entry_id=catalog_entry_id,
            classification_level_id=classification_level_id,
            category_id=category_id,
            provider=provider,
        )
        return ProviderExportDecision(
            result=raw["result"],
            reasons=raw.get("reasons", []),
            minimization_action=raw.get("minimization_action"),
            policy_id=raw.get("policy_id"),
        )


class GovernanceConnectorAdapter:
    """Interfaz para que conectores externos (1330) consulten políticas."""

    def __init__(self, db: Session):
        self.db = db

    def get_resource_policy(
        self,
        organization_id: str,
        catalog_entry_id: str,
    ) -> ConnectorPolicyView | None:
        raw = svc.get_connector_policy_view(self.db, organization_id, catalog_entry_id)
        if raw is None:
            return None
        return ConnectorPolicyView(
            classification_code=raw.get("classification_code"),
            classification_name=raw.get("classification_name"),
            provider_decision=raw.get("provider_decision"),
            retention_policy_id=raw.get("retention_policy_id"),
            retention_disposition=raw.get("retention_disposition"),
            purpose_code=raw.get("purpose_code"),
            restrictions=raw.get("restrictions", []),
            metadata=raw.get("metadata", {}),
        )
