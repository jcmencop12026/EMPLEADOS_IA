"""Migración 1710 — Centro de Negocios: PDF, aprobaciones, contratos, sync."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1710a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1700a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("negocio_proposal_extensions", sa.Column("precio_presentado", sa.Numeric(18, 4), nullable=True))
    op.add_column("negocio_proposal_extensions", sa.Column("precio_contratado", sa.Numeric(18, 4), nullable=True))
    op.add_column("negocio_proposal_extensions", sa.Column("approval_policy_json", sa.Text(), nullable=True))
    op.add_column("negocio_proposal_extensions", sa.Column("sync_revision", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "negocio_approval_policies",
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), primary_key=True),
        sa.Column("levels_json", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "negocio_approval_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("nivel", sa.String(40), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_appr_prop", "negocio_approval_records", ["proposal_id"])

    op.create_table(
        "negocio_proposal_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("negocio_proposal_versions.id"), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(80), nullable=False, server_default="application/pdf"),
        sa.Column("content_sha256", sa.String(64), nullable=True),
        sa.Column("content_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("generated_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_doc_prop", "negocio_proposal_documents", ["proposal_id"])

    op.add_column("negocio_proposal_versions", sa.Column("pdf_document_id", sa.String(36), nullable=True))
    op.add_column("negocio_proposal_versions", sa.Column("presented_by_id", sa.String(36), nullable=True))
    op.add_column("negocio_proposal_versions", sa.Column("approved_by_id", sa.String(36), nullable=True))
    op.add_column("negocio_proposal_versions", sa.Column("precio_presentado", sa.Numeric(18, 4), nullable=True))
    op.create_foreign_key(
        "fk_negocio_ver_pdf_doc",
        "negocio_proposal_versions",
        "negocio_proposal_documents",
        ["pdf_document_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_negocio_ver_presented_by",
        "negocio_proposal_versions",
        "users",
        ["presented_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_negocio_ver_approved_by",
        "negocio_proposal_versions",
        "users",
        ["approved_by_id"],
        ["id"],
    )

    op.create_table(
        "negocio_contract_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("negocio_proposal_versions.id"), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("negocio_proposal_documents.id"), nullable=True),
        sa.Column("precio_contratado", sa.Numeric(18, 4), nullable=True),
        sa.Column("modelo_comercial", sa.String(40), nullable=True),
        sa.Column("condiciones", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("proximo_paso", sa.String(500), nullable=True),
        sa.Column("fecha_contratacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_negocio_contract_prop", "negocio_contract_records", ["proposal_id"])

    op.create_table(
        "negocio_sync_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("direction", sa.String(30), nullable=False),
        sa.Column("field_name", sa.String(80), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_sync_prop", "negocio_sync_log", ["proposal_id"])

    op.create_table(
        "negocio_price_phase_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("fase", sa.String(20), nullable=False),
        sa.Column("monto", sa.Numeric(18, 4), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_negocio_price_phase_prop", "negocio_price_phase_records", ["proposal_id"])


def downgrade() -> None:
    op.drop_index("ix_negocio_price_phase_prop", table_name="negocio_price_phase_records")
    op.drop_table("negocio_price_phase_records")
    op.drop_index("ix_negocio_sync_prop", table_name="negocio_sync_log")
    op.drop_table("negocio_sync_log")
    op.drop_index("ix_negocio_contract_prop", table_name="negocio_contract_records")
    op.drop_table("negocio_contract_records")
    op.drop_constraint("fk_negocio_ver_approved_by", "negocio_proposal_versions", type_="foreignkey")
    op.drop_constraint("fk_negocio_ver_presented_by", "negocio_proposal_versions", type_="foreignkey")
    op.drop_constraint("fk_negocio_ver_pdf_doc", "negocio_proposal_versions", type_="foreignkey")
    op.drop_column("negocio_proposal_versions", "precio_presentado")
    op.drop_column("negocio_proposal_versions", "approved_by_id")
    op.drop_column("negocio_proposal_versions", "presented_by_id")
    op.drop_column("negocio_proposal_versions", "pdf_document_id")
    op.drop_index("ix_negocio_doc_prop", table_name="negocio_proposal_documents")
    op.drop_table("negocio_proposal_documents")
    op.drop_index("ix_negocio_appr_prop", table_name="negocio_approval_records")
    op.drop_table("negocio_approval_records")
    op.drop_table("negocio_approval_policies")
    op.drop_column("negocio_proposal_extensions", "sync_revision")
    op.drop_column("negocio_proposal_extensions", "approval_policy_json")
    op.drop_column("negocio_proposal_extensions", "precio_contratado")
    op.drop_column("negocio_proposal_extensions", "precio_presentado")
