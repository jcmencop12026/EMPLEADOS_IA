"""Alembic — Valor interno/externo y captura comercial (1280b)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1280b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "1280a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commercial_proposal_values",
        sa.Column("alcance", sa.String(20), nullable=False, server_default="INTERNO"),
    )
    op.add_column(
        "commercial_proposal_values",
        sa.Column("external_intelligence_ref", sa.String(120), nullable=True),
    )
    op.add_column(
        "commercial_proposals",
        sa.Column("pct_valor_capturado_empleados_ia", sa.Numeric(7, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("commercial_proposals", "pct_valor_capturado_empleados_ia")
    op.drop_column("commercial_proposal_values", "external_intelligence_ref")
    op.drop_column("commercial_proposal_values", "alcance")
