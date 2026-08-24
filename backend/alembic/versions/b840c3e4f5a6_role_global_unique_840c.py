"""role_global_unique_840c

Revision ID: b840c3e4f5a6
Revises: a840c4d5e6f7
Create Date: 2026-08-24 18:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b840c3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a840c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "sqlite":
        rows = conn.execute(
            sa.text(
                """
                SELECT code, GROUP_CONCAT(id) AS ids, COUNT(*) AS cnt
                FROM roles
                WHERE organization_id IS NULL
                GROUP BY code
                HAVING cnt > 1
                """
            )
        ).fetchall()
        for row in rows:
            ids = str(row.ids).split(",")
            for duplicate_id in ids[1:]:
                conn.execute(sa.text("DELETE FROM roles WHERE id = :id"), {"id": duplicate_id})
        conn.execute(
            sa.text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_global_code "
                "ON roles (code) WHERE organization_id IS NULL"
            )
        )
    else:
        conn.execute(
            sa.text(
                """
                DELETE FROM roles r
                USING roles r2
                WHERE r.organization_id IS NULL
                  AND r2.organization_id IS NULL
                  AND r.code = r2.code
                  AND r.created_at > r2.created_at
                """
            )
        )
        op.create_index(
            "uq_roles_global_code",
            "roles",
            ["code"],
            unique=True,
            postgresql_where=sa.text("organization_id IS NULL"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == "sqlite":
        conn.execute(sa.text("DROP INDEX IF EXISTS uq_roles_global_code"))
    else:
        op.drop_index("uq_roles_global_code", table_name="roles")
