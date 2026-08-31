"""multitenant_organization_slug_v1

Revision ID: c1a2b3c4d5e6
Revises: 1030a1b2c3d4e
Create Date: 2026-08-28 16:45:00.000000

"""
from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "1030a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str, org_id: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (name or "empresa").lower()).strip("-")[:60]
    if not base:
        base = "empresa"
    return f"{base}-{org_id[:8]}"


def upgrade() -> None:
    op.add_column("organizations", sa.Column("slug", sa.String(length=80), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, name FROM organizations")).fetchall()
    used: set[str] = set()
    for org_id, name in rows:
        candidate = _slugify(name or "empresa", org_id)
        slug = candidate
        suffix = 1
        while slug in used:
            slug = f"{candidate}-{suffix}"
            suffix += 1
        used.add(slug)
        conn.execute(
            sa.text("UPDATE organizations SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": org_id},
        )
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.alter_column("slug", nullable=False)
        batch_op.create_index("ix_organizations_slug", ["slug"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_index("ix_organizations_slug")
        batch_op.drop_column("slug")
