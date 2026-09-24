"""Migración 1700 — Centro de Negocios EIAAX."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1700a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1610a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "negocio_proposal_extensions",
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("evaluacion_id", sa.String(36), nullable=True),
        sa.Column("modelo_comercial", sa.String(40), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("proximo_paso", sa.String(500), nullable=True),
        sa.Column("version_actual", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("perspectivas_json", sa.Text(), nullable=True),
        sa.Column("documento_cliente_json", sa.Text(), nullable=True),
        sa.Column("documento_interno_json", sa.Text(), nullable=True),
        sa.Column("ia_consumo_json", sa.Text(), nullable=True),
        sa.Column("economic_recommendation_id", sa.String(36), sa.ForeignKey("economic_price_recommendations.id"), nullable=True),
        sa.Column("implementacion_proyecto_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_ext_org", "negocio_proposal_extensions", ["organization_id"])
    op.create_index("ix_negocio_ext_opp", "negocio_proposal_extensions", ["opportunity_id"])

    op.create_table(
        "negocio_proposal_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(40), nullable=False),
        sa.Column("estado_comercial", sa.String(30), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("documento_cliente_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_ver_prop", "negocio_proposal_versions", ["proposal_id"])

    op.create_table(
        "negocio_negotiation_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_presentada", sa.Integer(), nullable=True),
        sa.Column("fecha_presentacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interlocutor", sa.String(200), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("cambios_solicitados", sa.Text(), nullable=True),
        sa.Column("nueva_version_id", sa.String(36), sa.ForeignKey("negocio_proposal_versions.id"), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="ABIERTA"),
        sa.Column("proximo_paso", sa.String(500), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_neg_prop", "negocio_negotiation_entries", ["proposal_id"])

    op.create_table(
        "negocio_price_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("economic_price_recommendations.id"), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("precio_recomendado", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_decidido", sa.Numeric(18, 4), nullable=True),
        sa.Column("justificacion", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("negocio_price_decisions")
    op.drop_table("negocio_negotiation_entries")
    op.drop_table("negocio_proposal_versions")
    op.drop_table("negocio_proposal_extensions")
