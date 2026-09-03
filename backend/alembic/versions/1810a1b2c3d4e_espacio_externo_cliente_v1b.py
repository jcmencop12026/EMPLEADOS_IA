"""Migración 1810 — Espacio externo V1b: cliente contratado y audiencia."""

from alembic import op
import sqlalchemy as sa

revision = "1810a1b2c3d4e"
down_revision = "1800a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("entidades_empresa") as batch:
        batch.add_column(sa.Column("proyecto_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("capacidades_contrato_json", sa.Text(), nullable=True))
    op.create_index("ix_entidad_empresa_proyecto", "entidades_empresa", ["proyecto_id"])

    with op.batch_alter_table("empresa_publicaciones") as batch:
        batch.add_column(sa.Column("audiencia", sa.String(30), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("empresa_publicaciones") as batch:
        batch.drop_column("audiencia")
    op.drop_index("ix_entidad_empresa_proyecto", table_name="entidades_empresa")
    with op.batch_alter_table("entidades_empresa") as batch:
        batch.drop_column("capacidades_contrato_json")
        batch.drop_column("proyecto_id")
