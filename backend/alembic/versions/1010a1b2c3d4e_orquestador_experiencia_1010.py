"""orquestador_experiencia_1010

Revision ID: 1010a1b2c3d4e
Revises: 972a1b2c3d4e
Create Date: 2026-08-27 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1010a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "972a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_experience_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=36), nullable=False),
        sa.Column("dominio", sa.String(length=80), nullable=False),
        sa.Column("tipo_problema", sa.String(length=120), nullable=False),
        sa.Column("contexto_json", sa.Text(), nullable=True),
        sa.Column("senales_json", sa.Text(), nullable=True),
        sa.Column("hipotesis", sa.String(length=300), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("accion", sa.Text(), nullable=True),
        sa.Column("resultado_esperado", sa.Text(), nullable=True),
        sa.Column("resultado_real", sa.Text(), nullable=True),
        sa.Column("kpi_antes_json", sa.Text(), nullable=True),
        sa.Column("kpi_despues_json", sa.Text(), nullable=True),
        sa.Column("valor_esperado", sa.Float(), nullable=True),
        sa.Column("valor_obtenido", sa.Float(), nullable=True),
        sa.Column("tiempo_esperado_horas", sa.Float(), nullable=True),
        sa.Column("tiempo_real_horas", sa.Float(), nullable=True),
        sa.Column("feedback_humano", sa.String(length=60), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("confianza", sa.Float(), nullable=True),
        sa.Column("peso_calidad", sa.Float(), nullable=True),
        sa.Column("condiciones_exito_json", sa.Text(), nullable=True),
        sa.Column("condiciones_fracaso_json", sa.Text(), nullable=True),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("caso_origen_id", sa.String(length=36), nullable=True),
        sa.Column("trazabilidad_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resultado_actualizado_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["ai_employees.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["work_plan_id"], ["work_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exp_records_org", "employee_experience_records", ["organization_id"])
    op.create_index("ix_exp_records_emp", "employee_experience_records", ["employee_id"])
    op.create_index("ix_exp_records_dominio", "employee_experience_records", ["dominio"])
    op.create_index("ix_exp_records_tipo", "employee_experience_records", ["tipo_problema"])
    op.create_index("ix_exp_records_estado", "employee_experience_records", ["estado"])

    op.create_table(
        "experience_selection_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("solicitud", sa.Text(), nullable=True),
        sa.Column("dominio_principal", sa.String(length=80), nullable=True),
        sa.Column("candidatos_json", sa.Text(), nullable=True),
        sa.Column("factores_json", sa.Text(), nullable=True),
        sa.Column("experiencia_consultada_json", sa.Text(), nullable=True),
        sa.Column("seleccionados_json", sa.Text(), nullable=True),
        sa.Column("roles_json", sa.Text(), nullable=True),
        sa.Column("razon_seleccion", sa.Text(), nullable=True),
        sa.Column("work_plan_id", sa.String(length=36), nullable=True),
        sa.Column("caso_origen_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exp_sel_logs_org", "experience_selection_logs", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_exp_sel_logs_org", table_name="experience_selection_logs")
    op.drop_table("experience_selection_logs")
    op.drop_index("ix_exp_records_estado", table_name="employee_experience_records")
    op.drop_index("ix_exp_records_tipo", table_name="employee_experience_records")
    op.drop_index("ix_exp_records_dominio", table_name="employee_experience_records")
    op.drop_index("ix_exp_records_emp", table_name="employee_experience_records")
    op.drop_index("ix_exp_records_org", table_name="employee_experience_records")
    op.drop_table("employee_experience_records")
