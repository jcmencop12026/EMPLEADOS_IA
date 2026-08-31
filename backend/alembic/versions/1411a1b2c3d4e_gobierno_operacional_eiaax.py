"""Alembic — Gobierno operacional EIAAX (acciones, aprobaciones, visibilidad, IA)."""

from alembic import op
import sqlalchemy as sa

revision = "1411a1b2c3d4e"
down_revision = "1420a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gobierno_accion_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo_accion", sa.String(20), nullable=False),
        sa.Column("recurso_tipo", sa.String(60), nullable=True),
        sa.Column("criticidad", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("requiere_aprobacion_humana", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rol_aprobador", sa.String(60), nullable=True),
        sa.Column("capacidad_externa", sa.String(120), nullable=True),
        sa.Column("empleado_ia_id", sa.String(36), sa.ForeignKey("ai_employees.id"), nullable=True),
        sa.Column("auto_ejecutar", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gob_pol_org", "gobierno_accion_policies", ["organization_id"])
    op.create_index("ix_gob_pol_tipo", "gobierno_accion_policies", ["tipo_accion"])

    op.create_table(
        "gobierno_accion_solicitudes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("tipo_accion", sa.String(20), nullable=False),
        sa.Column("recurso_tipo", sa.String(60), nullable=False),
        sa.Column("recurso_id", sa.String(36), nullable=True),
        sa.Column("criticidad", sa.String(20), nullable=False, server_default="MEDIUM"),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="SOLICITADA"),
        sa.Column("actor_tipo", sa.String(20), nullable=False, server_default="HUMANO"),
        sa.Column("solicitado_por", sa.String(36), nullable=False),
        sa.Column("aprobado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rechazado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("motivo_solicitud", sa.Text(), nullable=True),
        sa.Column("motivo_decision", sa.Text(), nullable=True),
        sa.Column("approval_request_id", sa.String(36), sa.ForeignKey("approval_requests.id"), nullable=True),
        sa.Column("resultado_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_gob_sol_org", "gobierno_accion_solicitudes", ["organization_id"])
    op.create_index("ix_gob_sol_estado", "gobierno_accion_solicitudes", ["estado"])
    op.create_index("ix_gob_sol_corr", "gobierno_accion_solicitudes", ["correlation_id"])

    op.create_table(
        "gobierno_visibilidad_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dominio", sa.String(40), nullable=False),
        sa.Column("contexto_id", sa.String(36), nullable=True),
        sa.Column("objeto_tipo", sa.String(40), nullable=False),
        sa.Column("objeto_id", sa.String(36), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False),
        sa.Column("changed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gob_vis_org", "gobierno_visibilidad_log", ["organization_id"])
    op.create_index("ix_gob_vis_dom", "gobierno_visibilidad_log", ["dominio", "contexto_id"])

    op.create_table(
        "gobierno_ia_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("proveedores_permitidos_json", sa.Text(), nullable=True),
        sa.Column("modelos_permitidos_json", sa.Text(), nullable=True),
        sa.Column("acciones_permitidas_json", sa.Text(), nullable=True),
        sa.Column("herramientas_permitidas_json", sa.Text(), nullable=True),
        sa.Column("limites_json", sa.Text(), nullable=True),
        sa.Column("requiere_aprobacion_humana_json", sa.Text(), nullable=True),
        sa.Column("datos_permitidos_json", sa.Text(), nullable=True),
        sa.Column("auto_ejecutar", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gob_ia_org", "gobierno_ia_policies", ["organization_id"])

    op.create_table(
        "gobierno_eventos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("actor_tipo", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("accion", sa.String(120), nullable=False),
        sa.Column("recurso_tipo", sa.String(60), nullable=True),
        sa.Column("recurso_id", sa.String(36), nullable=True),
        sa.Column("decision", sa.String(40), nullable=True),
        sa.Column("aprobacion_id", sa.String(36), sa.ForeignKey("gobierno_accion_solicitudes.id"), nullable=True),
        sa.Column("resultado", sa.String(40), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gob_evt_org", "gobierno_eventos", ["organization_id"])
    op.create_index("ix_gob_evt_corr", "gobierno_eventos", ["correlation_id"])


def downgrade() -> None:
    op.drop_table("gobierno_eventos")
    op.drop_table("gobierno_ia_policies")
    op.drop_table("gobierno_visibilidad_log")
    op.drop_table("gobierno_accion_solicitudes")
    op.drop_table("gobierno_accion_policies")
