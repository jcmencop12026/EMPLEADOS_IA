"""Alembic — Presentación ejecutiva real e informes comerciales (1430)."""

from alembic import op
import sqlalchemy as sa

revision = "1430a1b2c3d4e"
down_revision = "1420a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "presentacion_publicacion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("estado", sa.String(40), nullable=False, server_default="PRIVADO"),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("actualizado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("publicado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "expediente_id", name="uq_pres_pub_org_exp"),
    )
    op.create_index("ix_pres_pub_org_estado", "presentacion_publicacion", ["organization_id", "estado"])

    op.create_table(
        "informes_comerciales_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("audiencia", sa.String(30), nullable=False, server_default="GERENCIA"),
        sa.Column("periodicidad", sa.String(20), nullable=False, server_default="MENSUAL"),
        sa.Column("destinatarios_json", sa.Text(), nullable=True),
        sa.Column("resumen", sa.Text(), nullable=True),
        sa.Column("enlace_seguro", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("comm_rule_id", sa.String(36), sa.ForeignKey("comm_rules.id"), nullable=True),
        sa.Column("ultimo_envio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proximo_envio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PENDIENTE_INTEGRACION"),
        sa.Column("error_ultimo", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inf_com_org_activo", "informes_comerciales_config", ["organization_id", "activo"])


def downgrade() -> None:
    op.drop_index("ix_inf_com_org_activo", table_name="informes_comerciales_config")
    op.drop_table("informes_comerciales_config")
    op.drop_index("ix_pres_pub_org_estado", table_name="presentacion_publicacion")
    op.drop_table("presentacion_publicacion")
