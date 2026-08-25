"""workplan priority and due date — OPERACIONES-940

Revision ID: 940a1b2c3d4e
Revises: 5b2eb2437398
Create Date: 2026-08-25
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "940a1b2c3d4e"
down_revision: Union[str, None] = "5b2eb2437398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "work_plans",
        sa.Column("prioridad", sa.String(length=20), nullable=False, server_default="MEDIA"),
    )
    op.add_column(
        "work_plans",
        sa.Column("vencimiento", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_work_plans_prioridad", "work_plans", ["prioridad"])
    op.create_index("ix_work_plans_vencimiento", "work_plans", ["vencimiento"])


def downgrade() -> None:
    op.drop_index("ix_work_plans_vencimiento", table_name="work_plans")
    op.drop_index("ix_work_plans_prioridad", table_name="work_plans")
    op.drop_column("work_plans", "vencimiento")
    op.drop_column("work_plans", "prioridad")
