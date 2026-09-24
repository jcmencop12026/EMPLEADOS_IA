"""Merge Alembic 1350 gobierno de datos + 1360 continuidad (convergencia fase 1)."""

from typing import Sequence, Union

from alembic import op

revision: str = "1365a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = ("1350a1b2c3d4e", "1360a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
