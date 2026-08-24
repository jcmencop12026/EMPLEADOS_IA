"""notification idempotency keys — CODEX-820 v3

Revision ID: 820a2
Revises: 820a1
"""
from alembic import op
import sqlalchemy as sa

revision = "820a2"
down_revision = "820a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("event_id", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("rule_id", sa.String(36), nullable=True))
        batch_op.add_column(sa.Column("idempotency_key", sa.String(255), nullable=True))
        batch_op.create_foreign_key(
            "fk_notifications_rule_id",
            "alert_rules",
            ["rule_id"],
            ["id"],
        )
    op.create_index("ix_notifications_event_id", "notifications", ["event_id"])
    op.create_index("ix_notifications_rule_id", "notifications", ["rule_id"])
    op.create_index("ix_notifications_idempotency_key", "notifications", ["idempotency_key"])
    op.create_index(
        "uq_notifications_idempotency",
        "notifications",
        ["organization_id", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_notifications_idempotency", table_name="notifications")
    op.drop_index("ix_notifications_idempotency_key", table_name="notifications")
    op.drop_index("ix_notifications_rule_id", table_name="notifications")
    op.drop_index("ix_notifications_event_id", table_name="notifications")
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_constraint("fk_notifications_rule_id", type_="foreignkey")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("rule_id")
        batch_op.drop_column("event_id")
