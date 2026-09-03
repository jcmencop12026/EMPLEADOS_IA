"""Alembic — Empleado IA 2.0 evolución (1510)."""

from alembic import op
import sqlalchemy as sa

revision = "1510a1b2c3d4e"
down_revision = "1030a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_labor_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("cargo", sa.String(160), nullable=True),
        sa.Column("mision", sa.Text(), nullable=True),
        sa.Column("funciones_json", sa.Text(), nullable=True),
        sa.Column("responsabilidades_json", sa.Text(), nullable=True),
        sa.Column("procesos_json", sa.Text(), nullable=True),
        sa.Column("empresa_ref", sa.String(200), nullable=True),
        sa.Column("supervisor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("limites_json", sa.Text(), nullable=True),
        sa.Column("horario_json", sa.Text(), nullable=True),
        sa.Column("autonomy_level", sa.String(40), nullable=False, server_default="EJECUTA_CON_APROBACION"),
        sa.Column("indicadores_json", sa.Text(), nullable=True),
        sa.Column("criterios_exito_json", sa.Text(), nullable=True),
        sa.Column("criterios_escalamiento_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("employee_id", name="uq_emp_labor_profile_employee"),
    )
    op.create_index("ix_emp_labor_org", "employee_labor_profiles", ["organization_id"])

    op.create_table(
        "employee_supervision_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("employee_tasks.id"), nullable=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("metricas_json", sa.Text(), nullable=True),
        sa.Column("calidad_score", sa.Float(), nullable=True),
        sa.Column("duracion_ms", sa.Integer(), nullable=True),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_sup_org_emp", "employee_supervision_logs", ["organization_id", "employee_id", "created_at"])

    op.create_table(
        "employee_performance_indicators",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("codigo", sa.String(80), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("unidad", sa.String(40), nullable=False, server_default="%"),
        sa.Column("valor_esperado", sa.Float(), nullable=True),
        sa.Column("valor_real", sa.Float(), nullable=True),
        sa.Column("periodo", sa.String(40), nullable=True),
        sa.Column("alerta", sa.String(60), nullable=True),
        sa.Column("evidencia_ref", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_perf_org_emp", "employee_performance_indicators", ["organization_id", "employee_id"])

    op.create_table(
        "employee_learning_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PROPUESTA"),
        sa.Column("observacion", sa.Text(), nullable=False),
        sa.Column("causa_probable", sa.Text(), nullable=True),
        sa.Column("propuesta", sa.Text(), nullable=False),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("impacto_esperado", sa.Text(), nullable=True),
        sa.Column("target_version", sa.Integer(), nullable=True),
        sa.Column("aprobado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_learn_org_emp", "employee_learning_proposals", ["organization_id", "employee_id", "estado"])

    op.create_table(
        "employee_result_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("employee_tasks.id"), nullable=True),
        sa.Column("resultado_ref", sa.String(200), nullable=True),
        sa.Column("indicador_codigo", sa.String(80), nullable=True),
        sa.Column("valor_ref", sa.Float(), nullable=True),
        sa.Column("valor_economico_ref", sa.String(120), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_res_org_emp", "employee_result_links", ["organization_id", "employee_id"])


def downgrade() -> None:
    op.drop_index("ix_emp_res_org_emp", table_name="employee_result_links")
    op.drop_table("employee_result_links")
    op.drop_index("ix_emp_learn_org_emp", table_name="employee_learning_proposals")
    op.drop_table("employee_learning_proposals")
    op.drop_index("ix_emp_perf_org_emp", table_name="employee_performance_indicators")
    op.drop_table("employee_performance_indicators")
    op.drop_index("ix_emp_sup_org_emp", table_name="employee_supervision_logs")
    op.drop_table("employee_supervision_logs")
    op.drop_index("ix_emp_labor_org", table_name="employee_labor_profiles")
    op.drop_table("employee_labor_profiles")
