"""Alembic — Implementación y éxito del cliente (1340)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1340a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1320a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "impl_proyectos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PLANIFICACION"),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("commercial_plans.id"), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_inicio", _ts(), nullable=True),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("alcance", sa.Text(), nullable=True),
        sa.Column("objetivos", sa.Text(), nullable=True),
        sa.Column("riesgos_resumen", sa.Text(), nullable=True),
        sa.Column("avance_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("valor_compromiso_json", sa.Text(), nullable=True),
        sa.Column("go_live_aprobado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("go_live_fecha", _ts(), nullable=True),
        sa.Column("go_live_aprobado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("go_live_checklist_json", sa.Text(), nullable=True),
        sa.Column("go_live_observaciones", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_impl_proyecto_org_codigo"),
    )
    op.create_index("ix_impl_proyectos_org", "impl_proyectos", ["organization_id"])
    op.create_index("ix_impl_proyectos_estado", "impl_proyectos", ["estado"])

    op.create_table(
        "impl_fases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responsabilidad", sa.String(20), nullable=False, server_default="NUESTRO_EQUIPO"),
        sa.Column("fecha_inicio", _ts(), nullable=True),
        sa.Column("fecha_fin", _ts(), nullable=True),
        sa.Column("criterio_entrada", sa.Text(), nullable=True),
        sa.Column("criterio_salida", sa.Text(), nullable=True),
        sa.Column("dependencias_json", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_hitos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("fase_id", sa.String(36), sa.ForeignKey("impl_fases.id"), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(60), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responsabilidad", sa.String(20), nullable=False, server_default="NUESTRO_EQUIPO"),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=True),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("fecha_real", _ts(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("dependencias_json", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_tareas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("fase_id", sa.String(36), sa.ForeignKey("impl_fases.id"), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responsabilidad", sa.String(20), nullable=False, server_default="NUESTRO_EQUIPO"),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=True),
        sa.Column("prioridad", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("dependencias_json", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_requisitos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("responsabilidad", sa.String(20), nullable=False, server_default="CLIENTE"),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("fecha_requerida", _ts(), nullable=True),
        sa.Column("fecha_recibida", _ts(), nullable=True),
        sa.Column("bloqueante", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_readiness",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("dimensiones_json", sa.Text(), nullable=False),
        sa.Column("resultado", sa.String(30), nullable=False),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("evaluado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_bloqueadores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("impacto", sa.String(20), nullable=False, server_default="ALTO"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("accion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ABIERTO"),
        sa.Column("critico", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("resuelto_at", _ts(), nullable=True),
    )

    op.create_table(
        "impl_riesgos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("probabilidad", sa.String(10), nullable=False, server_default="MEDIA"),
        sa.Column("impacto", sa.String(10), nullable=False, server_default="MEDIO"),
        sa.Column("nivel", sa.String(10), nullable=False, server_default="MEDIO"),
        sa.Column("mitigacion", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ABIERTO"),
        sa.Column("referencia_externa", sa.String(120), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_pilotos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("alcance", sa.Text(), nullable=True),
        sa.Column("usuarios_json", sa.Text(), nullable=True),
        sa.Column("procesos_json", sa.Text(), nullable=True),
        sa.Column("empleados_ia_json", sa.Text(), nullable=True),
        sa.Column("duracion_dias", sa.Integer(), nullable=True),
        sa.Column("metricas_objetivo_json", sa.Text(), nullable=True),
        sa.Column("criterios_exito", sa.Text(), nullable=True),
        sa.Column("criterios_suspension", sa.Text(), nullable=True),
        sa.Column("responsables_json", sa.Text(), nullable=True),
        sa.Column("resultado", sa.String(30), nullable=True),
        sa.Column("resultado_explicacion", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("aprobado_produccion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aprobado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("aprobado_at", _ts(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PLANIFICADO"),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_adopcion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=True),
        sa.Column("metricas_json", sa.Text(), nullable=False),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_plan_adopcion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo_accion", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_capacitaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tema", sa.String(200), nullable=False),
        sa.Column("grupo", sa.String(120), nullable=True),
        sa.Column("fecha", _ts(), nullable=True),
        sa.Column("asistentes", sa.Integer(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resultado", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_planes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("valor_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_compromiso_json", sa.Text(), nullable=True),
        sa.Column("periodicidad_revision", sa.String(20), nullable=False, server_default="MENSUAL"),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("proxima_revision", _ts(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_objetivos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("exito_planes.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("indicador", sa.String(120), nullable=True),
        sa.Column("valor_esperado", sa.Numeric(18, 4), nullable=True),
        sa.Column("valor_medido", sa.Numeric(18, 4), nullable=True),
        sa.Column("estado_valor", sa.String(30), nullable=False, server_default="NO_MEDIDO"),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("linea_base_id", sa.String(36), nullable=True),
        sa.Column("valuation_id", sa.String(36), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_revisiones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("exito_planes.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("fecha", _ts(), nullable=False),
        sa.Column("periodicidad", sa.String(20), nullable=False),
        sa.Column("indicadores_json", sa.Text(), nullable=True),
        sa.Column("valor_json", sa.Text(), nullable=True),
        sa.Column("riesgos_json", sa.Text(), nullable=True),
        sa.Column("bloqueos_json", sa.Text(), nullable=True),
        sa.Column("acciones_json", sa.Text(), nullable=True),
        sa.Column("decisiones", sa.Text(), nullable=True),
        sa.Column("revisado_por", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_planes_accion",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("exito_planes.id"), nullable=False),
        sa.Column("objetivo_id", sa.String(36), sa.ForeignKey("exito_objetivos.id"), nullable=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("causa", sa.String(40), nullable=False),
        sa.Column("accion", sa.Text(), nullable=False),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("impacto_esperado", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_renovaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("exito_planes.id"), nullable=True),
        sa.Column("fecha_renovacion", _ts(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("valor_acumulado", sa.Numeric(18, 4), nullable=True),
        sa.Column("adopcion_json", sa.Text(), nullable=True),
        sa.Column("salud", sa.String(20), nullable=True),
        sa.Column("riesgos_json", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_expansiones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("recomendacion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PROPUESTA"),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "exito_salud",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("resultado", sa.String(20), nullable=False),
        sa.Column("puntuacion", sa.Numeric(5, 2), nullable=False),
        sa.Column("factores_json", sa.Text(), nullable=False),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_alertas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("severidad", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("resuelta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", _ts(), nullable=False),
    )

    op.create_table(
        "impl_auditoria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("entidad", sa.String(60), nullable=False),
        sa.Column("entidad_id", sa.String(36), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )


def downgrade() -> None:
    for t in (
        "impl_auditoria", "impl_alertas", "exito_salud", "exito_expansiones", "exito_renovaciones",
        "exito_planes_accion", "exito_revisiones", "exito_objetivos", "exito_planes",
        "impl_capacitaciones", "impl_plan_adopcion", "impl_adopcion", "impl_pilotos",
        "impl_riesgos", "impl_bloqueadores", "impl_readiness", "impl_requisitos",
        "impl_tareas", "impl_hitos", "impl_fases", "impl_proyectos",
    ):
        op.drop_table(t)
