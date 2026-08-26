"""Merge Alembic: preintegración consolidada 002.

Unifica heads de scheduler, notificaciones, administración, capacidades,
FINOPS y stack SALUD/Operaciones/Conocimiento.

Revision ID: 972a1b2c3d4e
Revises: 820a2, 971a1b2c3d4e, a850c4d5e6f8, b810c2f3e4d5, b840c3e4f5a6, c950a1b2c3d4
Create Date: 2026-08-26 11:00:00.000000
"""

from typing import Sequence, Union

revision: str = "972a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = (
    "820a2",
    "971a1b2c3d4e",
    "a850c4d5e6f8",
    "b810c2f3e4d5",
    "b840c3e4f5a6",
    "c950a1b2c3d4",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
