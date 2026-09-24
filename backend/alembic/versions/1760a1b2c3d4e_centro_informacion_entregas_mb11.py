"""Alembic — Entregas de informes y referencias MB-11 EIAAX (1420)."""

from alembic import op
import sqlalchemy as sa

revision = "1760a1b2c3d4e"
down_revision = "1750a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comm_entregas_informe",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("informe_id", sa.String(36), sa.ForeignKey("resultados_informes.id"), nullable=False),
        sa.Column("informe_version", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("comm_messages.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=True),
        sa.Column("destinatario_tipo", sa.String(30), nullable=False),
        sa.Column("destinatario_id", sa.String(120), nullable=True),
        sa.Column("visibilidad_entrega", sa.String(20), nullable=False, server_default="VISIBLE_ENTIDAD"),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comm_ent_inf_org", "comm_entregas_informe", ["organization_id"])
    op.create_index("ix_comm_ent_inf_informe", "comm_entregas_informe", ["informe_id", "informe_version"])

    op.add_column("comm_messages", sa.Column("referencias_json", sa.Text(), nullable=True))
    op.add_column("comm_messages", sa.Column("prioridad", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("comm_messages", "prioridad")
    op.drop_column("comm_messages", "referencias_json")
    op.drop_table("comm_entregas_informe")
