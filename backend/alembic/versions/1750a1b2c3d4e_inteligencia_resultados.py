"""Alembic — Inteligencia de resultados EIAAX (1410)."""

from alembic import op
import sqlalchemy as sa

revision = "1750a1b2c3d4e"
down_revision = "1740a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resultados_indicadores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("definicion", sa.Text(), nullable=True),
        sa.Column("unidad", sa.String(40), nullable=False, server_default="unidad"),
        sa.Column("fuente", sa.String(80), nullable=False, server_default="MANUAL"),
        sa.Column("dimension_json", sa.Text(), nullable=True),
        sa.Column("periodo", sa.String(40), nullable=True),
        sa.Column("valor_antes", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_proyectado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_real", sa.Numeric(18, 4), nullable=True),
        sa.Column("meta", sa.Numeric(18, 4), nullable=True),
        sa.Column("fecha_medicion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidencia_ref", sa.String(300), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("calidad", sa.String(40), nullable=True),
        sa.Column("tipo_analitica", sa.String(20), nullable=False, server_default="DESCRIPTIVA"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("linea_base_id", sa.String(36), sa.ForeignKey("lineas_base.id"), nullable=True),
        sa.Column("proceso", sa.String(120), nullable=True),
        sa.Column("visible_entidad", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notas_internas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_res_ind_org", "resultados_indicadores", ["organization_id"])
    op.create_index("ix_res_ind_exp", "resultados_indicadores", ["expediente_id"])

    op.create_table(
        "resultados_informes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False, server_default="IMPACTO"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("visibilidad", sa.String(20), nullable=False, server_default="INTERNO"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("contenido_json", sa.Text(), nullable=False),
        sa.Column("narrativa", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "resultados_evidencias",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("indicador_id", sa.String(36), sa.ForeignKey("resultados_indicadores.id"), nullable=True),
        sa.Column("informe_id", sa.String(36), sa.ForeignKey("resultados_informes.id"), nullable=True),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fuente", sa.String(80), nullable=False, server_default="MANUAL"),
        sa.Column("referencia", sa.String(300), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "resultados_plan_acciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("indicador_id", sa.String(36), sa.ForeignKey("resultados_indicadores.id"), nullable=True),
        sa.Column("causa", sa.Text(), nullable=True),
        sa.Column("accion", sa.Text(), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_meta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("evidencia_ref", sa.String(300), nullable=True),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("seguimiento_notas", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "resultados_dimension_nodos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("indicador_id", sa.String(36), sa.ForeignKey("resultados_indicadores.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("resultados_dimension_nodos.id"), nullable=True),
        sa.Column("nivel", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("codigo", sa.String(80), nullable=False),
        sa.Column("etiqueta", sa.String(200), nullable=False),
        sa.Column("valor", sa.Numeric(18, 4), nullable=True),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("resultados_dimension_nodos")
    op.drop_table("resultados_plan_acciones")
    op.drop_table("resultados_evidencias")
    op.drop_table("resultados_informes")
    op.drop_table("resultados_indicadores")
