"""merge centro control integrado 1250c

Revision ID: 1250c1a2b3c4d
Revises: 1200a1b2c3d4e, 1210b2c3d4e5f, 1220a1b2c3d4e
Create Date: 2026-08-29

Unifica cabezas paralelas de bloques 1200, 1110/1210 y 1120/1220 para integración 1250C.
"""

from typing import Sequence, Union

revision: str = "1250c1a2b3c4d"
down_revision: Union[str, Sequence[str], None] = ("1200a1b2c3d4e", "1210b2c3d4e5f", "1220a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
