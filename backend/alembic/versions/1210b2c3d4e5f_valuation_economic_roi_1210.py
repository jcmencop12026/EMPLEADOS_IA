"""Alembic — Valoración económica y ROI por oportunidad (1210)."""

from alembic import op
import sqlalchemy as sa

revision = "1210b2c3d4e5f"
down_revision = "1110a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunity_valuations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("value_type", sa.String(length=40), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="INTERNO"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="BORRADOR"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "opportunity_id", name="uq_valuation_org_opp"),
    )
    op.create_index("ix_opportunity_valuations_org", "opportunity_valuations", ["organization_id"])
    op.create_index("ix_opportunity_valuations_opp", "opportunity_valuations", ["opportunity_id"])

    op.create_table(
        "opportunity_valuation_expected",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("valuation_id", sa.String(length=36), sa.ForeignKey("opportunity_valuations.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("gross_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("probability", sa.Numeric(7, 6), nullable=True),
        sa.Column("execution_cost_expected", sa.Numeric(18, 4), nullable=True),
        sa.Column("period_days", sa.Integer(), nullable=True),
        sa.Column("adjusted_expected", sa.Numeric(18, 4), nullable=True),
        sa.Column("value_nature", sa.String(length=20), nullable=False, server_default="ESTIMADA"),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("valuation_id", name="uq_valuation_expected_valuation"),
    )

    op.create_table(
        "opportunity_valuation_scenarios",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("valuation_id", sa.String(length=36), sa.ForeignKey("opportunity_valuations.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("scenario_type", sa.String(length=20), nullable=False),
        sa.Column("value_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("probability", sa.Numeric(7, 6), nullable=True),
        sa.Column("cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("period_days", sa.Integer(), nullable=True),
        sa.Column("adjusted_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("valuation_id", "scenario_type", name="uq_valuation_scenario_type"),
    )

    op.create_table(
        "opportunity_valuation_real",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("valuation_id", sa.String(length=36), sa.ForeignKey("opportunity_valuations.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("materialized_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("attributable_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("value_nature", sa.String(length=20), nullable=False, server_default="ESTIMADO"),
        sa.Column("attribution_level", sa.String(length=30), nullable=False, server_default="NO ATRIBUIBLE"),
        sa.Column("attribution_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("responsible_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("external_measurement_ref", sa.String(length=200), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_valuation_real_valuation", "opportunity_valuation_real", ["valuation_id"])

    op.create_table(
        "opportunity_execution_costs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("valuation_id", sa.String(length=36), sa.ForeignKey("opportunity_valuations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("cost_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("finops_record_id", sa.String(length=36), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("recorded_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "opportunity_valuation_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("valuation_id", sa.String(length=36), sa.ForeignKey("opportunity_valuations.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_valuation_history_valuation", "opportunity_valuation_history", ["valuation_id"])


def downgrade() -> None:
    op.drop_index("ix_valuation_history_valuation", table_name="opportunity_valuation_history")
    op.drop_table("opportunity_valuation_history")
    op.drop_table("opportunity_execution_costs")
    op.drop_index("ix_valuation_real_valuation", table_name="opportunity_valuation_real")
    op.drop_table("opportunity_valuation_real")
    op.drop_table("opportunity_valuation_scenarios")
    op.drop_table("opportunity_valuation_expected")
    op.drop_index("ix_opportunity_valuations_opp", table_name="opportunity_valuations")
    op.drop_index("ix_opportunity_valuations_org", table_name="opportunity_valuations")
    op.drop_table("opportunity_valuations")
