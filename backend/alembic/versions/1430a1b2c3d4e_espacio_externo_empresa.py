"""Espacio externo controlado — empresa/prospecto/cliente V1."""

from alembic import op
import sqlalchemy as sa

revision = "1430a1b2c3d4e"
down_revision = "1420a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entidades_empresa",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("contacto_email", sa.String(200), nullable=True),
        sa.Column("estado_relacion", sa.String(30), nullable=False, server_default="PROSPECTO_EVALUACION"),
        sa.Column("contrato_ref", sa.String(120), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "expediente_id", name="uq_entidad_expediente"),
    )
    op.create_index("ix_entidades_empresa_org", "entidades_empresa", ["organization_id"])
    op.create_index("ix_entidades_empresa_exp", "entidades_empresa", ["expediente_id"])
    op.create_index("ix_entidades_empresa_estado", "entidades_empresa", ["estado_relacion"])

    op.create_table(
        "entidades_empresa_acceso",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("entidad_id", sa.String(36), sa.ForeignKey("entidades_empresa.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rol_externo", sa.String(20), nullable=False, server_default="PROSPECTO"),
        sa.Column("capacidades_json", sa.Text, nullable=True),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("invited_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("entidad_id", "user_id", name="uq_entidad_user_acceso"),
    )
    op.create_index("ix_entidad_acceso_user", "entidades_empresa_acceso", ["user_id"])
    op.create_index("ix_entidad_acceso_activo", "entidades_empresa_acceso", ["activo"])

    op.create_table(
        "empresa_publicaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("entidad_id", sa.String(36), sa.ForeignKey("entidades_empresa.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("paquete", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PRIVADO"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("destinatario", sa.String(300), nullable=True),
        sa.Column("snapshot_hash", sa.String(64), nullable=True),
        sa.Column("publicado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("publicado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_pub_exp_paquete", "empresa_publicaciones", ["expediente_id", "paquete"])

    op.create_table(
        "empresa_publicacion_historial",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("publicacion_id", sa.String(36), sa.ForeignKey("empresa_publicaciones.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("estado_anterior", sa.String(30), nullable=True),
        sa.Column("estado_nuevo", sa.String(30), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("destinatario", sa.String(300), nullable=True),
        sa.Column("motivo", sa.Text, nullable=True),
        sa.Column("changed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_pub_hist_pub", "empresa_publicacion_historial", ["publicacion_id"])

    op.create_table(
        "evaluacion_entregas_externas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("entidad_id", sa.String(36), sa.ForeignKey("entidades_empresa.id"), nullable=False),
        sa.Column("informacion_item_id", sa.String(36), sa.ForeignKey("evaluaciones_informacion.id"), nullable=True),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="SOLICITADO"),
        sa.Column("fuente_tipo", sa.String(30), nullable=True),
        sa.Column("contenido", sa.Text, nullable=True),
        sa.Column("evidencia_ref", sa.String(300), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("solicitado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entregado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("solicitado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entregado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suficiencia_minima_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
    )
    op.create_index("ix_entrega_ext_exp", "evaluacion_entregas_externas", ["expediente_id", "solicitado_at"])

    with op.batch_alter_table("evaluaciones_informacion") as batch:
        batch.add_column(sa.Column("fuente_tipo", sa.String(30), nullable=True))
        batch.add_column(sa.Column("estado_validacion", sa.String(30), nullable=True))
        batch.add_column(sa.Column("entregado_por", sa.String(36), nullable=True))
        batch.add_column(sa.Column("entregado_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("validado_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("suficiencia_minima_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("evaluaciones_informacion") as batch:
        batch.drop_column("suficiencia_minima_at")
        batch.drop_column("validado_at")
        batch.drop_column("entregado_at")
        batch.drop_column("entregado_por")
        batch.drop_column("estado_validacion")
        batch.drop_column("fuente_tipo")
    op.drop_table("evaluacion_entregas_externas")
    op.drop_table("empresa_publicacion_historial")
    op.drop_table("empresa_publicaciones")
    op.drop_table("entidades_empresa_acceso")
    op.drop_table("entidades_empresa")
