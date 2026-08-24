"""capabilities_tools_knowledge_850

Revision ID: a850c4d5e6f8
Revises: 5b2eb2437398
Create Date: 2026-08-24 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a850c4d5e6f8"
down_revision: Union[str, Sequence[str], None] = "5b2eb2437398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("capabilities") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("tools") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("config_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("timeout_seconds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("employee_capabilities") as batch_op:
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("secret_ref", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_sources_code"), "knowledge_sources", ["code"], unique=False)
    op.create_index(op.f("ix_knowledge_sources_organization_id"), "knowledge_sources", ["organization_id"], unique=False)

    op.create_table(
        "knowledge_ingestions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("knowledge_source_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["knowledge_source_id"], ["knowledge_sources.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_ingestions_knowledge_source_id"), "knowledge_ingestions", ["knowledge_source_id"], unique=False)

    with op.batch_alter_table("employee_knowledge_sources") as batch_op:
        batch_op.add_column(sa.Column("knowledge_source_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_employee_knowledge_source", "knowledge_sources", ["knowledge_source_id"], ["id"])

    op.create_table(
        "test_lab_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("capability_id", sa.String(length=36), nullable=True),
        sa.Column("tool_id", sa.String(length=36), nullable=True),
        sa.Column("knowledge_source_ids_json", sa.Text(), nullable=True),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("context_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("approval_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approval_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["capability_id"], ["capabilities.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["ai_employees.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["work_plan_id"], ["work_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_lab_runs_organization_id"), "test_lab_runs", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_test_lab_runs_organization_id"), table_name="test_lab_runs")
    op.drop_table("test_lab_runs")

    with op.batch_alter_table("employee_knowledge_sources") as batch_op:
        batch_op.drop_constraint("fk_employee_knowledge_source", type_="foreignkey")
        batch_op.drop_column("knowledge_source_id")

    op.drop_index(op.f("ix_knowledge_ingestions_knowledge_source_id"), table_name="knowledge_ingestions")
    op.drop_table("knowledge_ingestions")
    op.drop_index(op.f("ix_knowledge_sources_organization_id"), table_name="knowledge_sources")
    op.drop_index(op.f("ix_knowledge_sources_code"), table_name="knowledge_sources")
    op.drop_table("knowledge_sources")

    with op.batch_alter_table("employee_capabilities") as batch_op:
        batch_op.drop_column("is_active")

    with op.batch_alter_table("tools") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("timeout_seconds")
        batch_op.drop_column("config_json")
        batch_op.drop_column("description")

    with op.batch_alter_table("capabilities") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("category")
