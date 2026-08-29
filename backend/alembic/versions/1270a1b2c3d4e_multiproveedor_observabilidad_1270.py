"""multiproveedor observabilidad 1270

Revision ID: 1270a1b2c3d4e
Revises: 1210b2c3d4e5f
Create Date: 2026-08-29

Catálogo de modelos y políticas de enrutamiento IA.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1270a1b2c3d4e"
down_revision: Union[str, None] = "1210b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_model_catalog",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider_type", sa.String(length=40), nullable=False),
        sa.Column("model_id", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="HABILITADO"),
        sa.Column("capabilities_json", sa.Text(), nullable=True),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("modalities_json", sa.Text(), nullable=True),
        sa.Column("cost_hint_json", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_llm_model_catalog_org", "llm_model_catalog", ["organization_id"])
    op.create_index("ix_llm_model_catalog_provider", "llm_model_catalog", ["provider_type"])

    op.create_table(
        "llm_routing_policies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("preferred_provider", sa.String(length=40), nullable=True),
        sa.Column("preferred_model", sa.String(length=120), nullable=True),
        sa.Column("required_capability", sa.String(length=60), nullable=True),
        sa.Column("fallback_allowed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_cost_per_1k_tokens", sa.Float(), nullable=True),
        sa.Column("credential_scope", sa.String(length=30), nullable=False, server_default="ORGANIZACION"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_llm_routing_policies_org", "llm_routing_policies", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_llm_routing_policies_org", table_name="llm_routing_policies")
    op.drop_table("llm_routing_policies")
    op.drop_index("ix_llm_model_catalog_provider", table_name="llm_model_catalog")
    op.drop_index("ix_llm_model_catalog_org", table_name="llm_model_catalog")
    op.drop_table("llm_model_catalog")
