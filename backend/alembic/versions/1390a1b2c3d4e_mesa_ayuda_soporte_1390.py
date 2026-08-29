"""Alembic — Mesa de Ayuda y Soporte (MB-12 / 1390)."""

from alembic import op
import sqlalchemy as sa

revision = "1390a1b2c3d4e"
down_revision = "1330b1b2c3d4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "support_sla_policies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("prioridad", sa.String(length=20), nullable=False, server_default="MEDIA"),
        sa.Column("minutos_primera_respuesta", sa.Integer(), nullable=True),
        sa.Column("minutos_resolucion", sa.Integer(), nullable=True),
        sa.Column("horario_servicio_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "nombre", name="uq_support_sla_org_nombre"),
    )
    op.create_index("ix_support_sla_org", "support_sla_policies", ["organization_id"])

    op.create_table(
        "support_cases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("categoria", sa.String(length=80), nullable=True),
        sa.Column("asunto", sa.String(length=300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("prioridad", sa.String(length=20), nullable=False, server_default="MEDIA"),
        sa.Column("impacto", sa.String(length=20), nullable=False, server_default="MEDIO"),
        sa.Column("urgencia", sa.String(length=20), nullable=False, server_default="MEDIA"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="NUEVO"),
        sa.Column("solicitante_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("grupo", sa.String(length=80), nullable=True),
        sa.Column("modulo_relacionado", sa.String(length=60), nullable=True),
        sa.Column("entidad_relacionada", sa.String(length=120), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("origen", sa.String(length=20), nullable=False, server_default="MANUAL"),
        sa.Column("origen_tipo", sa.String(length=60), nullable=True),
        sa.Column("origen_id", sa.String(length=120), nullable=True),
        sa.Column("resolucion", sa.Text(), nullable=True),
        sa.Column("sla_policy_id", sa.String(length=36), sa.ForeignKey("support_sla_policies.id"), nullable=True),
        sa.Column("primera_respuesta_limite", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolucion_limite", sa.DateTime(timezone=True), nullable=True),
        sa.Column("primera_respuesta_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_limite", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resuelto_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cerrado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidencia_ref", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "numero", name="uq_support_case_org_numero"),
    )
    op.create_index("ix_support_cases_org", "support_cases", ["organization_id"])
    op.create_index("ix_support_cases_estado", "support_cases", ["estado"])
    op.create_index("ix_support_cases_corr", "support_cases", ["correlation_id"])

    op.create_table(
        "support_case_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_support_history_case", "support_case_history", ["case_id"])

    op.create_table(
        "support_case_comments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("es_interno", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("evidencia_ref", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_support_comments_case", "support_case_comments", ["case_id"])

    op.create_table(
        "support_auto_dedup",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=False),
        sa.Column("origen_tipo", sa.String(length=60), nullable=False),
        sa.Column("origen_id", sa.String(length=120), nullable=False),
        sa.Column("ventana_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "dedup_key", name="uq_support_dedup_org_key"),
    )
    op.create_index("ix_support_dedup_org", "support_auto_dedup", ["organization_id"])


def downgrade() -> None:
    op.drop_table("support_auto_dedup")
    op.drop_table("support_case_comments")
    op.drop_table("support_case_history")
    op.drop_table("support_cases")
    op.drop_table("support_sla_policies")
