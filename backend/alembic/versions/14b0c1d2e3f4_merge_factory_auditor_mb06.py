"""Merge heads MB-06 fábrica + Auditor MVP.

Revision ID: 14b0c1d2e3f4
Revises: 6b06a1b2c3d4e, 1400a1b2c3d4e
"""

from typing import Sequence, Union

revision: str = "14b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = ("6b06a1b2c3d4e", "1400a1b2c3d4e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
