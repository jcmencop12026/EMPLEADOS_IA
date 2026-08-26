"""Merge Alembic: conocimiento 930 + integración salud/operaciones 970.

Revision ID: 971a1b2c3d4e
Revises: 930a1, 970a1b2c3d4e
Create Date: 2026-08-26 01:30:00.000000
"""

from typing import Sequence, Union

revision: str = "971a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = ("930a1", "970a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
