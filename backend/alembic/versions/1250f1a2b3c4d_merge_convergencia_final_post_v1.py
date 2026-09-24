"""Merge convergencia final post-V1 (1250A + 1250B).

Revision ID: 1250f1a2b3c4d
Revises: 1250a1b2c3d4e, 1250b1c2d3e4f
Create Date: 2026-08-29

Unifica cabezas de convergencia 1250A (bloques 1100-1220) y 1250B
(inteligencia externa 1240 + diagnóstico extendido).
"""

from typing import Sequence, Union

revision: str = "1250f1a2b3c4d"
down_revision: Union[str, Sequence[str], None] = ("1250a1b2c3d4e", "1250b1c2d3e4f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
