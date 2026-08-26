"""administration_840

Revision ID: a840c4d5e6f7
Revises: 5b2eb2437398
Create Date: 2026-08-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a840c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "5b2eb2437398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("status", sa.String(length=30), server_default="ACTIVE", nullable=False))
    op.add_column("organizations", sa.Column("timezone", sa.String(length=64), server_default="America/Bogota", nullable=False))
    op.add_column("organizations", sa.Column("config_json", sa.Text(), nullable=True))
    op.add_column("organizations", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("users", sa.Column("email", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("full_name", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("status", sa.String(length=30), server_default="ACTIVE", nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("created_by_id", sa.String(length=36), nullable=True))
    op.add_column("users", sa.Column("updated_by_id", sa.String(length=36), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table("users") as batch_op:
        batch_op.create_foreign_key("fk_users_created_by", "users", ["created_by_id"], ["id"])
        batch_op.create_foreign_key("fk_users_updated_by", "users", ["updated_by_id"], ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("module", sa.String(length=60), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "code", name="uq_role_org_code"),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")
    op.drop_index("ix_roles_organization_id", table_name="roles")
    op.drop_table("roles")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_users_email", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_updated_by", type_="foreignkey")
        batch_op.drop_constraint("fk_users_created_by", type_="foreignkey")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "updated_by_id")
    op.drop_column("users", "created_by_id")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "status")
    op.drop_column("users", "full_name")
    op.drop_column("users", "email")
    op.drop_column("organizations", "updated_at")
    op.drop_column("organizations", "config_json")
    op.drop_column("organizations", "timezone")
    op.drop_column("organizations", "status")
