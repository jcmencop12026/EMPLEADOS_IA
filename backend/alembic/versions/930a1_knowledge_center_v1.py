"""Centro de Conocimiento V1 — CONOCIMIENTO-930

Revision ID: 930a1
Revises: 5b2eb2437398
"""
from alembic import op
import sqlalchemy as sa

revision = "930a1"
down_revision = "5b2eb2437398"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=True),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("original_filename", sa.String(260), nullable=True),
        sa.Column("storage_key", sa.String(400), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("processed_content", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("association_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_knowledge_documents_org", "knowledge_documents", ["organization_id"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(200), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_chunks_document", "knowledge_chunks", ["document_id"])
    op.create_index("ix_knowledge_chunks_org", "knowledge_chunks", ["organization_id"])

    op.create_table(
        "knowledge_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_activities_document", "knowledge_activities", ["document_id"])

    op.create_table(
        "employee_knowledge_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("knowledge_documents.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("employee_id", "document_id", name="uq_employee_knowledge_grant"),
    )
    op.create_index("ix_employee_knowledge_grants_employee", "employee_knowledge_grants", ["employee_id"])
    op.create_index("ix_employee_knowledge_grants_document", "employee_knowledge_grants", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_employee_knowledge_grants_document", table_name="employee_knowledge_grants")
    op.drop_index("ix_employee_knowledge_grants_employee", table_name="employee_knowledge_grants")
    op.drop_table("employee_knowledge_grants")
    op.drop_index("ix_knowledge_activities_document", table_name="knowledge_activities")
    op.drop_table("knowledge_activities")
    op.drop_index("ix_knowledge_chunks_org", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_document", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_index("ix_knowledge_documents_status", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_org", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
