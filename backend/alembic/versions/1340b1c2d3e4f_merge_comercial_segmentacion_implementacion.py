"""Alembic — Unión segmentación (1310) e implementación (1340)."""

from typing import Sequence, Union

revision: str = "1340b1c2d3e4f"
down_revision: Union[str, Sequence[str], None] = ("1310a1b2c3d4e", "1340a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
