"""Alembic — TCO y ecosistema de aliados (1320)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1320a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1310a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tco_categorias_costo",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("es_global", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_tco_categoria_org_code"),
    )
    op.create_index("ix_tco_categorias_org", "tco_categorias_costo", ["organization_id"])

    op.create_table(
        "tco_proveedores_aliados",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("contacto", sa.String(200), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("riesgo_nivel", sa.String(10), nullable=False, server_default="MEDIO"),
        sa.Column("riesgo_criterio", sa.Text(), nullable=True),
        sa.Column("riesgo_justificacion", sa.Text(), nullable=True),
        sa.Column("riesgo_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("riesgo_responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "codigo", name="uq_tco_proveedor_org_codigo"),
    )
    op.create_index("ix_tco_proveedores_org", "tco_proveedores_aliados", ["organization_id"])

    op.create_table(
        "tco_contratos_condiciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=False),
        sa.Column("moneda", sa.String(8), nullable=False, server_default="COP"),
        sa.Column("tipo_tarifa", sa.String(30), nullable=True),
        sa.Column("minimo", sa.Numeric(18, 4), nullable=True),
        sa.Column("maximo", sa.Numeric(18, 4), nullable=True),
        sa.Column("compromiso", sa.Text(), nullable=True),
        sa.Column("descuento_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("condiciones", sa.Text(), nullable=True),
        sa.Column("sla", sa.String(200), nullable=True),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="VIGENTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_contratos_org", "tco_contratos_condiciones", ["organization_id"])
    op.create_index("ix_tco_contratos_prov", "tco_contratos_condiciones", ["proveedor_id"])

    op.create_table(
        "tco_tarifas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("unidad", sa.String(40), nullable=False, server_default="unidad"),
        sa.Column("moneda", sa.String(8), nullable=False, server_default="COP"),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="UNIDAD"),
        sa.Column("monto_base", sa.Numeric(18, 8), nullable=True),
        sa.Column("periodicidad", sa.String(30), nullable=True),
        sa.Column("vigente_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vigente_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="VIGENTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_tarifas_org", "tco_tarifas", ["organization_id"])

    op.create_table(
        "tco_tarifa_tramos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tarifa_id", sa.String(36), sa.ForeignKey("tco_tarifas.id"), nullable=False),
        sa.Column("desde_unidades", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("hasta_unidades", sa.Numeric(18, 4), nullable=True),
        sa.Column("precio_unidad", sa.Numeric(18, 8), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_tco_tarifa_tramos_tarifa", "tco_tarifa_tramos", ["tarifa_id"])

    op.create_table(
        "tco_costos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("categoria_id", sa.String(36), sa.ForeignKey("tco_categorias_costo.id"), nullable=True),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo_costo", sa.String(20), nullable=False, server_default="FIJO"),
        sa.Column("naturaleza", sa.String(20), nullable=False, server_default="ESTIMADO"),
        sa.Column("periodicidad", sa.String(30), nullable=False, server_default="MENSUAL"),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("cantidad", sa.Numeric(18, 4), nullable=True),
        sa.Column("monto", sa.Numeric(18, 4), nullable=False),
        sa.Column("moneda", sa.String(8), nullable=False, server_default="COP"),
        sa.Column("tasa_conversion", sa.Numeric(18, 8), nullable=True),
        sa.Column("tasa_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monto_convertido", sa.Numeric(18, 4), nullable=True),
        sa.Column("moneda_destino", sa.String(8), nullable=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=True),
        sa.Column("finops_record_id", sa.String(36), nullable=True),
        sa.Column("employee_id", sa.String(36), nullable=True),
        sa.Column("integracion_ref", sa.String(120), nullable=True),
        sa.Column("periodo_ref", sa.String(20), nullable=True),
        sa.Column("vigente_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vigente_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_costos_org", "tco_costos", ["organization_id"])

    op.create_table(
        "tco_costos_historico",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("costo_id", sa.String(36), sa.ForeignKey("tco_costos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("motivo", sa.String(300), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_costos_hist_costo", "tco_costos_historico", ["costo_id"])

    op.create_table(
        "tco_distribuciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("costo_id", sa.String(36), sa.ForeignKey("tco_costos.id"), nullable=False),
        sa.Column("metodo", sa.String(30), nullable=False),
        sa.Column("criterio_json", sa.Text(), nullable=True),
        sa.Column("asignaciones_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_distribuciones_org", "tco_distribuciones", ["organization_id"])

    op.create_table(
        "tco_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=True),
        sa.Column("escenario", sa.String(60), nullable=True),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="ESTIMADO"),
        sa.Column("total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("desglose_json", sa.Text(), nullable=True),
        sa.Column("ingreso", sa.Numeric(18, 4), nullable=True),
        sa.Column("margen_bruto", sa.Numeric(18, 4), nullable=True),
        sa.Column("margen_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("punto_equilibrio", sa.Numeric(18, 4), nullable=True),
        sa.Column("finops_ia", sa.Numeric(18, 4), nullable=True),
        sa.Column("finops_total", sa.Numeric(18, 4), nullable=True),
        sa.Column("proveedores_json", sa.Text(), nullable=True),
        sa.Column("concentracion_json", sa.Text(), nullable=True),
        sa.Column("alertas_json", sa.Text(), nullable=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=True),
        sa.Column("es_simulacion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("explicacion", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_snapshots_org", "tco_snapshots", ["organization_id"])

    op.create_table(
        "tco_alianzas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proveedor_id", sa.String(36), sa.ForeignKey("tco_proveedores_aliados.id"), nullable=True),
        sa.Column("opportunity_id", sa.String(36), sa.ForeignKey("opportunities.id"), nullable=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("alcance", sa.Text(), nullable=True),
        sa.Column("vigencia_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vigencia_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("beneficios_esperados", sa.Text(), nullable=True),
        sa.Column("costos_esperados", sa.Numeric(18, 4), nullable=True),
        sa.Column("responsabilidades", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PROPUESTA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_alianzas_org", "tco_alianzas", ["organization_id"])

    op.create_table(
        "tco_simulaciones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("parametros_json", sa.Text(), nullable=False),
        sa.Column("resultado_json", sa.Text(), nullable=False),
        sa.Column("confirmada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_simulaciones_org", "tco_simulaciones", ["organization_id"])

    op.create_table(
        "tco_alertas_economicas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("severidad", sa.String(20), nullable=False, server_default="MEDIA"),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("datos_json", sa.Text(), nullable=True),
        sa.Column("resuelta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_alertas_org", "tco_alertas_economicas", ["organization_id"])

    op.create_table(
        "tco_auditoria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("entidad", sa.String(60), nullable=False),
        sa.Column("entidad_id", sa.String(36), nullable=True),
        sa.Column("detalle_json", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tco_auditoria_org", "tco_auditoria", ["organization_id"])


def downgrade() -> None:
    op.drop_table("tco_auditoria")
    op.drop_table("tco_alertas_economicas")
    op.drop_table("tco_simulaciones")
    op.drop_table("tco_alianzas")
    op.drop_table("tco_snapshots")
    op.drop_table("tco_distribuciones")
    op.drop_table("tco_costos_historico")
    op.drop_table("tco_costos")
    op.drop_table("tco_tarifa_tramos")
    op.drop_table("tco_tarifas")
    op.drop_table("tco_contratos_condiciones")
    op.drop_table("tco_proveedores_aliados")
    op.drop_table("tco_categorias_costo")
