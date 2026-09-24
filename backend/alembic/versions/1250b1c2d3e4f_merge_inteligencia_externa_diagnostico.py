"""Merge heads 1220 (diagnóstico transversal) y 1240 (inteligencia externa) — bloque 1250B."""

from typing import Sequence, Union

from alembic import op

revision: str = "1250b1c2d3e4f"
down_revision: Union[str, Sequence[str], None] = ("1220a1b2c3d4e", "1240c3d4e5f6a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
