"""Alembic — Modelo comercial basado en valor (1280)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1280a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1270a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("credential_mode", sa.String(30), nullable=False, server_default="IA_ADMINISTRADA"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("precio_base_mensual", sa.Numeric(18, 4), nullable=True),
        sa.Column("margen_minimo_pct", sa.Numeric(7, 4), nullable=False, server_default="0.15"),
        sa.Column("fraccion_valor_sugerida", sa.Numeric(7, 4), nullable=True),
        sa.Column("precio_minimo", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_maximo", sa.Numeric(18, 4), nullable=True),
        sa.Column("consumo_ia_incluido_tokens", sa.Integer(), nullable=True),
        sa.Column("presupuesto_ia_incluido", sa.Numeric(18, 4), nullable=True),
        sa.Column("excedente_ia_por_millon", sa.Numeric(18, 8), nullable=True),
        sa.Column("alerta_consumo_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("bloqueo_excedente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("limits_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_commercial_plan_org_code"),
    )
    op.create_index("ix_commercial_plans_org", "commercial_plans", ["organization_id"])

    op.create_table(
        "commercial_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="BORRADOR"),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("commercial_plans.id"), nullable=True),
        sa.Column("credential_mode", sa.String(30), nullable=False, server_default="IA_ADMINISTRADA"),
        sa.Column("escenario_recomendado", sa.String(20), nullable=False, server_default="BASE"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("valor_total_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_atribuible_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("costo_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_sugerido", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_final", sa.Numeric(18, 4), nullable=True),
        sa.Column("beneficio_neto_cliente", sa.Numeric(18, 4), nullable=True),
        sa.Column("roi_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("payback_meses", sa.Numeric(10, 2), nullable=True),
        sa.Column("pct_valor_conservado_cliente", sa.Numeric(7, 4), nullable=True),
        sa.Column("margen_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("vigencia_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supuestos_json", sa.Text(), nullable=True),
        sa.Column("riesgos_json", sa.Text(), nullable=True),
        sa.Column("traceability_json", sa.Text(), nullable=True),
        sa.Column("diagnostic_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_commercial_proposal_org_code"),
    )
    op.create_index("ix_commercial_proposals_org", "commercial_proposals", ["organization_id"])
    op.create_index("ix_commercial_proposals_estado", "commercial_proposals", ["estado"])

    op.create_table(
        "commercial_proposal_values",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("valuation_id", sa.String(36), nullable=True),
        sa.Column("linea_base_id", sa.String(36), nullable=True),
        sa.Column("categoria", sa.String(40), nullable=False),
        sa.Column("naturaleza", sa.String(20), nullable=False, server_default="ESTIMADO"),
        sa.Column("valor_bruto", sa.Numeric(18, 4), nullable=False),
        sa.Column("atribucion_pct", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("valor_atribuible", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("criterio_atribucion", sa.String(200), nullable=True),
        sa.Column("justificacion", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("dedupe_key", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_commercial_prop_values_proposal", "commercial_proposal_values", ["proposal_id"])
    op.create_index("ix_commercial_prop_values_dedupe", "commercial_proposal_values", ["dedupe_key"])

    op.create_table(
        "commercial_proposal_scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("scenario_type", sa.String(20), nullable=False),
        sa.Column("valor_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_atribuible", sa.Numeric(18, 4), nullable=True),
        sa.Column("probabilidad", sa.Numeric(7, 6), nullable=True),
        sa.Column("costo", sa.Numeric(18, 4), nullable=True),
        sa.Column("periodo_meses", sa.Integer(), nullable=True),
        sa.Column("riesgo_nivel", sa.String(20), nullable=True),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("es_recomendado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("proposal_id", "scenario_type", name="uq_proposal_scenario_type"),
    )

    op.create_table(
        "commercial_proposal_costs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("categoria", sa.String(40), nullable=False),
        sa.Column("clase_costo", sa.String(30), nullable=False, server_default="COSTO_INTERNO"),
        sa.Column("monto", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("finops_record_id", sa.String(36), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("es_recurrente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("periodo_meses", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "commercial_proposal_price_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("precio_sugerido", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_modificado", sa.Numeric(18, 4), nullable=True),
        sa.Column("justificacion", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "commercial_double_count_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("severidad", sa.String(20), nullable=False, server_default="ADVERTENCIA"),
        sa.Column("tipo", sa.String(60), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("value_ids_json", sa.Text(), nullable=True),
        sa.Column("resuelto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("commercial_double_count_alerts")
    op.drop_table("commercial_proposal_price_history")
    op.drop_table("commercial_proposal_costs")
    op.drop_table("commercial_proposal_scenarios")
    op.drop_index("ix_commercial_prop_values_dedupe", table_name="commercial_proposal_values")
    op.drop_index("ix_commercial_prop_values_proposal", table_name="commercial_proposal_values")
    op.drop_table("commercial_proposal_values")
    op.drop_index("ix_commercial_proposals_estado", table_name="commercial_proposals")
    op.drop_index("ix_commercial_proposals_org", table_name="commercial_proposals")
    op.drop_table("commercial_proposals")
    op.drop_index("ix_commercial_plans_org", table_name="commercial_plans")
    op.drop_table("commercial_plans")
