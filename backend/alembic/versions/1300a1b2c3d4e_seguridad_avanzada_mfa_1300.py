"""Migración 1300 — Seguridad avanzada: MFA, sesiones, políticas y eventos."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1300a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1250a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_security_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("mfa_mode", sa.String(20), nullable=False, server_default="OPCIONAL"),
        sa.Column("mfa_required_roles_json", sa.Text(), nullable=True),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=False, server_default="720"),
        sa.Column("max_active_sessions", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("login_max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("lockout_minutes", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("revoke_sessions_on_password_change", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("excess_session_policy", sa.String(30), nullable=False, server_default="REVOCAR_MAS_ANTIGUA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_mfa_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("secret_encrypted", sa.Text(), nullable=True),
        sa.Column("pending_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_mfa_settings_org", "user_mfa_settings", ["organization_id"])

    op.create_table(
        "user_mfa_recovery_codes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_mfa_recovery_user", "user_mfa_recovery_codes", ["user_id"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoke_reason", sa.String(120), nullable=True),
        sa.Column("mfa_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_user_sessions_user", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_org", "user_sessions", ["organization_id"])

    op.create_table(
        "security_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_security_events_org", "security_events", ["organization_id"])
    op.create_index("ix_security_events_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_created", "security_events", ["created_at"])

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("identifier", sa.String(120), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_login_attempts_identifier", "login_attempts", ["identifier"])
    op.create_index("ix_login_attempts_ip", "login_attempts", ["ip_address"])
    op.create_index("ix_login_attempts_created", "login_attempts", ["created_at"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_reset_user", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_user", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_login_attempts_created", table_name="login_attempts")
    op.drop_index("ix_login_attempts_ip", table_name="login_attempts")
    op.drop_index("ix_login_attempts_identifier", table_name="login_attempts")
    op.drop_table("login_attempts")
    op.drop_index("ix_security_events_created", table_name="security_events")
    op.drop_index("ix_security_events_type", table_name="security_events")
    op.drop_index("ix_security_events_org", table_name="security_events")
    op.drop_table("security_events")
    op.drop_index("ix_user_sessions_org", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_user_mfa_recovery_user", table_name="user_mfa_recovery_codes")
    op.drop_table("user_mfa_recovery_codes")
    op.drop_index("ix_user_mfa_settings_org", table_name="user_mfa_settings")
    op.drop_table("user_mfa_settings")
    op.drop_table("organization_security_policies")
