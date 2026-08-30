"""Alembic — Enlace conector integraciones ↔ catálogo gobierno (WIRING-01)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1330b1b2c3d4f"
down_revision: Union[str, Sequence[str], None] = "1330a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("integration_connectors", schema=None) as batch_op:
        batch_op.add_column(sa.Column("gov_catalog_entry_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_integration_connectors_gov_catalog",
            "gov_catalog_entries",
            ["gov_catalog_entry_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_integration_connectors_gov_catalog_entry_id",
            ["gov_catalog_entry_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("integration_connectors", schema=None) as batch_op:
        batch_op.drop_index("ix_integration_connectors_gov_catalog_entry_id")
        batch_op.drop_constraint("fk_integration_connectors_gov_catalog", type_="foreignkey")
        batch_op.drop_column("gov_catalog_entry_id")
