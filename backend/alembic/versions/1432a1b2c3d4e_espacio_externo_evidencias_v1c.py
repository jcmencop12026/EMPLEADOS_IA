"""Alembic — Espacio externo V1c: evidencias/adjuntos versionados."""

from alembic import op
import sqlalchemy as sa

revision = "1432a1b2c3d4e"
down_revision = "1431a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("evaluacion_entregas_externas") as batch:
        batch.add_column(sa.Column("observacion_publica", sa.Text(), nullable=True))
        batch.add_column(sa.Column("observacion_interna", sa.Text(), nullable=True))

    op.create_table(
        "evaluacion_entrega_adjuntos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("entidad_id", sa.String(36), sa.ForeignKey("entidades_empresa.id"), nullable=False),
        sa.Column("entrega_id", sa.String(36), sa.ForeignKey("evaluacion_entregas_externas.id"), nullable=False),
        sa.Column("informacion_item_id", sa.String(36), sa.ForeignKey("evaluaciones_informacion.id"), nullable=True),
        sa.Column("grupo_archivo", sa.String(36), nullable=False),
        sa.Column("reemplaza_id", sa.String(36), sa.ForeignKey("evaluacion_entrega_adjuntos.id"), nullable=True),
        sa.Column("nombre_original", sa.String(260), nullable=False),
        sa.Column("nombre_sanitizado", sa.String(260), nullable=False),
        sa.Column("extension", sa.String(20), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(400), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("es_version_actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("estado", sa.String(30), nullable=False, server_default="RECIBIDO"),
        sa.Column("observacion", sa.Text(), nullable=True),
        sa.Column("observacion_interna", sa.Text(), nullable=True),
        sa.Column("fuente_tipo", sa.String(30), nullable=True),
        sa.Column("subido_por", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_adjunto_entrega", "evaluacion_entrega_adjuntos", ["entrega_id", "es_version_actual"])
    op.create_index("ix_adjunto_expediente", "evaluacion_entrega_adjuntos", ["expediente_id", "created_at"])
    op.create_index("ix_adjunto_org", "evaluacion_entrega_adjuntos", ["organization_id"])
    op.create_index("ix_adjunto_grupo", "evaluacion_entrega_adjuntos", ["grupo_archivo"])


def downgrade() -> None:
    op.drop_index("ix_adjunto_grupo", table_name="evaluacion_entrega_adjuntos")
    op.drop_index("ix_adjunto_org", table_name="evaluacion_entrega_adjuntos")
    op.drop_index("ix_adjunto_expediente", table_name="evaluacion_entrega_adjuntos")
    op.drop_index("ix_adjunto_entrega", table_name="evaluacion_entrega_adjuntos")
    op.drop_table("evaluacion_entrega_adjuntos")
    with op.batch_alter_table("evaluacion_entregas_externas") as batch:
        batch.drop_column("observacion_interna")
        batch.drop_column("observacion_publica")
