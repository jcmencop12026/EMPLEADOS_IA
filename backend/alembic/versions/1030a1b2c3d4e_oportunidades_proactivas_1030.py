"""Migración 1030 — Inteligencia proactiva y centro de oportunidades."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1030a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1010a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "proactive_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(60), nullable=False),
        sa.Column("dominio", sa.String(60), nullable=False),
        sa.Column("origen", sa.String(60), nullable=False),
        sa.Column("source_reference", sa.String(200), nullable=True),
        sa.Column("evento", sa.String(120), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("severidad", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=False, server_default="0.5"),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("procesada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_proactive_signals_org", "proactive_signals", ["organization_id"])
    op.create_index("ix_signal_dedupe", "proactive_signals", ["organization_id", "dedupe_key"])

    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("dominio", sa.String(60), nullable=False),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("proactive_signals.id"), nullable=True),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("contexto_json", sa.Text(), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("impacto_estimado", sa.Numeric(18, 4), nullable=True),
        sa.Column("urgencia", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("riesgo", sa.String(20), nullable=False, server_default="MEDIO"),
        sa.Column("probabilidad", sa.Numeric(5, 4), nullable=True),
        sa.Column("esfuerzo", sa.String(20), nullable=False, server_default="MEDIO"),
        sa.Column("costo_estimado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_potencial", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_potencial_certidumbre", sa.String(30), nullable=False, server_default="ESTIMADO"),
        sa.Column("valor_materializado", sa.Numeric(18, 4), nullable=True),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=False, server_default="0.5"),
        sa.Column("pertinencia", sa.String(30), nullable=True),
        sa.Column("pertinencia_razon", sa.Text(), nullable=True),
        sa.Column("momento", sa.String(30), nullable=True),
        sa.Column("prioridad_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("prioridad_componentes_json", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(40), nullable=False, server_default="DETECTADA"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("equipo_json", sa.Text(), nullable=True),
        sa.Column("siguiente_accion_json", sa.Text(), nullable=True),
        sa.Column("work_plan_id", sa.String(36), sa.ForeignKey("work_plans.id"), nullable=True),
        sa.Column("operation_id", sa.String(36), nullable=True),
        sa.Column("finops_reference", sa.String(200), nullable=True),
        sa.Column("atribucion_nivel", sa.String(30), nullable=True),
        sa.Column("atribucion_razon", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("fecha_deteccion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_revaluacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resultado_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opportunities_org", "opportunities", ["organization_id"])
    op.create_index("ix_opportunities_estado", "opportunities", ["estado"])
    op.create_index("ix_opportunities_codigo", "opportunities", ["codigo"])

    op.create_table(
        "opportunity_transitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("estado_anterior", sa.String(40), nullable=False),
        sa.Column("estado_nuevo", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("evidencia_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opp_trans_opp", "opportunity_transitions", ["opportunity_id"])

    op.create_table(
        "opportunity_tracking",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("accion", sa.String(200), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("bloqueo", sa.Text(), nullable=True),
        sa.Column("kpi_inicial_json", sa.Text(), nullable=True),
        sa.Column("kpi_objetivo_json", sa.Text(), nullable=True),
        sa.Column("kpi_actual_json", sa.Text(), nullable=True),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("escalamiento", sa.String(200), nullable=True),
        sa.Column("proxima_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opp_track_opp", "opportunity_tracking", ["opportunity_id"])

    op.create_table(
        "opportunity_traces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("signal_id", sa.String(36), sa.ForeignKey("proactive_signals.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("etapa", sa.String(60), nullable=False),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opp_trace_corr", "opportunity_traces", ["correlation_id"])

    # G-02: vincular FINOPS con oportunidad
    with op.batch_alter_table("finops_values") as batch_op:
        batch_op.add_column(sa.Column("opportunity_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_finops_values_opportunity", ["opportunity_id"])
        batch_op.create_foreign_key(
            "fk_finops_values_opportunity_id",
            "opportunities",
            ["opportunity_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("finops_values") as batch_op:
        batch_op.drop_constraint("fk_finops_values_opportunity_id", type_="foreignkey")
        batch_op.drop_index("ix_finops_values_opportunity")
        batch_op.drop_column("opportunity_id")

    op.drop_table("opportunity_traces")
    op.drop_table("opportunity_tracking")
    op.drop_table("opportunity_transitions")
    op.drop_table("opportunities")
    op.drop_table("proactive_signals")
