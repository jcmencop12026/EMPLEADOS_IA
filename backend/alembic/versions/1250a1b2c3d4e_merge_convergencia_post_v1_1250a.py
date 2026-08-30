"""Merge Alembic: convergencia post-V1 fase 1 (bloque 1250A).

Unifica heads paralelos de línea base (1200), valoración (1210) y
diagnóstico transversal (1220) tras integración controlada.

Revision ID: 1250a1b2c3d4e
Revises: 1200a1b2c3d4e, 1210b2c3d4e5f, 1220a1b2c3d4e
Create Date: 2026-08-29 02:30:00.000000
"""

from typing import Sequence, Union

revision: str = "1250a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = (
    "1200a1b2c3d4e",
    "1210b2c3d4e5f",
    "1220a1b2c3d4e",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
