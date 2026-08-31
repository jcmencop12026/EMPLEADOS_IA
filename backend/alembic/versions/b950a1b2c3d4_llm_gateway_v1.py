"""Migración LLM Gateway V1 — Paquete B."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b950a1b2c3d4"
down_revision: Union[str, None] = "1030a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_provider_configs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider_type", sa.String(length=40), nullable=False),
        sa.Column("model_default", sa.String(length=120), nullable=True),
        sa.Column("endpoint", sa.String(length=500), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("secret_ref", sa.String(length=200), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_provider_configs_org", "llm_provider_configs", ["organization_id"])
    op.create_index("ix_llm_provider_configs_type", "llm_provider_configs", ["provider_type"])

    op.create_table(
        "llm_inference_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("trace_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=True),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("tokens_total", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="OK"),
        sa.Column("finish_reason", sa.String(length=40), nullable=True),
        sa.Column("error_category", sa.String(length=40), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("initial_provider", sa.String(length=80), nullable=True),
        sa.Column("fallback_provider", sa.String(length=80), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["ai_employees.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["employee_tasks.id"]),
        sa.ForeignKeyConstraint(["work_plan_id"], ["work_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_inference_logs_org", "llm_inference_logs", ["organization_id"])
    op.create_index("ix_llm_inference_logs_trace", "llm_inference_logs", ["trace_id"])
    op.create_index("ix_llm_inference_logs_created", "llm_inference_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_llm_inference_logs_created", table_name="llm_inference_logs")
    op.drop_index("ix_llm_inference_logs_trace", table_name="llm_inference_logs")
    op.drop_index("ix_llm_inference_logs_org", table_name="llm_inference_logs")
    op.drop_table("llm_inference_logs")
    op.drop_index("ix_llm_provider_configs_type", table_name="llm_provider_configs")
    op.drop_index("ix_llm_provider_configs_org", table_name="llm_provider_configs")
    op.drop_table("llm_provider_configs")
