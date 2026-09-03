"""1740 — Inteligencia económica: runs de escenarios comparativos.

Revision ID: 1740a1b2c3d4e
Revises: 1730a1b2c3d4e
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1740a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1730a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "economic_scenario_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("scope_type", sa.String(30), nullable=False, server_default="ORGANIZACION"),
        sa.Column("scope_id", sa.String(36), nullable=True),
        sa.Column("params_json", sa.Text(), nullable=True),
        sa.Column("resultados_json", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )
    op.create_index("ix_economic_scenario_runs_org", "economic_scenario_runs", ["organization_id"])
    op.create_index("ix_economic_scenario_runs_scope", "economic_scenario_runs", ["scope_id"])


def downgrade() -> None:
    op.drop_index("ix_economic_scenario_runs_scope", table_name="economic_scenario_runs")
    op.drop_index("ix_economic_scenario_runs_org", table_name="economic_scenario_runs")
    op.drop_table("economic_scenario_runs")
