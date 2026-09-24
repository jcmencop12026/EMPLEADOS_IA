"""Migración 1380 — Aprovisionamiento empresarial SCIM 2.0."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1380a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1370a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organization_identity_settings", sa.Column("scim_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "scim_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("token_prefix", sa.String(12), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scim_tokens_org", "scim_tokens", ["organization_id"])

    op.create_table(
        "scim_user_resources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("user_name", sa.String(120), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("emails_json", sa.Text(), nullable=True),
        sa.Column("provision_status", sa.String(20), nullable=False, server_default="PROVISIONADO"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_scim_user_org_external"),
        sa.UniqueConstraint("organization_id", "user_name", name="uq_scim_user_org_username"),
    )

    op.create_table(
        "scim_groups",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_scim_group_org_external"),
    )

    op.create_table(
        "scim_group_members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("group_id", sa.String(36), sa.ForeignKey("scim_groups.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("group_id", "user_id", name="uq_scim_group_member"),
    )

    op.create_table(
        "scim_group_role_mappings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("external_group", sa.String(200), nullable=False),
        sa.Column("role_code", sa.String(40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "external_group", name="uq_scim_group_role_map"),
    )

    op.create_table(
        "scim_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("token_id", sa.String(36), sa.ForeignKey("scim_tokens.id"), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("detail", sa.String(500), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "scim_conflicts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("conflict_type", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "scim_idempotency_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_scim_idempotency"),
    )

    op.create_table(
        "scim_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), unique=True, nullable=False),
        sa.Column("users_provisioned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("users_active", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("users_deactivated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflicts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rate_limited_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requests_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_latency_ms", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scim_metrics")
    op.drop_table("scim_idempotency_records")
    op.drop_table("scim_conflicts")
    op.drop_table("scim_audit_logs")
    op.drop_table("scim_group_role_mappings")
    op.drop_table("scim_group_members")
    op.drop_table("scim_groups")
    op.drop_table("scim_user_resources")
    op.drop_index("ix_scim_tokens_org", table_name="scim_tokens")
    op.drop_table("scim_tokens")
    op.drop_column("organization_identity_settings", "scim_enabled")
