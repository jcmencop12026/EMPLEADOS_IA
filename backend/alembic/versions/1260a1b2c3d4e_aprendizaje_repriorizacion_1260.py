"""Migración 1260 — Aprendizaje, retroalimentación y repriorización."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1260a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1330b1b2c3d4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ciclos_aprendizaje",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("proactive_signals.id"), nullable=True),
        sa.Column("diagnostic_id", sa.String(36), sa.ForeignKey("diagnostics.id"), nullable=True),
        sa.Column("valuation_id", sa.String(36), sa.ForeignKey("opportunity_valuations.id"), nullable=True),
        sa.Column("linea_base_id", sa.String(36), sa.ForeignKey("lineas_base.id"), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="ABIERTO"),
        sa.Column("impacto_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("costo_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("tiempo_esperado_dias", sa.Numeric(10, 2), nullable=True),
        sa.Column("impacto_real", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_real", sa.Numeric(18, 4), nullable=True),
        sa.Column("costo_real", sa.Numeric(18, 4), nullable=True),
        sa.Column("tiempo_real_dias", sa.Numeric(10, 2), nullable=True),
        sa.Column("desviaciones_json", sa.Text(), nullable=True),
        sa.Column("calidad_recomendacion", sa.String(30), nullable=True),
        sa.Column("prioridad_anterior", sa.Numeric(8, 4), nullable=True),
        sa.Column("prioridad_propuesta", sa.Numeric(8, 4), nullable=True),
        sa.Column("explicacion_prioridad_json", sa.Text(), nullable=True),
        sa.Column("referencias_json", sa.Text(), nullable=True),
        sa.Column("evaluado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("evaluado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ciclo_aprendizaje_org", "ciclos_aprendizaje", ["organization_id"])
    op.create_index("ix_ciclo_aprendizaje_org_opp", "ciclos_aprendizaje", ["organization_id", "opportunity_id"])

    op.create_table(
        "retroalimentaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ciclo_id", sa.String(36), sa.ForeignKey("ciclos_aprendizaje.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("tipo_explicacion", sa.String(30), nullable=False, server_default="PROBABLE"),
        sa.Column("calidad_recomendacion", sa.String(30), nullable=False),
        sa.Column("resumen", sa.String(500), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("lecciones_json", sa.Text(), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_retroalimentacion_org", "retroalimentaciones", ["organization_id"])
    op.create_index("ix_retroalimentacion_ciclo", "retroalimentaciones", ["ciclo_id"])

    op.create_table(
        "recalibraciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ciclo_id", sa.String(36), sa.ForeignKey("ciclos_aprendizaje.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="SUGERIDA"),
        sa.Column("campo", sa.String(60), nullable=False),
        sa.Column("valor_anterior", sa.String(200), nullable=True),
        sa.Column("valor_nuevo", sa.String(200), nullable=True),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("factores_json", sa.Text(), nullable=True),
        sa.Column("sugerida_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("sugerida_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decidida_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decidida_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aplicada_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("aplicada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
    )
    op.create_index("ix_recalibracion_org", "recalibraciones", ["organization_id"])
    op.create_index("ix_recalibracion_ciclo", "recalibraciones", ["ciclo_id"])
    op.create_index("ix_recalibracion_estado", "recalibraciones", ["organization_id", "estado"])

    op.create_table(
        "patrones_aprendizaje",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo_patron", sa.String(40), nullable=False),
        sa.Column("clave_patron", sa.String(200), nullable=False),
        sa.Column("dominio", sa.String(60), nullable=True),
        sa.Column("tipo_oportunidad", sa.String(40), nullable=True),
        sa.Column("ocurrencias", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("resumen", sa.String(500), nullable=False),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("ultima_deteccion_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_patron_aprendizaje_org", "patrones_aprendizaje", ["organization_id"])
    op.create_index("ix_patron_aprendizaje_org_tipo", "patrones_aprendizaje", ["organization_id", "tipo_patron", "clave_patron"])

    op.create_table(
        "aprendizaje_auditoria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ciclo_id", sa.String(36), sa.ForeignKey("ciclos_aprendizaje.id"), nullable=True),
        sa.Column("recalibracion_id", sa.String(36), sa.ForeignKey("recalibraciones.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("accion", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aprendizaje_auditoria_org", "aprendizaje_auditoria", ["organization_id"])


def downgrade() -> None:
    op.drop_table("aprendizaje_auditoria")
    op.drop_table("patrones_aprendizaje")
    op.drop_table("recalibraciones")
    op.drop_table("retroalimentaciones")
    op.drop_table("ciclos_aprendizaje")
