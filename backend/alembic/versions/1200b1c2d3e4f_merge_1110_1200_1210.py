"""Merge heads 1210 (valoración) y 1200 (línea base) — base 1280."""

from typing import Sequence, Union

from alembic import op

revision: str = "1200b1c2d3e4f"
down_revision: Union[str, Sequence[str], None] = ("1210b2c3d4e5f", "1200a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
