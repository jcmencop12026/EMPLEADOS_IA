"""notifications and alert rules v1

Revision ID: 820a1
Revises: 5b2eb2437398
"""
from alembic import op
import sqlalchemy as sa

revision = "820a1"
down_revision = "5b2eb2437398"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("type", sa.String(40), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(240), nullable=False), sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False), sa.Column("source_id", sa.String(80)),
        sa.Column("recipient_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("recipient_role", sa.String(40)), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)), sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("metadata_json", sa.Text()),
    )
    for column in ("organization_id", "type", "severity", "recipient_user_id", "recipient_role", "status", "created_at"):
        op.create_index(f"ix_notifications_{column}", "notifications", [column])
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("condition_json", sa.Text()), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("recipient_user_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("recipient_role", sa.String(40)), sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("organization_id", "event_type", "enabled"):
        op.create_index(f"ix_alert_rules_{column}", "alert_rules", [column])


def downgrade() -> None:
    op.drop_table("alert_rules")
    op.drop_table("notifications")
