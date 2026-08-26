"""merge operaciones 940 + salud 960

Revision ID: 970a1b2c3d4e
Revises: 940a1b2c3d4e, 960a1b2c3d4e
Create Date: 2026-08-25 22:00:00.000000
"""

from typing import Sequence, Union

revision: str = "970a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = ("940a1b2c3d4e", "960a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
