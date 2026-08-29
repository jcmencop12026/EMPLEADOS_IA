"""Esquemas Pydantic — gobierno de datos BLOQUE 1350."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas_semantic import SemanticMetaFields


class ClassificationLevelOut(BaseModel):
    id: str
    organization_id: str | None = None
    code: str
    name: str
    sensitivity_rank: int
    description: str | None = None
    is_active: bool = True
    is_system: bool = False


class ClassificationLevelIn(BaseModel):
    code: str
    name: str
    sensitivity_rank: int = 0
    description: str | None = None


class DataCategoryOut(BaseModel):
    id: str
    organization_id: str | None = None
    code: str
    name: str
    description: str | None = None
    is_active: bool = True
    is_system: bool = False


class DataCategoryIn(BaseModel):
    code: str
    name: str
    description: str | None = None


class PurposeOut(BaseModel):
    id: str
    organization_id: str
    code: str
    name: str
    is_active: bool = True


class CatalogEntryOut(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None = None
    source: str | None = None
    origin_system: str | None = None
    responsible_user_id: str | None = None
    functional_owner: str | None = None
    classification_level_id: str | None = None
    classification_code: str | None = None
    classification_name: str | None = None
    categories: list[Any] = Field(default_factory=list)
    logical_location: str | None = None
    format: str | None = None
    retention_policy_id: str | None = None
    authorized_use: str | None = None
    status: str
    data_environment: str
    secret_status: str | None = None
    purpose_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CatalogEntryIn(BaseModel):
    name: str
    description: str | None = None
    source: str | None = None
    origin_system: str | None = None
    responsible_user_id: str | None = None
    functional_owner: str | None = None
    classification_level_id: str | None = None
    categories: list[Any] = Field(default_factory=list)
    logical_location: str | None = None
    format: str | None = None
    retention_policy_id: str | None = None
    authorized_use: str | None = None
    status: str = "ACTIVO"
    data_environment: str = "PRODUCCION"
    secret_status: str | None = None
    purpose_id: str | None = None
    metadata: dict[str, Any] | None = None


class CatalogEntryPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    source: str | None = None
    origin_system: str | None = None
    responsible_user_id: str | None = None
    functional_owner: str | None = None
    classification_level_id: str | None = None
    categories: list[Any] | None = None
    logical_location: str | None = None
    format: str | None = None
    retention_policy_id: str | None = None
    authorized_use: str | None = None
    status: str | None = None
    data_environment: str | None = None
    secret_status: str | None = None
    purpose_id: str | None = None
    metadata: dict[str, Any] | None = None


class RetentionPolicyOut(BaseModel):
    id: str
    organization_id: str
    name: str
    scope_type: str
    scope_ref: str | None = None
    duration_unit: str
    duration_value: int | None = None
    disposition: str
    is_active: bool = True


class RetentionPolicyIn(BaseModel):
    name: str
    scope_type: str = "ORGANIZACION"
    scope_ref: str | None = None
    duration_unit: str = "MESES"
    duration_value: int | None = None
    disposition: str = "REVISIÓN_MANUAL"


class LineageEventIn(BaseModel):
    catalog_entry_id: str
    step_type: str
    label: str
    detail: str | None = None
    related_process_id: str | None = None
    related_employee_id: str | None = None
    parent_event_id: str | None = None
    metadata: dict[str, Any] | None = None


class LineageEventOut(BaseModel):
    id: str
    catalog_entry_id: str
    step_type: str
    label: str
    detail: str | None = None
    related_process_id: str | None = None
    related_employee_id: str | None = None
    parent_event_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime | None = None


class AiUsageGrantIn(BaseModel):
    target_type: str
    target_id: str
    source_type: str
    source_ref: str
    permission: str
    purpose_id: str | None = None


class AiUsageGrantOut(BaseModel):
    id: str
    target_type: str
    target_id: str
    source_type: str
    source_ref: str
    permission: str
    purpose_id: str | None = None
    is_active: bool = True


class ProviderPolicyIn(BaseModel):
    classification_level_id: str | None = None
    category_id: str | None = None
    decision: str
    minimization_action: str | None = None
    provider_scope: str | None = None
    is_mandatory_global: bool = False
    metadata: dict[str, Any] | None = None


class ProviderPolicyOut(BaseModel):
    id: str
    organization_id: str | None = None
    classification_level_id: str | None = None
    category_id: str | None = None
    decision: str
    minimization_action: str | None = None
    provider_scope: str | None = None
    is_mandatory_global: bool = False
    metadata: dict[str, Any] | None = None


class ProviderExportEvalIn(BaseModel):
    catalog_entry_id: str | None = None
    classification_level_id: str | None = None
    category_id: str | None = None
    provider: str | None = None


class ProviderExportEvalOut(SemanticMetaFields):
    result: str
    reasons: list[str] = Field(default_factory=list)
    minimization_action: str | None = None
    policy_id: str | None = None


class AccessLogOut(BaseModel):
    id: str
    user_id: str | None = None
    catalog_entry_id: str | None = None
    resource_ref: str | None = None
    action: str
    result: str
    purpose_id: str | None = None
    detail: str | None = None
    created_at: datetime | None = None


class AccessLogIn(BaseModel):
    catalog_entry_id: str | None = None
    resource_ref: str | None = None
    action: str
    result: str = "OK"
    purpose_id: str | None = None
    detail: str | None = None


class AuthorizationIn(BaseModel):
    auth_type: str
    purpose: str | None = None
    source_ref: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: str = "VIGENTE"
    evidence_ref: str | None = None
    metadata: dict[str, Any] | None = None


class AuthorizationOut(BaseModel):
    id: str
    auth_type: str
    purpose: str | None = None
    source_ref: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: str
    evidence_ref: str | None = None
    metadata: dict[str, Any] | None = None


class SubjectRequestIn(BaseModel):
    request_type: str
    subject_ref: str | None = None
    catalog_entry_id: str | None = None


class SubjectRequestPatch(BaseModel):
    status: str | None = None
    assigned_to_id: str | None = None
    resolution_note: str | None = None


class SubjectRequestOut(BaseModel):
    id: str
    request_type: str
    subject_ref: str | None = None
    catalog_entry_id: str | None = None
    status: str
    requested_by_id: str | None = None
    assigned_to_id: str | None = None
    resolution_note: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class ExportRecordIn(BaseModel):
    catalog_entry_id: str | None = None
    reason: str | None = None
    format: str | None = None
    result: str = "OK"
    metadata: dict[str, Any] | None = None


class ExportRecordOut(BaseModel):
    id: str
    user_id: str | None = None
    catalog_entry_id: str | None = None
    reason: str | None = None
    format: str | None = None
    result: str
    metadata: dict[str, Any] | None = None
    exported_at: datetime | None = None


class LegalHoldIn(BaseModel):
    catalog_entry_id: str | None = None
    scope_ref: str | None = None
    reason: str
    hold_until: datetime | None = None


class LegalHoldOut(BaseModel):
    id: str
    catalog_entry_id: str | None = None
    scope_ref: str | None = None
    reason: str
    status: str
    hold_until: datetime | None = None
    created_by_id: str | None = None
    created_at: datetime | None = None
    released_at: datetime | None = None


class OrgPolicyIn(BaseModel):
    policy_key: str
    policy_value: Any = None


class GlobalPolicyIn(BaseModel):
    policy_key: str
    policy_value: Any = None
    is_mandatory: bool = True


class FindingOut(SemanticMetaFields):
    id: str
    finding_type: str
    severity: str
    catalog_entry_id: str | None = None
    description: str
    status: str
    detected_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class CorrectiveActionIn(BaseModel):
    finding_id: str
    responsible_user_id: str | None = None
    target_date: datetime | None = None
    status: str = "PENDIENTE"


class CorrectiveActionOut(SemanticMetaFields):
    id: str
    finding_id: str
    responsible_user_id: str | None = None
    target_date: datetime | None = None
    status: str
    outcome: str | None = None


class RiskOut(SemanticMetaFields):
    catalog_entry_id: str
    risk_level: str
    score: int
    factors: list[str] = Field(default_factory=list)


class MaskIn(BaseModel):
    field_type: str
    value: str


class MaskOut(BaseModel):
    original_length: str
    masked: str


class DashboardOut(SemanticMetaFields):
    fuentes_catalogadas: int
    sin_clasificar: int
    riesgo_alto: int
    retencion_vencida: int
    exportaciones: int
    solicitudes_abiertas: int
    hallazgos_abiertos: int
    acciones_pendientes: int
    contrato_semantico: dict | None = None
    riesgo_alto_semantico: dict | None = None
