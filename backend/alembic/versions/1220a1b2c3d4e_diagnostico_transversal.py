"""Migración 1220 — Diagnóstico transversal multidominio."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1220a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1120a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_indicator_defs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("dominio", sa.String(60), nullable=False),
        sa.Column("proceso", sa.String(120), nullable=True),
        sa.Column("subproceso", sa.String(120), nullable=True),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("direccion_esperada", sa.String(20), nullable=False, server_default="CUALQUIERA"),
        sa.Column("periodicidad", sa.String(40), nullable=True),
        sa.Column("umbral_min", sa.Numeric(18, 4), nullable=True),
        sa.Column("umbral_max", sa.Numeric(18, 4), nullable=True),
        sa.Column("fuente_code", sa.String(80), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_ind_def_org", "diagnostic_indicator_defs", ["organization_id"])
    op.create_index("ix_diag_ind_def_org_code", "diagnostic_indicator_defs", ["organization_id", "code"], unique=True)

    op.create_table(
        "diagnostic_indicator_values",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("indicator_def_id", sa.String(36), sa.ForeignKey("diagnostic_indicator_defs.id"), nullable=True),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("proactive_signals.id"), nullable=True),
        sa.Column("dominio", sa.String(60), nullable=False),
        sa.Column("proceso", sa.String(120), nullable=True),
        sa.Column("metrica", sa.String(120), nullable=False),
        sa.Column("valor", sa.Numeric(18, 4), nullable=True),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("periodo_referencia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_ind_val_org", "diagnostic_indicator_values", ["organization_id"])
    op.create_index("ix_diag_ind_val_org_metric", "diagnostic_indicator_values", ["organization_id", "dominio", "metrica"])

    op.create_table(
        "diagnostic_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("tipo_contenido", sa.String(20), nullable=False, server_default="HECHO"),
        sa.Column("que_ocurre", sa.String(500), nullable=False),
        sa.Column("donde", sa.String(200), nullable=True),
        sa.Column("desde_cuando", sa.DateTime(timezone=True), nullable=True),
        sa.Column("magnitud", sa.Numeric(18, 4), nullable=True),
        sa.Column("severidad", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=False, server_default="0.7"),
        sa.Column("dominio", sa.String(60), nullable=False),
        sa.Column("proceso", sa.String(120), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("indicadores_json", sa.Text(), nullable=True),
        sa.Column("signal_ids_json", sa.Text(), nullable=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("signal_sources.id"), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="DETECTADO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_finding_org", "diagnostic_findings", ["organization_id"])
    op.create_index("ix_diag_finding_org_codigo", "diagnostic_findings", ["organization_id", "codigo"])

    op.create_table(
        "diagnostic_correlations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("finding_ids_json", sa.Text(), nullable=True),
        sa.Column("indicator_value_ids_json", sa.Text(), nullable=True),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=False, server_default="0.6"),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("es_causal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("nota_causalidad", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_corr_org", "diagnostic_correlations", ["organization_id"])

    op.create_table(
        "diagnostics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("periodo_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("periodo_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="GENERADO"),
        sa.Column("dominios_json", sa.Text(), nullable=True),
        sa.Column("procesos_json", sa.Text(), nullable=True),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column("prioridad_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("explicacion_json", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_org", "diagnostics", ["organization_id"])
    op.create_index("ix_diag_org_codigo_ver", "diagnostics", ["organization_id", "codigo", "version"])

    op.create_table(
        "diagnostic_probable_causes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("finding_id", sa.String(36), sa.ForeignKey("diagnostic_findings.id"), nullable=True),
        sa.Column("diagnostic_id", sa.String(36), sa.ForeignKey("diagnostics.id"), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="HIPOTESIS"),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=False, server_default="0.5"),
        sa.Column("fuentes_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_cause_org", "diagnostic_probable_causes", ["organization_id"])

    op.create_table(
        "diagnostic_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("diagnostic_id", sa.String(36), sa.ForeignKey("diagnostics.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("diagnostic_findings.id"), nullable=True),
        sa.Column("causa_id", sa.String(36), sa.ForeignKey("diagnostic_probable_causes.id"), nullable=True),
        sa.Column("prioridad_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("impacto_json", sa.Text(), nullable=True),
        sa.Column("accion_recomendada_json", sa.Text(), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_item_diag", "diagnostic_items", ["diagnostic_id"])

    op.create_table(
        "diagnostic_opportunity_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("diagnostic_id", sa.String(36), sa.ForeignKey("diagnostics.id"), nullable=False),
        sa.Column("finding_id", sa.String(36), sa.ForeignKey("diagnostic_findings.id"), nullable=True),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("proactive_signals.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("dedupe_key", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diag_opp_link_org", "diagnostic_opportunity_links", ["organization_id"])
    op.create_index("ix_diag_opp_link_dedupe", "diagnostic_opportunity_links", ["organization_id", "dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_diag_opp_link_dedupe", table_name="diagnostic_opportunity_links")
    op.drop_index("ix_diag_opp_link_org", table_name="diagnostic_opportunity_links")
    op.drop_table("diagnostic_opportunity_links")
    op.drop_index("ix_diag_item_diag", table_name="diagnostic_items")
    op.drop_table("diagnostic_items")
    op.drop_index("ix_diag_cause_org", table_name="diagnostic_probable_causes")
    op.drop_table("diagnostic_probable_causes")
    op.drop_index("ix_diag_org_codigo_ver", table_name="diagnostics")
    op.drop_index("ix_diag_org", table_name="diagnostics")
    op.drop_table("diagnostics")
    op.drop_index("ix_diag_corr_org", table_name="diagnostic_correlations")
    op.drop_table("diagnostic_correlations")
    op.drop_index("ix_diag_finding_org_codigo", table_name="diagnostic_findings")
    op.drop_index("ix_diag_finding_org", table_name="diagnostic_findings")
    op.drop_table("diagnostic_findings")
    op.drop_index("ix_diag_ind_val_org_metric", table_name="diagnostic_indicator_values")
    op.drop_index("ix_diag_ind_val_org", table_name="diagnostic_indicator_values")
    op.drop_table("diagnostic_indicator_values")
    op.drop_index("ix_diag_ind_def_org_code", table_name="diagnostic_indicator_defs")
    op.drop_index("ix_diag_ind_def_org", table_name="diagnostic_indicator_defs")
    op.drop_table("diagnostic_indicator_defs")
