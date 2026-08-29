"""FinOps trazabilidad 1110 — opportunity_id, alertas presupuesto."""

from alembic import op
import sqlalchemy as sa

revision = "1110a1b2c3d4e"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "finops_records",
        sa.Column("opportunity_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_finops_records_opportunity_id", "finops_records", ["opportunity_id"])
    op.create_foreign_key(
        "fk_finops_records_opportunity_id",
        "finops_records",
        "opportunities",
        ["opportunity_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "finops_budgets",
        sa.Column("alert_threshold_pct", sa.Integer(), nullable=False, server_default="90"),
    )

    op.create_table(
        "finops_budget_alert_states",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("budget_id", sa.String(length=36), sa.ForeignKey("finops_budgets.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("state_alerted", sa.String(length=30), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alerted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "budget_id",
            "state_alerted",
            "period_start",
            name="uq_finops_budget_alert_period_state",
        ),
    )
    op.create_index(
        "ix_finops_budget_alert_budget",
        "finops_budget_alert_states",
        ["budget_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_finops_budget_alert_budget", table_name="finops_budget_alert_states")
    op.drop_table("finops_budget_alert_states")
    op.drop_column("finops_budgets", "alert_threshold_pct")
    op.drop_constraint("fk_finops_records_opportunity_id", "finops_records", type_="foreignkey")
    op.drop_index("ix_finops_records_opportunity_id", table_name="finops_records")
    op.drop_column("finops_records", "opportunity_id")
