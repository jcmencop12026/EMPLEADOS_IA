"""Migración 1290 — Optimización y recomendaciones."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1290a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1260a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "optimizacion_configuraciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("objetivo_default", sa.String(40), nullable=False, server_default="RESULTADO_EQUILIBRADO"),
        sa.Column("pesos_json", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opt_config_org", "optimizacion_configuraciones", ["organization_id"], unique=True)

    op.create_table(
        "optimizacion_recomendaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PROPUESTA"),
        sa.Column("objetivo", sa.String(40), nullable=False),
        sa.Column("es_simulacion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("grupo_comparacion_id", sa.String(36), nullable=True),
        sa.Column("restricciones_json", sa.Text(), nullable=True),
        sa.Column("resultado_json", sa.Text(), nullable=True),
        sa.Column("explicacion_json", sa.Text(), nullable=True),
        sa.Column("aprendizaje_influencia_json", sa.Text(), nullable=True),
        sa.Column("trazabilidad_json", sa.Text(), nullable=True),
        sa.Column("factible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("conflicto_restricciones_json", sa.Text(), nullable=True),
        sa.Column("valor_esperado_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("costo_esperado_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("impacto_esperado_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("riesgo_promedio", sa.Numeric(8, 4), nullable=True),
        sa.Column("confianza_promedio", sa.Numeric(8, 4), nullable=True),
        sa.Column("roi_esperado", sa.Numeric(10, 4), nullable=True),
        sa.Column("tiempo_esperado_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("justificacion_aprobacion", sa.Text(), nullable=True),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("recomendacion_origen_id", sa.String(36), sa.ForeignKey("optimizacion_recomendaciones.id"), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decidida_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decidida_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opt_rec_org", "optimizacion_recomendaciones", ["organization_id"])
    op.create_index("ix_opt_rec_org_estado", "optimizacion_recomendaciones", ["organization_id", "estado"])
    op.create_index("ix_opt_rec_codigo", "optimizacion_recomendaciones", ["codigo"])

    op.create_table(
        "optimizacion_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recomendacion_id", sa.String(36), sa.ForeignKey("optimizacion_recomendaciones.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("seleccionado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("orden", sa.Integer(), nullable=True),
        sa.Column("puntuacion_total", sa.Numeric(10, 4), nullable=True),
        sa.Column("factores_json", sa.Text(), nullable=True),
        sa.Column("exclusion_razon", sa.Text(), nullable=True),
        sa.Column("valor_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("costo_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("impacto_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("riesgo", sa.Numeric(8, 4), nullable=True),
        sa.Column("confianza", sa.Numeric(8, 4), nullable=True),
        sa.Column("probabilidad_exito", sa.Numeric(8, 4), nullable=True),
        sa.Column("tiempo_esperado_dias", sa.Numeric(10, 2), nullable=True),
        sa.Column("aprendizaje_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_opt_item_rec", "optimizacion_items", ["recomendacion_id"])
    op.create_index("ix_opt_item_rec_opp", "optimizacion_items", ["recomendacion_id", "opportunity_id"])

    op.create_table(
        "optimizacion_auditoria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("recomendacion_id", sa.String(36), sa.ForeignKey("optimizacion_recomendaciones.id"), nullable=True),
        sa.Column("accion", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opt_auditoria_org", "optimizacion_auditoria", ["organization_id"])


def downgrade() -> None:
    op.drop_table("optimizacion_auditoria")
    op.drop_table("optimizacion_items")
    op.drop_table("optimizacion_recomendaciones")
    op.drop_table("optimizacion_configuraciones")
