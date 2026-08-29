"""Alembic — Inteligencia externa y oportunidades estratégicas (1240)."""

from alembic import op
import sqlalchemy as sa

revision = "1240c3d4e5f6a"
down_revision = "1120a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_external_context",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("mercado", sa.String(length=200), nullable=True),
        sa.Column("productos_servicios", sa.Text(), nullable=True),
        sa.Column("geografias", sa.Text(), nullable=True),
        sa.Column("clientes_objetivo", sa.Text(), nullable=True),
        sa.Column("procesos_clave", sa.Text(), nullable=True),
        sa.Column("estrategia", sa.Text(), nullable=True),
        sa.Column("dominios_json", sa.Text(), nullable=True),
        sa.Column("freshness_recent_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("freshness_stale_days", sa.Integer(), nullable=False, server_default="180"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", name="uq_org_external_context"),
    )

    op.create_table(
        "external_sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("signal_source_id", sa.String(length=36), sa.ForeignKey("signal_sources.id"), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("ingestion_channel", sa.String(length=40), nullable=False),
        sa.Column("url_reference", sa.String(length=500), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("pais_region", sa.String(length=120), nullable=True),
        sa.Column("frecuencia_esperada", sa.String(length=60), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="ACTIVA"),
        sa.Column("confiabilidad", sa.Numeric(5, 4), nullable=False, server_default="0.5"),
        sa.Column("ultima_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_external_source_org_code"),
    )
    op.create_index("ix_external_sources_org", "external_sources", ["organization_id"])
    op.create_index("ix_external_sources_type", "external_sources", ["source_type"])

    op.create_table(
        "external_signal_extensions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("proactive_signals.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("external_source_id", sa.String(length=36), sa.ForeignKey("external_sources.id"), nullable=True),
        sa.Column("ambito", sa.String(length=20), nullable=False, server_default="EXTERNO"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("freshness_status", sa.String(length=30), nullable=False, server_default="SIN FECHA VERIFICABLE"),
        sa.Column("classification", sa.String(length=30), nullable=False, server_default="INFORMACIÓN"),
        sa.Column("relevance", sa.String(length=30), nullable=False, server_default="POSIBLEMENTE RELEVANTE"),
        sa.Column("hecho_observado", sa.Text(), nullable=True),
        sa.Column("interpretacion", sa.Text(), nullable=True),
        sa.Column("hipotesis", sa.Text(), nullable=True),
        sa.Column("oportunidad_propuesta", sa.Text(), nullable=True),
        sa.Column("confidence_level", sa.Numeric(5, 4), nullable=False, server_default="0.5"),
        sa.Column("is_risk", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("risk_type", sa.String(length=60), nullable=True),
        sa.Column("competitor_json", sa.Text(), nullable=True),
        sa.Column("regulation_json", sa.Text(), nullable=True),
        sa.Column("technology_json", sa.Text(), nullable=True),
        sa.Column("demand_json", sa.Text(), nullable=True),
        sa.Column("valuation_contract_ref", sa.String(length=200), nullable=True),
        sa.Column("diagnostic_contract_ref", sa.String(length=200), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validated_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("signal_id", name="uq_external_signal_extension"),
    )
    op.create_index("ix_external_signal_ext_org", "external_signal_extensions", ["organization_id"])

    op.create_table(
        "external_evidence",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("proactive_signals.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("external_source_id", sa.String(length=36), sa.ForeignKey("external_sources.id"), nullable=True),
        sa.Column("reference_url", sa.String(length=500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("structured_content", sa.Text(), nullable=True),
        sa.Column("observed_data", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("dedupe_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "dedupe_hash", name="uq_external_evidence_dedupe"),
    )
    op.create_index("ix_external_evidence_signal", "external_evidence", ["signal_id"])


def downgrade() -> None:
    op.drop_index("ix_external_evidence_signal", table_name="external_evidence")
    op.drop_table("external_evidence")
    op.drop_index("ix_external_signal_ext_org", table_name="external_signal_extensions")
    op.drop_table("external_signal_extensions")
    op.drop_index("ix_external_sources_type", table_name="external_sources")
    op.drop_index("ix_external_sources_org", table_name="external_sources")
    op.drop_table("external_sources")
    op.drop_table("organization_external_context")
