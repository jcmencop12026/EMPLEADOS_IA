"""Puente trazabilidad Auditor → Fábrica (ciclo de mejora).

Revision ID: 14b1c2d3e4f5
Revises: 14b0c1d2e3f4
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "14b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "14b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_improvement_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("audit_run_id", sa.String(36), sa.ForeignKey("employee_audit_runs.id"), nullable=True),
        sa.Column("finding_id", sa.String(36), sa.ForeignKey("employee_audit_findings.id"), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("recommendation", sa.String(80), nullable=False),
        sa.Column("work_item_ref", sa.String(120), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("outcome_classification", sa.String(40), nullable=True),
        sa.Column("requested_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("executed_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("factory_operation", sa.String(40), nullable=True),
        sa.Column("factory_result_ref", sa.String(120), nullable=True),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("employee_versions.id"), nullable=True),
        sa.Column("approval_id", sa.String(36), sa.ForeignKey("approval_requests.id"), nullable=True),
        sa.Column("test_run_id", sa.String(36), sa.ForeignKey("employee_test_runs.id"), nullable=True),
        sa.Column("before_snapshot_json", sa.Text(), nullable=True),
        sa.Column("after_snapshot_json", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_emp_improvement_idempotency"),
    )
    op.create_index("ix_emp_improvement_org", "employee_improvement_traces", ["organization_id"])
    op.create_index("ix_emp_improvement_employee", "employee_improvement_traces", ["employee_id"])
    op.create_index("ix_emp_improvement_finding", "employee_improvement_traces", ["finding_id"])
    op.create_index("ix_emp_improvement_status", "employee_improvement_traces", ["status"])


def downgrade() -> None:
    op.drop_index("ix_emp_improvement_status", table_name="employee_improvement_traces")
    op.drop_index("ix_emp_improvement_finding", table_name="employee_improvement_traces")
    op.drop_index("ix_emp_improvement_employee", table_name="employee_improvement_traces")
    op.drop_index("ix_emp_improvement_org", table_name="employee_improvement_traces")
    op.drop_table("employee_improvement_traces")
