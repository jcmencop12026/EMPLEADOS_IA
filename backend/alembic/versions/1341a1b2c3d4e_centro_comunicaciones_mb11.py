"""Alembic — Centro de Información y Comunicaciones (MB-11 / 1341)."""

from alembic import op
import sqlalchemy as sa

revision = "1341a1b2c3d4e"
down_revision = "1507a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comm_channels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("secret_ref", sa.String(200), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("prioridad", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("uso_permitido", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "nombre", name="uq_comm_channel_org_nombre"),
    )
    op.create_table(
        "comm_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(60), nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("tipo_comunicacion", sa.String(60), nullable=False),
        sa.Column("canal_tipo", sa.String(40), nullable=False),
        sa.Column("idioma", sa.String(10), nullable=False, server_default="es"),
        sa.Column("current_version_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_comm_template_org_codigo"),
    )
    op.create_table(
        "comm_template_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_id", sa.String(36), sa.ForeignKey("comm_templates.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("asunto", sa.String(300), nullable=True),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("variables_json", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVA"),
        sa.Column("vigencia_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vigencia_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creador_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("template_id", "version", name="uq_comm_template_version"),
    )
    op.create_table(
        "comm_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("condicion_json", sa.Text(), nullable=True),
        sa.Column("destinatario_tipo", sa.String(30), nullable=False),
        sa.Column("destinatario_regla", sa.String(120), nullable=False),
        sa.Column("template_version_id", sa.String(36), sa.ForeignKey("comm_template_versions.id"), nullable=False),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("comm_channels.id"), nullable=False),
        sa.Column("accion", sa.String(30), nullable=False, server_default="ENVIAR"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("antispam_minutos", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("obligatoria", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "comm_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="BORRADOR"),
        sa.Column("tipo_comunicacion", sa.String(60), nullable=False),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("comm_channels.id"), nullable=True),
        sa.Column("template_version_id", sa.String(36), sa.ForeignKey("comm_template_versions.id"), nullable=True),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("comm_rules.id"), nullable=True),
        sa.Column("destinatario_tipo", sa.String(30), nullable=False),
        sa.Column("destinatario_id", sa.String(120), nullable=True),
        sa.Column("destinatario_externo", sa.String(300), nullable=True),
        sa.Column("asunto", sa.String(300), nullable=True),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("idioma", sa.String(10), nullable=False, server_default="es"),
        sa.Column("programada_para", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("event_id", sa.String(128), nullable=True),
        sa.Column("origen", sa.String(30), nullable=False, server_default="MANUAL"),
        sa.Column("origen_id", sa.String(120), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_intentos", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("proximo_intento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("creador_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enviada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entregada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelada_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_comm_msg_idempotency"),
    )
    op.create_index("ix_comm_messages_org", "comm_messages", ["organization_id"])
    op.create_index("ix_comm_messages_estado", "comm_messages", ["estado"])
    op.create_table(
        "comm_delivery_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("comm_messages.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("intento_num", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("causa", sa.String(120), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "comm_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("canales_json", sa.Text(), nullable=True),
        sa.Column("tipos_json", sa.Text(), nullable=True),
        sa.Column("horario_json", sa.Text(), nullable=True),
        sa.Column("idioma", sa.String(10), nullable=False, server_default="es"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_comm_pref_org_user"),
    )
    op.create_table(
        "comm_dedup",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dedup_key", sa.String(128), nullable=False),
        sa.Column("message_id", sa.String(36), sa.ForeignKey("comm_messages.id"), nullable=False),
        sa.Column("ventana_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "dedup_key", name="uq_comm_dedup_org_key"),
    )


def downgrade() -> None:
    op.drop_table("comm_dedup")
    op.drop_table("comm_preferences")
    op.drop_table("comm_delivery_attempts")
    op.drop_index("ix_comm_messages_estado", table_name="comm_messages")
    op.drop_index("ix_comm_messages_org", table_name="comm_messages")
    op.drop_table("comm_messages")
    op.drop_table("comm_rules")
    op.drop_table("comm_template_versions")
    op.drop_table("comm_templates")
    op.drop_table("comm_channels")
