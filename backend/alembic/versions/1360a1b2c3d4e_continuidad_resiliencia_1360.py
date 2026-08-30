"""Alembic — Continuidad operativa y resiliencia (1360)."""

from alembic import op
import sqlalchemy as sa

revision = "1360a1b2c3d4e"
down_revision = "1250f1a2b3c4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cont_servicios_criticos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False, server_default="OTRO"),
        sa.Column("criticidad", sa.String(length=10), nullable=False, server_default="MEDIA"),
        sa.Column("justificacion_criticidad", sa.Text(), nullable=True),
        sa.Column("rto_valor", sa.Numeric(10, 2), nullable=True),
        sa.Column("rto_unidad", sa.String(length=20), nullable=True),
        sa.Column("rpo_valor", sa.Numeric(10, 2), nullable=True),
        sa.Column("rpo_unidad", sa.String(length=20), nullable=True),
        sa.Column("proveedor_ref", sa.String(length=120), nullable=True),
        sa.Column("estado_operacional", sa.String(length=20), nullable=False, server_default="DESCONOCIDO"),
        sa.Column("ultima_comprobacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_cont_servicio_org_codigo"),
    )
    op.create_index("ix_cont_servicios_org", "cont_servicios_criticos", ["organization_id"])

    op.create_table(
        "cont_dependencias",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_origen_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("servicio_destino_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False, server_default="REQUIERE"),
        sa.Column("critica", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_dependencias_org", "cont_dependencias", ["organization_id"])

    op.create_table(
        "cont_planes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("nombre", sa.String(length=300), nullable=False),
        sa.Column("alcance", sa.Text(), nullable=True),
        sa.Column("servicios_json", sa.Text(), nullable=True),
        sa.Column("responsables_json", sa.Text(), nullable=True),
        sa.Column("riesgos_json", sa.Text(), nullable=True),
        sa.Column("activadores", sa.Text(), nullable=True),
        sa.Column("rto_valor", sa.Numeric(10, 2), nullable=True),
        sa.Column("rto_unidad", sa.String(length=20), nullable=True),
        sa.Column("rpo_valor", sa.Numeric(10, 2), nullable=True),
        sa.Column("rpo_unidad", sa.String(length=20), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="BORRADOR"),
        sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_cont_plan_org_codigo"),
    )
    op.create_index("ix_cont_planes_org", "cont_planes", ["organization_id"])

    op.create_table(
        "cont_backup_politicas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=True),
        sa.Column("recurso", sa.String(length=200), nullable=False),
        sa.Column("frecuencia", sa.String(length=30), nullable=False, server_default="DIARIA"),
        sa.Column("retencion_dias", sa.Integer(), nullable=True),
        sa.Column("ubicacion_logica", sa.String(length=200), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False, server_default="COMPLETO"),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("cifrado_requerido", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("verificacion_requerida", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PROGRAMADO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_backup_pol_org", "cont_backup_politicas", ["organization_id"])

    op.create_table(
        "cont_backup_ejecuciones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("politica_id", sa.String(length=36), sa.ForeignKey("cont_backup_politicas.id"), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurso", sa.String(length=200), nullable=False),
        sa.Column("estado_registro", sa.String(length=20), nullable=False, server_default="EJECUTADO"),
        sa.Column("resultado", sa.String(length=20), nullable=False, server_default="EXITOSO"),
        sa.Column("tamano_bytes", sa.Integer(), nullable=True),
        sa.Column("hash_referencia", sa.String(length=128), nullable=True),
        sa.Column("ubicacion_logica", sa.String(length=200), nullable=True),
        sa.Column("error_seguro", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_backup_ej_org", "cont_backup_ejecuciones", ["organization_id"])
    op.create_index("ix_cont_backup_ej_pol", "cont_backup_ejecuciones", ["politica_id"])

    op.create_table(
        "cont_backup_verificaciones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ejecucion_id", sa.String(length=36), sa.ForeignKey("cont_backup_ejecuciones.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("existe", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tamano_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("integridad_ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("verificado_por", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_restore_pruebas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("ejecucion_id", sa.String(length=36), sa.ForeignKey("cont_backup_ejecuciones.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="SIMULADA"),
        sa.Column("entorno_destino", sa.String(length=100), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracion_minutos", sa.Numeric(10, 2), nullable=True),
        sa.Column("resultado", sa.String(length=20), nullable=False, server_default="EXITOSO"),
        sa.Column("datos_validados", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_incidentes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=True),
        sa.Column("severidad", sa.String(length=10), nullable=False, server_default="SEV3"),
        sa.Column("titulo", sa.String(length=300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("impacto_json", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="DETECTADO"),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deteccion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recuperacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("causa", sa.Text(), nullable=True),
        sa.Column("causa_raiz_tipo", sa.String(length=20), nullable=True),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("cont_planes.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_incidentes_org", "cont_incidentes", ["organization_id"])
    op.create_index("ix_cont_incidentes_estado", "cont_incidentes", ["estado"])

    op.create_table(
        "cont_contingencia_activaciones",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("cont_planes.id"), nullable=False),
        sa.Column("incidente_id", sa.String(length=36), sa.ForeignKey("cont_incidentes.id"), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("acciones_activadas_json", sa.Text(), nullable=True),
        sa.Column("autorizado_por", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_modo_degradado",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("funciones_continuan_json", sa.Text(), nullable=True),
        sa.Column("funciones_bloqueadas_json", sa.Text(), nullable=True),
        sa.Column("funciones_limitadas_json", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_fallbacks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("proveedor_principal_ref", sa.String(length=120), nullable=True),
        sa.Column("proveedor_alternativo_ref", sa.String(length=120), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_slos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("objetivo_pct", sa.Numeric(7, 4), nullable=False),
        sa.Column("medido_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("periodo", sa.String(length=20), nullable=True),
        sa.Column("incumplido", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_disponibilidad",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=False),
        sa.Column("periodo", sa.String(length=20), nullable=False),
        sa.Column("tiempo_disponible_min", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tiempo_caido_min", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("disponibilidad_pct", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_escalamientos",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("severidad", sa.String(length=10), nullable=False),
        sa.Column("nivel", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("tiempo_max_min", sa.Integer(), nullable=True),
        sa.Column("siguiente_nivel", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_runbooks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("servicio_id", sa.String(length=36), sa.ForeignKey("cont_servicios_criticos.id"), nullable=True),
        sa.Column("nombre", sa.String(length=300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("pasos_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_pruebas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("cont_planes.id"), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("escenario", sa.String(length=100), nullable=False),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("resultado", sa.String(length=30), nullable=True),
        sa.Column("rto_obtenido", sa.Numeric(10, 2), nullable=True),
        sa.Column("rpo_obtenido", sa.Numeric(10, 2), nullable=True),
        sa.Column("hallazgos", sa.Text(), nullable=True),
        sa.Column("acciones_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_post_incidentes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("incidente_id", sa.String(length=36), sa.ForeignKey("cont_incidentes.id"), nullable=False),
        sa.Column("que_ocurrio", sa.Text(), nullable=True),
        sa.Column("impacto", sa.Text(), nullable=True),
        sa.Column("causa", sa.Text(), nullable=True),
        sa.Column("causa_raiz_tipo", sa.String(length=20), nullable=False, server_default="NO_DETERMINADA"),
        sa.Column("que_funciono", sa.Text(), nullable=True),
        sa.Column("que_fallo", sa.Text(), nullable=True),
        sa.Column("aprendizaje_ref", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_acciones_correctivas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("post_incidente_id", sa.String(length=36), sa.ForeignKey("cont_post_incidentes.id"), nullable=True),
        sa.Column("incidente_id", sa.String(length=36), sa.ForeignKey("cont_incidentes.id"), nullable=True),
        sa.Column("accion", sa.Text(), nullable=False),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("prioridad", sa.String(length=10), nullable=False, server_default="MEDIA"),
        sa.Column("fecha_objetivo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cont_alertas",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("severidad", sa.String(length=20), nullable=False, server_default="MEDIA"),
        sa.Column("entidad_ref", sa.String(length=120), nullable=True),
        sa.Column("resuelta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_alertas_org", "cont_alertas", ["organization_id"])

    op.create_table(
        "cont_auditoria",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("accion", sa.String(length=60), nullable=False),
        sa.Column("entidad", sa.String(length=60), nullable=False),
        sa.Column("entidad_id", sa.String(length=36), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cont_auditoria_org", "cont_auditoria", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_cont_auditoria_org", table_name="cont_auditoria")
    op.drop_table("cont_auditoria")
    op.drop_index("ix_cont_alertas_org", table_name="cont_alertas")
    op.drop_table("cont_alertas")
    op.drop_table("cont_acciones_correctivas")
    op.drop_table("cont_post_incidentes")
    op.drop_table("cont_pruebas")
    op.drop_table("cont_runbooks")
    op.drop_table("cont_escalamientos")
    op.drop_table("cont_disponibilidad")
    op.drop_table("cont_slos")
    op.drop_table("cont_fallbacks")
    op.drop_table("cont_modo_degradado")
    op.drop_table("cont_contingencia_activaciones")
    op.drop_index("ix_cont_incidentes_estado", table_name="cont_incidentes")
    op.drop_index("ix_cont_incidentes_org", table_name="cont_incidentes")
    op.drop_table("cont_incidentes")
    op.drop_table("cont_restore_pruebas")
    op.drop_table("cont_backup_verificaciones")
    op.drop_index("ix_cont_backup_ej_pol", table_name="cont_backup_ejecuciones")
    op.drop_index("ix_cont_backup_ej_org", table_name="cont_backup_ejecuciones")
    op.drop_table("cont_backup_ejecuciones")
    op.drop_index("ix_cont_backup_pol_org", table_name="cont_backup_politicas")
    op.drop_table("cont_backup_politicas")
    op.drop_index("ix_cont_planes_org", table_name="cont_planes")
    op.drop_table("cont_planes")
    op.drop_index("ix_cont_dependencias_org", table_name="cont_dependencias")
    op.drop_table("cont_dependencias")
    op.drop_index("ix_cont_servicios_org", table_name="cont_servicios_criticos")
    op.drop_table("cont_servicios_criticos")
