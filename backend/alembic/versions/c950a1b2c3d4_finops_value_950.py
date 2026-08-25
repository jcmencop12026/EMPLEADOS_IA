"""FINOPS-950 costos y valor

Revision ID: c950a1b2c3d4
Revises: 5b2eb2437398
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c950a1b2c3d4"
down_revision: Union[str, None] = "5b2eb2437398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("finops_records") as batch_op:
        batch_op.add_column(sa.Column("employee_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("execution_ref", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("currency", sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column("quantity", sa.Numeric(18, 6), nullable=True))
        batch_op.add_column(sa.Column("unit", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("rate_source", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("rate_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_finops_records_employee", "ai_employees", ["employee_id"], ["id"])

    op.create_index("ix_finops_records_org_created", "finops_records", ["organization_id", "created_at"])

    op.create_table(
        "finops_rates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model_service", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("price_input", sa.Numeric(18, 8), nullable=True),
        sa.Column("price_output", sa.Numeric(18, 8), nullable=True),
        sa.Column("unit_price", sa.Numeric(18, 8), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finops_rates_org", "finops_rates", ["organization_id"])

    op.create_table(
        "finops_values",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=True),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("value_type", sa.String(length=40), nullable=False),
        sa.Column("certainty", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["ai_employees.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["employee_tasks.id"]),
        sa.ForeignKeyConstraint(["work_plan_id"], ["work_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finops_values_org", "finops_values", ["organization_id"])

    op.create_table(
        "finops_budgets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_limit", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("policy", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finops_budgets_org", "finops_budgets", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_finops_budgets_org", table_name="finops_budgets")
    op.drop_table("finops_budgets")
    op.drop_index("ix_finops_values_org", table_name="finops_values")
    op.drop_table("finops_values")
    op.drop_index("ix_finops_rates_org", table_name="finops_rates")
    op.drop_table("finops_rates")
    op.drop_index("ix_finops_records_org_created", table_name="finops_records")
    with op.batch_alter_table("finops_records") as batch_op:
        batch_op.drop_constraint("fk_finops_records_employee", type_="foreignkey")
        batch_op.drop_column("rate_id")
        batch_op.drop_column("rate_source")
        batch_op.drop_column("unit")
        batch_op.drop_column("quantity")
        batch_op.drop_column("currency")
        batch_op.drop_column("category")
        batch_op.drop_column("execution_ref")
        batch_op.drop_column("employee_id")
