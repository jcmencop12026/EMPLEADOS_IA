"""Alembic — MB-03 Partners / Aliados comerciales (1410)."""

from alembic import op
import sqlalchemy as sa

revision = "1410a1b2c3d4e"
down_revision = "1405a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partners",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("razon_social", sa.String(300), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("tipo_relacion", sa.String(40), nullable=False, server_default="CONSULTOR"),
        sa.Column("contacto_nombre", sa.String(200), nullable=True),
        sa.Column("contacto_email", sa.String(200), nullable=True),
        sa.Column("contacto_telefono", sa.String(40), nullable=True),
        sa.Column("alcance_descripcion", sa.Text(), nullable=True),
        sa.Column("notas_internas", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("codigo", name="uq_partner_codigo"),
    )
    op.create_index("ix_partners_estado", "partners", ["estado"])

    op.create_table(
        "partner_organization_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("alcance_json", sa.Text(), nullable=False),
        sa.Column("permisos_json", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("granted_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("partner_id", "organization_id", name="uq_partner_org_grant"),
    )

    op.create_table(
        "partner_user_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False, server_default="OPERADOR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assigned_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("partner_id", "user_id", name="uq_partner_user"),
    )

    op.create_table(
        "partner_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_partner_audit_partner", "partner_audit_events", ["partner_id"])


def downgrade() -> None:
    op.drop_table("partner_audit_events")
    op.drop_table("partner_user_memberships")
    op.drop_table("partner_organization_grants")
    op.drop_table("partners")
