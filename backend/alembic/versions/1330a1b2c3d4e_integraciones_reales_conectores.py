"""Alembic — Integraciones reales y conectores (1330)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1330a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1250f1a2b3c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integration_connectors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("connector_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("auth_type", sa.String(20), nullable=False, server_default="NINGUNA"),
        sa.Column("secret_ref", sa.String(200), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("mapping_json", sa.Text(), nullable=True),
        sa.Column("schema_json", sa.Text(), nullable=True),
        sa.Column("destination_type", sa.String(30), nullable=True),
        sa.Column("signal_source_code", sa.String(80), nullable=True),
        sa.Column("trigger_mode", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("retry_max", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_delay_ms", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="30000"),
        sa.Column("max_response_bytes", sa.Integer(), nullable=False, server_default="5242880"),
        sa.Column("circuit_breaker_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("circuit_breaker_cooldown_sec", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("circuit_open_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.String(500), nullable=True),
        sa.Column("last_latency_ms", sa.Integer(), nullable=True),
        sa.Column("webhook_token_hash", sa.String(64), nullable=True),
        sa.Column("allow_internal_urls", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_integration_connector_org_code"),
    )
    op.create_index("ix_integration_connectors_org", "integration_connectors", ["organization_id"])
    op.create_index("ix_integration_connectors_type", "integration_connectors", ["connector_type"])
    op.create_index("ix_integration_connectors_status", "integration_connectors", ["status"])

    op.create_table(
        "integration_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("connector_id", sa.String(36), sa.ForeignKey("integration_connectors.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("trigger_mode", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_valid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_category", sa.String(30), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("idempotency_key", sa.String(120), nullable=True),
        sa.Column("result_summary_json", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_integration_executions_connector", "integration_executions", ["connector_id"])
    op.create_index("ix_integration_executions_idem", "integration_executions", ["idempotency_key"])

    op.create_table(
        "integration_webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("connector_id", sa.String(36), sa.ForeignKey("integration_connectors.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dedupe_key", sa.String(120), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="RECIBIDO"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_webhook_dedupe"),
    )


def downgrade() -> None:
    op.drop_table("integration_webhook_events")
    op.drop_index("ix_integration_executions_idem", table_name="integration_executions")
    op.drop_index("ix_integration_executions_connector", table_name="integration_executions")
    op.drop_table("integration_executions")
    op.drop_index("ix_integration_connectors_status", table_name="integration_connectors")
    op.drop_index("ix_integration_connectors_type", table_name="integration_connectors")
    op.drop_index("ix_integration_connectors_org", table_name="integration_connectors")
    op.drop_table("integration_connectors")
