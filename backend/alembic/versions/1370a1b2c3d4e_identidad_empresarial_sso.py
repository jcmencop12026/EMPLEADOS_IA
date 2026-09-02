"""Migración 1370 — Identidad empresarial, SSO, OIDC y SAML."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1370a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1300a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_identity_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("auth_mode", sa.String(20), nullable=False, server_default="SOLO_LOCAL"),
        sa.Column("mfa_sso_mode", sa.String(20), nullable=False, server_default="EAIOS"),
        sa.Column("auto_provision_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("default_role_on_provision", sa.String(40), nullable=False, server_default="viewer"),
        sa.Column("allowed_domains_json", sa.Text(), nullable=True),
        sa.Column("org_discovery_code", sa.String(40), nullable=True),
        sa.Column("attribute_mapping_json", sa.Text(), nullable=True),
        sa.Column("break_glass_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("break_glass_secret_ref", sa.String(200), nullable=True),
        sa.Column("scim_prepared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_org_identity_discovery", "organization_identity_settings", ["org_discovery_code"])

    op.create_table(
        "identity_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("provider_type", sa.String(10), nullable=False),
        sa.Column("vendor_hint", sa.String(80), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("secret_ref", sa.String(200), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("saml_cert_fingerprint", sa.String(128), nullable=True),
        sa.Column("saml_cert_not_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_result", sa.String(20), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_idp_org_code"),
    )
    op.create_index("ix_identity_providers_org", "identity_providers", ["organization_id"])
    op.create_index("ix_identity_providers_status", "identity_providers", ["status"])

    op.create_table(
        "user_external_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("identity_providers.id"), nullable=False),
        sa.Column("external_subject", sa.String(255), nullable=False),
        sa.Column("external_email", sa.String(200), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider_id", "external_subject", name="uq_external_identity_subject"),
    )

    op.create_table(
        "identity_group_role_mappings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("identity_providers.id"), nullable=False),
        sa.Column("external_group", sa.String(200), nullable=False),
        sa.Column("role_code", sa.String(40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "provider_id", "external_group", name="uq_group_role_map"),
    )

    op.create_table(
        "sso_auth_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("identity_providers.id"), nullable=False),
        sa.Column("state", sa.String(120), nullable=False, unique=True),
        sa.Column("nonce", sa.String(120), nullable=True),
        sa.Column("pkce_verifier", sa.String(128), nullable=True),
        sa.Column("redirect_after", sa.String(300), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "identity_login_audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("identity_providers.id"), nullable=True),
        sa.Column("login_method", sa.String(20), nullable=False),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("detail", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_identity_login_audits_org", "identity_login_audits", ["organization_id"])
    op.create_index("ix_identity_login_audits_created", "identity_login_audits", ["created_at"])

    op.add_column("user_sessions", sa.Column("auth_method", sa.String(20), nullable=True))
    op.add_column("user_sessions", sa.Column("identity_provider_id", sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_column("user_sessions", "identity_provider_id")
    op.drop_column("user_sessions", "auth_method")
    op.drop_table("identity_login_audits")
    op.drop_table("sso_auth_states")
    op.drop_table("identity_group_role_mappings")
    op.drop_table("user_external_identities")
    op.drop_table("identity_providers")
    op.drop_index("ix_org_identity_discovery", table_name="organization_identity_settings")
    op.drop_table("organization_identity_settings")
