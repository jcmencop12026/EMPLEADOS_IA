"""Modelos de gobierno de datos, privacidad y retención — BLOQUE 1350."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GovClassificationLevel(Base):
    __tablename__ = "gov_classification_levels"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_gov_class_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sensitivity_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovDataCategory(Base):
    __tablename__ = "gov_data_categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_gov_cat_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovRetentionPolicy(Base):
    __tablename__ = "gov_retention_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(40), nullable=False, default="ORGANIZACION")
    scope_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    duration_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="MESES")
    duration_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disposition: Mapped[str] = mapped_column(String(40), nullable=False, default="REVISIÓN_MANUAL")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovCatalogEntry(Base):
    __tablename__ = "gov_catalog_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    origin_system: Mapped[str | None] = mapped_column(String(160), nullable=True)
    responsible_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    functional_owner: Mapped[str | None] = mapped_column(String(160), nullable=True)
    classification_level_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_classification_levels.id"), nullable=True)
    categories_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    logical_location: Mapped[str | None] = mapped_column(String(240), nullable=True)
    format: Mapped[str | None] = mapped_column(String(80), nullable=True)
    retention_policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_retention_policies.id"), nullable=True)
    authorized_use: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVO", index=True)
    data_environment: Mapped[str] = mapped_column(String(20), nullable=False, default="PRODUCCION")
    secret_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    purpose_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_purposes.id"), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovPurpose(Base):
    __tablename__ = "gov_purposes"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_gov_purpose_org_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class GovLineageEvent(Base):
    __tablename__ = "gov_lineage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    catalog_entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=False, index=True)
    step_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(240), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_process_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    related_employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    parent_event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_lineage_events.id"), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class GovAiUsageGrant(Base):
    __tablename__ = "gov_ai_usage_grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    permission: Mapped[str] = mapped_column(String(40), nullable=False)
    purpose_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_purposes.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class GovProviderPolicy(Base):
    __tablename__ = "gov_provider_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    classification_level_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_classification_levels.id"), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_data_categories.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    minimization_action: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider_scope: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_mandatory_global: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovLegalHold(Base):
    __tablename__ = "gov_legal_holds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    scope_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO", index=True)
    hold_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GovAccessLog(Base):
    __tablename__ = "gov_access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    resource_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    result: Mapped[str] = mapped_column(String(30), nullable=False, default="OK")
    purpose_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_purposes.id"), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class GovAuthorization(Base):
    __tablename__ = "gov_authorizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    auth_type: Mapped[str] = mapped_column(String(60), nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="VIGENTE")
    evidence_ref: Mapped[str | None] = mapped_column(String(240), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovSubjectRequest(Base):
    __tablename__ = "gov_subject_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RECIBIDA", index=True)
    requested_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_to_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GovExportRecord(Base):
    __tablename__ = "gov_export_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str | None] = mapped_column(String(40), nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False, default="OK")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class GovOrgPolicySetting(Base):
    __tablename__ = "gov_org_policy_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", "policy_key", name="uq_gov_org_policy_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    policy_key: Mapped[str] = mapped_column(String(80), nullable=False)
    policy_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovGlobalPolicy(Base):
    __tablename__ = "gov_global_policies"
    __table_args__ = (
        UniqueConstraint("policy_key", name="uq_gov_global_policy_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    policy_key: Mapped[str] = mapped_column(String(80), nullable=False)
    policy_value_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    min_restriction_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class GovFinding(Base):
    __tablename__ = "gov_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    finding_type: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    catalog_entry_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("gov_catalog_entries.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ABIERTO", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class GovCorrectiveAction(Base):
    __tablename__ = "gov_corrective_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("gov_findings.id"), nullable=False, index=True)
    responsible_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
