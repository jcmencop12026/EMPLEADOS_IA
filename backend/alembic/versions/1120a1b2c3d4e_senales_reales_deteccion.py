"""Migración 1120 — Fuentes y señales reales para detección proactiva."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1120a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signal_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tipo_fuente", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("configuracion_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_signal_sources_org", "signal_sources", ["organization_id"])
    op.create_index("ix_signal_sources_org_code", "signal_sources", ["organization_id", "code"], unique=True)

    with op.batch_alter_table("proactive_signals") as batch_op:
        batch_op.add_column(sa.Column("source_id", sa.String(36), sa.ForeignKey("signal_sources.id"), nullable=True))
        batch_op.add_column(sa.Column("modo_ingesta", sa.String(20), nullable=False, server_default="REAL"))
        batch_op.add_column(sa.Column("proceso", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("metrica", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("valor_metrica", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("unidad", sa.String(40), nullable=True))
        batch_op.add_column(sa.Column("dimension", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("evidencia_resumen", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("estado_procesamiento", sa.String(30), nullable=False, server_default="RECIBIDA"))
        batch_op.add_column(sa.Column("rejection_reason", sa.String(300), nullable=True))
        batch_op.add_column(sa.Column("signal_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_signal_source_ref", "proactive_signals", ["organization_id", "source_id"])
    op.create_index("ix_signal_modo_ingesta", "proactive_signals", ["organization_id", "modo_ingesta"])
    op.create_index("ix_signal_estado_proc", "proactive_signals", ["organization_id", "estado_procesamiento"])


def downgrade() -> None:
    op.drop_index("ix_signal_estado_proc", table_name="proactive_signals")
    op.drop_index("ix_signal_modo_ingesta", table_name="proactive_signals")
    op.drop_index("ix_signal_source_ref", table_name="proactive_signals")
    with op.batch_alter_table("proactive_signals") as batch_op:
        batch_op.drop_column("signal_at")
        batch_op.drop_column("rejection_reason")
        batch_op.drop_column("estado_procesamiento")
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("evidencia_resumen")
        batch_op.drop_column("dimension")
        batch_op.drop_column("unidad")
        batch_op.drop_column("valor_metrica")
        batch_op.drop_column("metrica")
        batch_op.drop_column("proceso")
        batch_op.drop_column("modo_ingesta")
        batch_op.drop_column("source_id")
    op.drop_index("ix_signal_sources_org_code", table_name="signal_sources")
    op.drop_index("ix_signal_sources_org", table_name="signal_sources")
    op.drop_table("signal_sources")
