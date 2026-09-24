"""Migración 1600 — Motor Económico EIAAX (capa unificada sobre FinOps)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1600a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1412a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "economic_cost_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("cost_class", sa.String(30), nullable=False, server_default="DIRECTO"),
        sa.Column("amount_kind", sa.String(20), nullable=False, server_default="REAL"),
        sa.Column("cost_source", sa.String(40), nullable=False, server_default="OTRO"),
        sa.Column("scope_type", sa.String(30), nullable=False, server_default="ORGANIZACION"),
        sa.Column("scope_id", sa.String(36), nullable=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), nullable=True),
        sa.Column("evaluacion_id", sa.String(36), nullable=True),
        sa.Column("finops_record_id", sa.String(36), sa.ForeignKey("finops_records.id"), nullable=True),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("provider", sa.String(80), nullable=True),
        sa.Column("model_name", sa.String(120), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_economic_cost_org", "economic_cost_entries", ["organization_id"])
    op.create_index("ix_economic_cost_scope", "economic_cost_entries", ["scope_id"])
    op.create_index("ix_economic_cost_finops", "economic_cost_entries", ["finops_record_id"])

    op.create_table(
        "economic_value_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("value_type", sa.String(60), nullable=False),
        sa.Column("value_nature", sa.String(20), nullable=False, server_default="ESTIMADO"),
        sa.Column("scope_type", sa.String(30), nullable=False, server_default="ORGANIZACION"),
        sa.Column("scope_id", sa.String(36), nullable=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), nullable=True),
        sa.Column("evaluacion_id", sa.String(36), nullable=True),
        sa.Column("finops_value_id", sa.String(36), sa.ForeignKey("finops_values.id"), nullable=True),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_economic_value_org", "economic_value_entries", ["organization_id"])
    op.create_index("ix_economic_value_nature", "economic_value_entries", ["value_nature"])

    op.create_table(
        "economic_private_economy",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("period_label", sa.String(40), nullable=False, server_default="MENSUAL"),
        sa.Column("estimated_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("real_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("time_hours", sa.Numeric(12, 2), nullable=True),
        sa.Column("resources_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("ia_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("infra_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("services_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("support_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("client_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("suggested_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("margin", sa.Numeric(18, 4), nullable=True),
        sa.Column("roi", sa.Numeric(10, 4), nullable=True),
        sa.Column("payback_months", sa.Numeric(10, 2), nullable=True),
        sa.Column("commercial_risk_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_economic_private_org", "economic_private_economy", ["organization_id"])

    op.create_table(
        "economic_price_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("scope_type", sa.String(30), nullable=False, server_default="ORGANIZACION"),
        sa.Column("scope_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("recommended_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("margin_estimate", sa.Numeric(18, 4), nullable=True),
        sa.Column("factors_json", sa.Text(), nullable=True),
        sa.Column("rationale_text", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_economic_price_rec_org", "economic_price_recommendations", ["organization_id"])


def downgrade() -> None:
    op.drop_table("economic_price_recommendations")
    op.drop_table("economic_private_economy")
    op.drop_table("economic_value_entries")
    op.drop_table("economic_cost_entries")
