"""execution_fence_810c

Revision ID: b810c2f3e4d5
Revises: a810f1c2d3e4
Create Date: 2026-08-24 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b810c2f3e4d5"
down_revision: Union[str, Sequence[str], None] = "a810f1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("automation_runs") as batch_op:
        batch_op.add_column(
            sa.Column("execution_generation", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    with op.batch_alter_table("automation_runs") as batch_op:
        batch_op.drop_column("execution_generation")
