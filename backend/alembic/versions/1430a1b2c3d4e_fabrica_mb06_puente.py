"""Alembic — MB-06 Fábrica puente Arquitecto y trazabilidad (1430).

NOTA INTEGRACIÓN: revisiones 1410 y 1420 colisionan con otras ramas (Partners, BP2).
Esta migración usa identificador propio 1430a1b2c3d4e sobre down_revision 1420 de esta rama.
"""

from alembic import op
import sqlalchemy as sa

revision = "1430a1b2c3d4e"
down_revision = "1420a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_employees", sa.Column("source_type", sa.String(40), nullable=True))
    op.add_column("ai_employees", sa.Column("source_ref", sa.String(36), nullable=True))
    op.add_column("ai_employees", sa.Column("requerimiento_id", sa.String(36), nullable=True))
    op.add_column("ai_employees", sa.Column("dossier_id", sa.String(36), nullable=True))
    op.add_column("ai_employees", sa.Column("autonomy_level", sa.String(30), nullable=False, server_default="SUPERVISADO"))
    op.add_column("ai_employees", sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_ai_employees_source_type", "ai_employees", ["source_type"])

    op.add_column("empleado_ia_requerimientos", sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True))
    op.add_column("empleado_ia_requerimientos", sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"))

    op.create_table(
        "employee_business_capabilities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("employee_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("operation_class", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("employee_business_capabilities")
    op.drop_column("empleado_ia_requerimientos", "estado")
    op.drop_column("empleado_ia_requerimientos", "employee_id")
    op.drop_index("ix_ai_employees_source_type", "ai_employees")
    op.drop_column("ai_employees", "is_template")
    op.drop_column("ai_employees", "autonomy_level")
    op.drop_column("ai_employees", "dossier_id")
    op.drop_column("ai_employees", "requerimiento_id")
    op.drop_column("ai_employees", "source_ref")
    op.drop_column("ai_employees", "source_type")
