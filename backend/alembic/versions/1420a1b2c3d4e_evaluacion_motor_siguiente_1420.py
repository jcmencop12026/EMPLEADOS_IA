"""Alembic — Bloque Producto 2 ampliado: motor siguiente acción y proveedor (1420)."""

from alembic import op
import sqlalchemy as sa

revision = "1420a1b2c3d4e"
down_revision = "1410a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evaluaciones_expediente",
        sa.Column("siguiente_accion_json", sa.Text(), nullable=True),
    )
    op.add_column(
        "evaluaciones_acciones_externas",
        sa.Column("proveedor_codigo", sa.String(40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluaciones_acciones_externas", "proveedor_codigo")
    op.drop_column("evaluaciones_expediente", "siguiente_accion_json")
