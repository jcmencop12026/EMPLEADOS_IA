"""Alembic — Bloque Producto 2: capacidades externas, acciones PIIAX prep (1410)."""

from alembic import op
import sqlalchemy as sa

revision = "1410a1b2c3d4e"
down_revision = "1405a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluaciones_acciones_externas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("capacidad", sa.String(40), nullable=False),
        sa.Column("tipo_accion", sa.String(20), nullable=False, server_default="LECTURA"),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="BORRADOR"),
        sa.Column("requiere_aprobacion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aprobado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rechazo_motivo", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=False),
        sa.Column("referencia_externa", sa.String(120), nullable=True),
        sa.Column("resultado_resumen", sa.Text(), nullable=True),
        sa.Column("evidencia_ref", sa.Text(), nullable=True),
        sa.Column("error_mensaje", sa.Text(), nullable=True),
        sa.Column("parametros_json", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_acc_exp", "evaluaciones_acciones_externas", ["expediente_id", "created_at"])
    op.create_index("ix_eval_acc_corr", "evaluaciones_acciones_externas", ["correlation_id"])
    op.create_index("ix_eval_acc_estado", "evaluaciones_acciones_externas", ["estado"])

    op.create_table(
        "evaluaciones_accion_eventos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("accion_id", sa.String(36), sa.ForeignKey("evaluaciones_acciones_externas.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("tipo_evento", sa.String(40), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evaluaciones_indicadores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expediente_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("hallazgo_id", sa.String(36), sa.ForeignKey("evaluaciones_hallazgos.id"), nullable=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("valor_antes", sa.String(80), nullable=True),
        sa.Column("valor_proyectado", sa.String(80), nullable=True),
        sa.Column("valor_real", sa.String(80), nullable=True),
        sa.Column("fuente", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("visible_entidad", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_eval_ind_exp", "evaluaciones_indicadores", ["expediente_id", "nombre"])


def downgrade() -> None:
    op.drop_table("evaluaciones_indicadores")
    op.drop_table("evaluaciones_accion_eventos")
    op.drop_table("evaluaciones_acciones_externas")
