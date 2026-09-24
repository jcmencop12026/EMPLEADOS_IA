"""Alembic — Expediente de evaluación empresarial EIAAX (1405)."""

from alembic import op
import sqlalchemy as sa

revision = "1405a1b2c3d4e"
down_revision = "1341a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluaciones_expediente",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("entidad_nombre", sa.String(200), nullable=False),
        sa.Column("entidad_ref", sa.String(120), nullable=True),
        sa.Column("necesidad", sa.Text(), nullable=True),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("area_proceso", sa.String(120), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="BORRADOR"),
        sa.Column("nivel", sa.String(20), nullable=False, server_default="PRELIMINAR"),
        sa.Column("confianza_global", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("porcentaje_informacion", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valor_potencial", sa.String(40), nullable=True),
        sa.Column("diagnostic_id", sa.String(36), sa.ForeignKey("diagnostics.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notas_internas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_eval_exp_org_codigo"),
    )
    op.create_index("ix_eval_exp_org", "evaluaciones_expediente", ["organization_id"])
    op.create_index("ix_eval_exp_estado", "evaluaciones_expediente", ["estado"])

    op.create_table(
        "evaluaciones_informacion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("campo", sa.String(80), nullable=False),
        sa.Column("etiqueta", sa.String(200), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("obligatorio", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("por_que", sa.Text(), nullable=True),
        sa.Column("impacto_precision", sa.Text(), nullable=True),
        sa.Column("respuesta", sa.Text(), nullable=True),
        sa.Column("evidencia_ref", sa.String(300), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("expediente_id", "campo", name="uq_eval_info_exp_campo"),
    )

    op.create_table(
        "evaluaciones_hallazgos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("tipo_contenido", sa.String(20), nullable=False, server_default="HECHO"),
        sa.Column("confianza", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("explicacion_confianza", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("origen", sa.Text(), nullable=True),
        sa.Column("impacto_resumen", sa.Text(), nullable=True),
        sa.Column("visible_entidad", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("es_problema_original", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("diagnostic_finding_id", sa.String(36), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_hall_visible", "evaluaciones_hallazgos", ["visible_entidad"])

    op.create_table(
        "evaluaciones_oportunidad_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("rol", sa.String(20), nullable=False, server_default="VINCULADA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("expediente_id", "opportunity_id", name="uq_eval_opp_link"),
    )

    op.create_table(
        "evaluaciones_visibilidad_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("objeto_tipo", sa.String(40), nullable=False),
        sa.Column("objeto_id", sa.String(36), nullable=False),
        sa.Column("visible_entidad", sa.Boolean(), nullable=False),
        sa.Column("changed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluaciones_visibilidad_log")
    op.drop_table("evaluaciones_oportunidad_links")
    op.drop_table("evaluaciones_hallazgos")
    op.drop_table("evaluaciones_informacion")
    op.drop_table("evaluaciones_expediente")
