"""MB-06 fábrica empleados IA — ciclo de vida, versionado, capacitación.

Revision ID: mb06a1b2c3d4e
Revises: 1330b1b2c3d4f
Create Date: 2026-08-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6b06a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1330b1b2c3d4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    ev_cols = {c["name"] for c in inspector.get_columns("employee_versions")}

    with op.batch_alter_table("employee_versions") as batch:
        if "organization_id" not in ev_cols:
            batch.add_column(sa.Column("organization_id", sa.String(36), nullable=True))
        if "previous_version" not in ev_cols:
            batch.add_column(sa.Column("previous_version", sa.Integer(), nullable=True))
        if "changed_fields_json" not in ev_cols:
            batch.add_column(sa.Column("changed_fields_json", sa.Text(), nullable=True))
        if "change_reason" not in ev_cols:
            batch.add_column(sa.Column("change_reason", sa.Text(), nullable=True))
        if "test_summary_json" not in ev_cols:
            batch.add_column(sa.Column("test_summary_json", sa.Text(), nullable=True))
        if "approved_by_id" not in ev_cols:
            batch.add_column(sa.Column("approved_by_id", sa.String(36), nullable=True))
        if "published_at" not in ev_cols:
            batch.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE employee_versions
        SET organization_id = (
            SELECT organization_id FROM ai_employees WHERE ai_employees.id = employee_versions.employee_id
        )
        WHERE organization_id IS NULL
        """
    )

    etc_cols = {c["name"] for c in inspector.get_columns("employee_test_cases")}
    with op.batch_alter_table("employee_test_cases") as batch:
        if "organization_id" not in etc_cols:
            batch.add_column(sa.Column("organization_id", sa.String(36), nullable=True))
        if "test_category" not in etc_cols:
            batch.add_column(sa.Column("test_category", sa.String(20), server_default="TECHNICAL", nullable=False))
        if "criterion" not in etc_cols:
            batch.add_column(sa.Column("criterion", sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE employee_test_cases
        SET organization_id = (
            SELECT organization_id FROM ai_employees WHERE ai_employees.id = employee_test_cases.employee_id
        )
        WHERE organization_id IS NULL
        """
    )

    ae_cols = {c["name"] for c in inspector.get_columns("ai_employees")}
    if "last_training_at" not in ae_cols:
        with op.batch_alter_table("ai_employees") as batch:
            batch.add_column(sa.Column("last_training_at", sa.DateTime(timezone=True), nullable=True))

    if not inspector.has_table("employee_trainings"):
        op.create_table(
            "employee_trainings",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
            sa.Column("training_type", sa.String(40), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("source", sa.String(200), nullable=True),
            sa.Column("version_before", sa.Integer(), nullable=False),
            sa.Column("version_after", sa.Integer(), nullable=False),
            sa.Column("config_delta_json", sa.Text(), nullable=True),
            sa.Column("test_before_id", sa.String(36), sa.ForeignKey("employee_test_runs.id"), nullable=True),
            sa.Column("test_after_id", sa.String(36), sa.ForeignKey("employee_test_runs.id"), nullable=True),
            sa.Column("approved_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_employee_trainings_org", "employee_trainings", ["organization_id"])
        op.create_index("ix_employee_trainings_emp", "employee_trainings", ["employee_id"])

    if not inspector.has_table("employee_factory_approvals"):
        op.create_table(
            "employee_factory_approvals",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
            sa.Column("approval_request_id", sa.String(36), sa.ForeignKey("approval_requests.id"), nullable=False),
            sa.Column("approval_kind", sa.String(40), nullable=False),
            sa.Column("target_version", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(30), server_default="PENDING", nullable=False),
            sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_efa_org", "employee_factory_approvals", ["organization_id"])
        op.create_index("ix_efa_emp", "employee_factory_approvals", ["employee_id"])
        op.create_index("ix_efa_kind", "employee_factory_approvals", ["approval_kind"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("employee_factory_approvals"):
        op.drop_table("employee_factory_approvals")
    if inspector.has_table("employee_trainings"):
        op.drop_table("employee_trainings")

    with op.batch_alter_table("ai_employees") as batch:
        cols = {c["name"] for c in inspector.get_columns("ai_employees")}
        if "last_training_at" in cols:
            batch.drop_column("last_training_at")

    with op.batch_alter_table("employee_test_cases") as batch:
        cols = {c["name"] for c in inspector.get_columns("employee_test_cases")}
        for col in ("criterion", "test_category", "organization_id"):
            if col in cols:
                batch.drop_column(col)

    with op.batch_alter_table("employee_versions") as batch:
        cols = {c["name"] for c in inspector.get_columns("employee_versions")}
        for col in (
            "published_at",
            "approved_by_id",
            "test_summary_json",
            "change_reason",
            "changed_fields_json",
            "previous_version",
            "organization_id",
        ):
            if col in cols:
                batch.drop_column(col)
