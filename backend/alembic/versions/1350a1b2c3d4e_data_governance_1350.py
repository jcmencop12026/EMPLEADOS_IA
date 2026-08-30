"""Migración 1350 — Gobierno de datos, privacidad y retención."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1350a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1250f1a2b3c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gov_classification_levels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("sensitivity_rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_gov_class_org_code"),
    )
    op.create_index("ix_gov_class_org", "gov_classification_levels", ["organization_id"])

    op.create_table(
        "gov_data_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_gov_cat_org_code"),
    )
    op.create_index("ix_gov_cat_org", "gov_data_categories", ["organization_id"])

    op.create_table(
        "gov_retention_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("scope_type", sa.String(40), nullable=False, server_default="ORGANIZACION"),
        sa.Column("scope_ref", sa.String(120), nullable=True),
        sa.Column("duration_unit", sa.String(20), nullable=False, server_default="MESES"),
        sa.Column("duration_value", sa.Integer(), nullable=True),
        sa.Column("disposition", sa.String(40), nullable=False, server_default="REVISIÓN_MANUAL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_retention_org", "gov_retention_policies", ["organization_id"])

    op.create_table(
        "gov_purposes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_gov_purpose_org_code"),
    )
    op.create_index("ix_gov_purpose_org", "gov_purposes", ["organization_id"])

    op.create_table(
        "gov_catalog_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("origin_system", sa.String(160), nullable=True),
        sa.Column("responsible_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("functional_owner", sa.String(160), nullable=True),
        sa.Column("classification_level_id", sa.String(36), sa.ForeignKey("gov_classification_levels.id"), nullable=True),
        sa.Column("categories_json", sa.Text(), nullable=True),
        sa.Column("logical_location", sa.String(240), nullable=True),
        sa.Column("format", sa.String(80), nullable=True),
        sa.Column("retention_policy_id", sa.String(36), sa.ForeignKey("gov_retention_policies.id"), nullable=True),
        sa.Column("authorized_use", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVO"),
        sa.Column("data_environment", sa.String(20), nullable=False, server_default="PRODUCCION"),
        sa.Column("secret_status", sa.String(20), nullable=True),
        sa.Column("purpose_id", sa.String(36), sa.ForeignKey("gov_purposes.id"), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_catalog_org", "gov_catalog_entries", ["organization_id"])
    op.create_index("ix_gov_catalog_status", "gov_catalog_entries", ["status"])

    op.create_table(
        "gov_lineage_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=False),
        sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("label", sa.String(240), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("related_process_id", sa.String(36), nullable=True),
        sa.Column("related_employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("parent_event_id", sa.String(36), sa.ForeignKey("gov_lineage_events.id"), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_lineage_org", "gov_lineage_events", ["organization_id"])
    op.create_index("ix_gov_lineage_catalog", "gov_lineage_events", ["catalog_entry_id"])

    op.create_table(
        "gov_ai_usage_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_ref", sa.String(120), nullable=False),
        sa.Column("permission", sa.String(40), nullable=False),
        sa.Column("purpose_id", sa.String(36), sa.ForeignKey("gov_purposes.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_ai_usage_org", "gov_ai_usage_grants", ["organization_id"])

    op.create_table(
        "gov_provider_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("classification_level_id", sa.String(36), sa.ForeignKey("gov_classification_levels.id"), nullable=True),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("gov_data_categories.id"), nullable=True),
        sa.Column("decision", sa.String(40), nullable=False),
        sa.Column("minimization_action", sa.String(40), nullable=True),
        sa.Column("provider_scope", sa.String(120), nullable=True),
        sa.Column("is_mandatory_global", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_provider_pol_org", "gov_provider_policies", ["organization_id"])

    op.create_table(
        "gov_legal_holds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("scope_ref", sa.String(120), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("hold_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gov_legal_hold_org", "gov_legal_holds", ["organization_id"])
    op.create_index("ix_gov_legal_hold_status", "gov_legal_holds", ["status"])

    op.create_table(
        "gov_access_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("resource_ref", sa.String(200), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("result", sa.String(30), nullable=False, server_default="OK"),
        sa.Column("purpose_id", sa.String(36), sa.ForeignKey("gov_purposes.id"), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_access_org", "gov_access_logs", ["organization_id"])
    op.create_index("ix_gov_access_created", "gov_access_logs", ["created_at"])

    op.create_table(
        "gov_authorizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("auth_type", sa.String(60), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("source_ref", sa.String(200), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="VIGENTE"),
        sa.Column("evidence_ref", sa.String(240), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_auth_org", "gov_authorizations", ["organization_id"])

    op.create_table(
        "gov_subject_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("request_type", sa.String(40), nullable=False),
        sa.Column("subject_ref", sa.String(200), nullable=True),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="RECIBIDA"),
        sa.Column("requested_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_to_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gov_request_org", "gov_subject_requests", ["organization_id"])
    op.create_index("ix_gov_request_status", "gov_subject_requests", ["status"])

    op.create_table(
        "gov_export_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("format", sa.String(40), nullable=True),
        sa.Column("result", sa.String(30), nullable=False, server_default="OK"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_export_org", "gov_export_records", ["organization_id"])
    op.create_index("ix_gov_export_at", "gov_export_records", ["exported_at"])

    op.create_table(
        "gov_org_policy_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("policy_key", sa.String(80), nullable=False),
        sa.Column("policy_value_json", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "policy_key", name="uq_gov_org_policy_key"),
    )
    op.create_index("ix_gov_org_policy_org", "gov_org_policy_settings", ["organization_id"])

    op.create_table(
        "gov_global_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_key", sa.String(80), nullable=False),
        sa.Column("policy_value_json", sa.Text(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_restriction_level", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("policy_key", name="uq_gov_global_policy_key"),
    )

    op.create_table(
        "gov_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("finding_type", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ABIERTO"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_gov_finding_org", "gov_findings", ["organization_id"])
    op.create_index("ix_gov_finding_status", "gov_findings", ["status"])

    op.create_table(
        "gov_corrective_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("finding_id", sa.String(36), sa.ForeignKey("gov_findings.id"), nullable=False),
        sa.Column("responsible_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDIENTE"),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gov_action_org", "gov_corrective_actions", ["organization_id"])
    op.create_index("ix_gov_action_finding", "gov_corrective_actions", ["finding_id"])


def downgrade() -> None:
    op.drop_table("gov_corrective_actions")
    op.drop_table("gov_findings")
    op.drop_table("gov_global_policies")
    op.drop_table("gov_org_policy_settings")
    op.drop_table("gov_export_records")
    op.drop_table("gov_subject_requests")
    op.drop_table("gov_authorizations")
    op.drop_table("gov_access_logs")
    op.drop_table("gov_legal_holds")
    op.drop_table("gov_provider_policies")
    op.drop_table("gov_ai_usage_grants")
    op.drop_table("gov_lineage_events")
    op.drop_table("gov_catalog_entries")
    op.drop_table("gov_purposes")
    op.drop_table("gov_retention_policies")
    op.drop_table("gov_data_categories")
    op.drop_table("gov_classification_levels")
