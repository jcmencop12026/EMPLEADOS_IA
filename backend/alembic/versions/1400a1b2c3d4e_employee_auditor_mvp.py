"""Migración — Auditor determinístico Empleados IA MVP.

revision_id 1400a1b2c3d4e: identificador único portable del Auditor.
NO define un bloque funcional «1400» en el producto.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1400a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1391a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_audit_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="WEEKLY"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("thresholds_json", sa.Text(), nullable=True),
        sa.Column("metrics_active_json", sa.Text(), nullable=True),
        sa.Column("allowed_actions_json", sa.Text(), nullable=True),
        sa.Column("budget_usd", sa.Float(), nullable=True),
        sa.Column("max_runs_per_window", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("window_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("automation_id", sa.String(36), sa.ForeignKey("automations.id"), nullable=True),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "employee_id", name="uq_employee_audit_policy_org_emp"),
    )
    op.create_index("ix_employee_audit_policies_org", "employee_audit_policies", ["organization_id"])

    op.create_table(
        "employee_audit_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("employee_audit_policies.id"), nullable=True),
        sa.Column("trigger_type", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("trigger_ref", sa.String(120), nullable=True),
        sa.Column("scope_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="RUNNING"),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("employee_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("initiated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_employee_audit_run_idempotency"),
    )
    op.create_index("ix_employee_audit_runs_org", "employee_audit_runs", ["organization_id"])
    op.create_index("ix_employee_audit_runs_started", "employee_audit_runs", ["started_at"])

    op.create_table(
        "employee_audit_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("employee_audit_runs.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("health_status", sa.String(30), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("metrics_snapshot_json", sa.Text(), nullable=True),
        sa.Column("lifecycle_status", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "employee_id", name="uq_employee_audit_assessment_run_emp"),
    )
    op.create_index("ix_employee_audit_assessments_org", "employee_audit_assessments", ["organization_id"])
    op.create_index("ix_employee_audit_assessments_health", "employee_audit_assessments", ["health_status"])

    op.create_table(
        "employee_audit_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("employee_audit_runs.id"), nullable=False),
        sa.Column("assessment_id", sa.String(36), sa.ForeignKey("employee_audit_assessments.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("rule_code", sa.String(60), nullable=False),
        sa.Column("metric_name", sa.String(60), nullable=False),
        sa.Column("observed_value", sa.String(120), nullable=True),
        sa.Column("threshold_value", sa.String(120), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="ADVERTENCIA"),
        sa.Column("semantic_kind", sa.String(20), nullable=False, server_default="HECHO"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.String(40), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ABIERTO"),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("notification_id", sa.String(36), sa.ForeignKey("notifications.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_employee_audit_findings_org", "employee_audit_findings", ["organization_id"])
    op.create_index("ix_employee_audit_findings_status", "employee_audit_findings", ["status"])
    op.create_index("ix_employee_audit_findings_severity", "employee_audit_findings", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_employee_audit_findings_severity", table_name="employee_audit_findings")
    op.drop_index("ix_employee_audit_findings_status", table_name="employee_audit_findings")
    op.drop_index("ix_employee_audit_findings_org", table_name="employee_audit_findings")
    op.drop_table("employee_audit_findings")
    op.drop_index("ix_employee_audit_assessments_health", table_name="employee_audit_assessments")
    op.drop_index("ix_employee_audit_assessments_org", table_name="employee_audit_assessments")
    op.drop_table("employee_audit_assessments")
    op.drop_index("ix_employee_audit_runs_started", table_name="employee_audit_runs")
    op.drop_index("ix_employee_audit_runs_org", table_name="employee_audit_runs")
    op.drop_table("employee_audit_runs")
    op.drop_index("ix_employee_audit_policies_org", table_name="employee_audit_policies")
    op.drop_table("employee_audit_policies")
