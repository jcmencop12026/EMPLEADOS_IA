"""Migración 1200 — Línea base, medición posterior e impacto."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1200a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lineas_base",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("indicador", sa.String(120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("unidad", sa.String(40), nullable=False, server_default="unidad"),
        sa.Column("valor_base", sa.Numeric(18, 4), nullable=False),
        sa.Column("fecha_inicio_base", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin_base", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fuente", sa.String(60), nullable=False, server_default="MANUAL"),
        sa.Column("metodo_calculo", sa.Text(), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("direccion_indicador", sa.String(30), nullable=False, server_default="MAYOR_ES_MEJOR"),
        sa.Column("impacto_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="BORRADOR"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("proceso", sa.String(120), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("accion_referencia", sa.String(200), nullable=True),
        sa.Column("valor_economico_tipo", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lineas_base_org", "lineas_base", ["organization_id"])
    op.create_index("ix_lineas_base_opp", "lineas_base", ["opportunity_id"])

    op.create_table(
        "lineas_base_mediciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("linea_base_id", sa.String(36), sa.ForeignKey("lineas_base.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("valor_posterior", sa.Numeric(18, 4), nullable=False),
        sa.Column("periodo_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("periodo_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fuente", sa.String(60), nullable=False, server_default="MANUAL"),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="REGISTRADA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_lb_mediciones_lb", "lineas_base_mediciones", ["linea_base_id"])

    op.create_table(
        "lineas_base_impactos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("linea_base_id", sa.String(36), sa.ForeignKey("lineas_base.id"), nullable=False),
        sa.Column("medicion_id", sa.String(36), sa.ForeignKey("lineas_base_mediciones.id"), nullable=False, unique=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("valor_base", sa.Numeric(18, 4), nullable=False),
        sa.Column("valor_posterior", sa.Numeric(18, 4), nullable=False),
        sa.Column("variacion_absoluta", sa.Numeric(18, 4), nullable=False),
        sa.Column("variacion_porcentual", sa.Numeric(10, 4), nullable=True),
        sa.Column("evaluacion", sa.String(30), nullable=False),
        sa.Column("tipo_impacto", sa.String(40), nullable=False, server_default="CAMBIO_OBSERVADO"),
        sa.Column("atribucion_nivel", sa.String(40), nullable=False, server_default="NO_ATRIBUIBLE"),
        sa.Column("atribucion_porcentaje", sa.Numeric(5, 2), nullable=True),
        sa.Column("atribucion_justificacion", sa.Text(), nullable=True),
        sa.Column("atribucion_evidencia_json", sa.Text(), nullable=True),
        sa.Column("impacto_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("impacto_real", sa.Numeric(18, 4), nullable=True),
        sa.Column("congelado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lb_impactos_lb", "lineas_base_impactos", ["linea_base_id"])

    op.create_table(
        "lineas_base_historial",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("linea_base_id", sa.String(36), sa.ForeignKey("lineas_base.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lb_historial_lb", "lineas_base_historial", ["linea_base_id"])


def downgrade() -> None:
    op.drop_table("lineas_base_historial")
    op.drop_table("lineas_base_impactos")
    op.drop_table("lineas_base_mediciones")
    op.drop_table("lineas_base")
