"""Migración MB-07 — Planificador consumo y capacidad IA."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1507a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "14b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consumption_planner_org_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("credential_mode", sa.String(30), nullable=False, server_default="IA_ADMINISTRADA"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("included_consumption_usd", sa.Numeric(18, 4), nullable=True),
        sa.Column("client_price_monthly", sa.Numeric(18, 4), nullable=True),
        sa.Column("capacity_total_units", sa.Numeric(18, 4), nullable=True),
        sa.Column("max_concurrency", sa.Integer(), nullable=True),
        sa.Column("executions_per_employee_per_day", sa.Numeric(10, 2), nullable=False, server_default="5"),
        sa.Column("tokens_in_avg", sa.Integer(), nullable=False, server_default="1500"),
        sa.Column("tokens_out_avg", sa.Integer(), nullable=False, server_default="800"),
        sa.Column("model_distribution_json", sa.Text(), nullable=True),
        sa.Column("alert_thresholds_json", sa.Text(), nullable=True),
        sa.Column("plan_label", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", name="uq_consumption_planner_org_config"),
    )
    op.create_index("ix_consumption_planner_org_configs_org", "consumption_planner_org_configs", ["organization_id"])

    op.create_table(
        "consumption_planner_transversal",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("capability_code", sa.String(60), nullable=False),
        sa.Column("consumption_class", sa.String(30), nullable=False, server_default="TRANSVERSAL_ATRIBUIBLE"),
        sa.Column("activation_type", sa.String(30), nullable=False, server_default="PERIODICO"),
        sa.Column("is_deterministic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("executions_per_period", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("period_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("tokens_in_avg", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out_avg", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(80), nullable=True),
        sa.Column("model_name", sa.String(120), nullable=True),
        sa.Column("tools_cost_estimated", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("infra_cost_estimated", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consumption_planner_transversal_org", "consumption_planner_transversal", ["organization_id"])

    op.create_table(
        "consumption_planner_simulations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("params_json", sa.Text(), nullable=False),
        sa.Column("results_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consumption_planner_simulations_org", "consumption_planner_simulations", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_consumption_planner_simulations_org", table_name="consumption_planner_simulations")
    op.drop_table("consumption_planner_simulations")
    op.drop_index("ix_consumption_planner_transversal_org", table_name="consumption_planner_transversal")
    op.drop_table("consumption_planner_transversal")
    op.drop_index("ix_consumption_planner_org_configs_org", table_name="consumption_planner_org_configs")
    op.drop_table("consumption_planner_org_configs")
