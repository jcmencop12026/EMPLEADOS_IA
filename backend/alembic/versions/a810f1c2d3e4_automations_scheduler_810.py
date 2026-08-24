"""automations_scheduler_810

Revision ID: a810f1c2d3e4
Revises: 5b2eb2437398
Create Date: 2026-08-24 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a810f1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "5b2eb2437398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("trigger_type", sa.String(length=30), nullable=False),
        sa.Column("schedule_type", sa.String(length=30), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_config_json", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=True),
        sa.Column("workflow_config_json", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("max_cost_per_run", sa.Float(), nullable=True),
        sa.Column("max_runs_per_day", sa.Integer(), nullable=True),
        sa.Column("missed_run_policy", sa.String(length=30), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["ai_employees.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_automations_organization_id"), "automations", ["organization_id"], unique=False)
    op.create_index(op.f("ix_automations_status"), "automations", ["status"], unique=False)
    op.create_index(op.f("ix_automations_next_run_at"), "automations", ["next_run_at"], unique=False)

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("automation_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("occurrence_key", sa.String(length=64), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("result_reference_json", sa.Text(), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("cost_reference", sa.Float(), nullable=True),
        sa.Column("trigger_source", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["automation_id"], ["automations.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["work_plan_id"], ["work_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("automation_id", "occurrence_key", name="uq_automation_occurrence"),
    )
    op.create_index(op.f("ix_automation_runs_automation_id"), "automation_runs", ["automation_id"], unique=False)
    op.create_index(op.f("ix_automation_runs_organization_id"), "automation_runs", ["organization_id"], unique=False)
    op.create_index(op.f("ix_automation_runs_scheduled_for"), "automation_runs", ["scheduled_for"], unique=False)
    op.create_index(op.f("ix_automation_runs_status"), "automation_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("automation_runs")
    op.drop_table("automations")
