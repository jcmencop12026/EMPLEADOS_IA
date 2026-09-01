"""Alembic — Capa transversal seguridad, gobierno de datos y trazabilidad EIAAX."""

from alembic import op
import sqlalchemy as sa

revision = "1610a1b2c3d4e"
down_revision = "1600a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "empresa_objeto_clasificacion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("objeto_tipo", sa.String(60), nullable=False),
        sa.Column("objeto_id", sa.String(36), nullable=False),
        sa.Column("classification_level_id", sa.String(36), sa.ForeignKey("gov_classification_levels.id"), nullable=False),
        sa.Column("asignado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("catalog_entry_id", sa.String(36), sa.ForeignKey("gov_catalog_entries.id"), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "objeto_tipo", "objeto_id", name="uq_emp_cls_obj"),
    )
    op.create_index("ix_emp_cls_org", "empresa_objeto_clasificacion", ["organization_id"])
    op.create_index("ix_emp_cls_tipo", "empresa_objeto_clasificacion", ["objeto_tipo", "objeto_id"])

    op.create_table(
        "empresa_evidencia_vinculo",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo_evidencia", sa.String(40), nullable=False),
        sa.Column("referencia", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("objeto_tipo", sa.String(60), nullable=False),
        sa.Column("objeto_id", sa.String(36), nullable=False),
        sa.Column("rol_vinculo", sa.String(40), nullable=False, server_default="SOPORTE"),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("creado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emp_evid_org", "empresa_evidencia_vinculo", ["organization_id"])
    op.create_index("ix_emp_evid_obj", "empresa_evidencia_vinculo", ["objeto_tipo", "objeto_id"])
    op.create_index("ix_emp_evid_corr", "empresa_evidencia_vinculo", ["correlation_id"])

    with op.batch_alter_table("gobierno_visibilidad_log") as batch_op:
        batch_op.add_column(sa.Column("nivel_visibilidad", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("estado_anterior", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("motivo", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("version", sa.Integer(), nullable=True))

    with op.batch_alter_table("gobierno_ia_policies") as batch_op:
        batch_op.add_column(sa.Column("trazabilidad_obligatoria", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("catalogo_proveedores_ref", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("registro_detalle_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("gobierno_ia_policies") as batch_op:
        batch_op.drop_column("registro_detalle_json")
        batch_op.drop_column("catalogo_proveedores_ref")
        batch_op.drop_column("trazabilidad_obligatoria")

    with op.batch_alter_table("gobierno_visibilidad_log") as batch_op:
        batch_op.drop_column("version")
        batch_op.drop_column("motivo")
        batch_op.drop_column("estado_anterior")
        batch_op.drop_column("nivel_visibilidad")

    op.drop_table("empresa_evidencia_vinculo")
    op.drop_table("empresa_objeto_clasificacion")
