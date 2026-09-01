"""Alembic — Arquitecto de Transformación Empresarial (1420)."""

from alembic import op
import sqlalchemy as sa

revision = "1730a1b2c3d4e"
down_revision = "1720a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dossier_empresarial",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("etapa_actual", sa.String(30), nullable=False, server_default="PROSPECTO"),
        sa.Column("sector", sa.String(120), nullable=True),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column("confianza_global", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("porcentaje_completitud", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expediente_activo_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", name="uq_dossier_org"),
    )

    op.create_table(
        "dossier_conocimiento_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("campo", sa.String(80), nullable=False),
        sa.Column("etiqueta", sa.String(200), nullable=False),
        sa.Column("valor", sa.Text(), nullable=True),
        sa.Column("fuente", sa.String(40), nullable=False),
        sa.Column("calidad", sa.String(10), nullable=False),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("explicacion_calidad", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "dossier_mapa_nodos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("dossier_mapa_nodos.id"), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "dossier_causas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("dossier_causas.id"), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("explicacion_confianza", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "transformacion_alternativas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("causa_id", sa.String(36), sa.ForeignKey("dossier_causas.id"), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("impacto", sa.String(10), nullable=False),
        sa.Column("costo", sa.String(10), nullable=False),
        sa.Column("esfuerzo", sa.String(10), nullable=False),
        sa.Column("riesgo", sa.String(10), nullable=False),
        sa.Column("tiempo", sa.String(40), nullable=True),
        sa.Column("complejidad", sa.String(10), nullable=False),
        sa.Column("reversibilidad", sa.String(10), nullable=False),
        sa.Column("madurez", sa.String(10), nullable=False),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("score_total", sa.Integer(), nullable=False),
        sa.Column("scores_json", sa.Text(), nullable=True),
        sa.Column("recomendada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "transformacion_iniciativas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("alternativa_id", sa.String(36), sa.ForeignKey("transformacion_alternativas.id"), nullable=True),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("clasificacion", sa.String(20), nullable=False),
        sa.Column("prioridad_score", sa.Integer(), nullable=False),
        sa.Column("impacto_vs_esfuerzo_json", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "transformacion_escenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("proyeccion_json", sa.Text(), nullable=True),
        sa.Column("es_proyectado", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "empleado_ia_requerimientos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("iniciativa_id", sa.String(36), sa.ForeignKey("transformacion_iniciativas.id"), nullable=True),
        sa.Column("alternativa_id", sa.String(36), sa.ForeignKey("transformacion_alternativas.id"), nullable=True),
        sa.Column("objetivo", sa.Text(), nullable=False),
        sa.Column("responsabilidad", sa.Text(), nullable=True),
        sa.Column("entradas_json", sa.Text(), nullable=True),
        sa.Column("salidas_json", sa.Text(), nullable=True),
        sa.Column("herramientas_json", sa.Text(), nullable=True),
        sa.Column("frecuencia", sa.String(40), nullable=True),
        sa.Column("riesgo", sa.String(10), nullable=False),
        sa.Column("supervision", sa.Text(), nullable=True),
        sa.Column("indicadores_json", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "capacidad_externa_necesidades",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dossier_id", sa.String(36), sa.ForeignKey("dossier_empresarial.id"), nullable=False),
        sa.Column("alternativa_id", sa.String(36), sa.ForeignKey("transformacion_alternativas.id"), nullable=True),
        sa.Column("necesidad_empresarial", sa.Text(), nullable=False),
        sa.Column("contrato_json", sa.Text(), nullable=True),
        sa.Column("confianza", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("capacidad_externa_necesidades")
    op.drop_table("empleado_ia_requerimientos")
    op.drop_table("transformacion_escenarios")
    op.drop_table("transformacion_iniciativas")
    op.drop_table("transformacion_alternativas")
    op.drop_table("dossier_causas")
    op.drop_table("dossier_mapa_nodos")
    op.drop_table("dossier_conocimiento_items")
    op.drop_table("dossier_empresarial")
