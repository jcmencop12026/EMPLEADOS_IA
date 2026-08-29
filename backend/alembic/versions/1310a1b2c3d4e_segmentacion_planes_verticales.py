"""Alembic — Segmentación, paquetes y planes verticales (1310)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1310a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1280b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commercial_sectors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_commercial_sector_org_code"),
    )
    op.create_index("ix_commercial_sectors_org", "commercial_sectors", ["organization_id"])

    op.create_table(
        "commercial_segments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("sector_id", sa.String(36), sa.ForeignKey("commercial_sectors.id"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("dimensions_json", sa.Text(), nullable=True),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="ACTIVO"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_commercial_segment_org_code"),
    )

    op.create_table(
        "organization_commercial_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("segment_id", sa.String(36), sa.ForeignKey("commercial_segments.id"), nullable=True),
        sa.Column("sector_id", sa.String(36), sa.ForeignKey("commercial_sectors.id"), nullable=True),
        sa.Column("subsector", sa.String(120), nullable=True),
        sa.Column("tamano", sa.String(40), nullable=True),
        sa.Column("madurez_digital", sa.String(40), nullable=True),
        sa.Column("complejidad_operativa", sa.String(40), nullable=True),
        sa.Column("num_usuarios", sa.Integer(), nullable=True),
        sa.Column("num_empleados_ia", sa.Integer(), nullable=True),
        sa.Column("volumen_operaciones", sa.Integer(), nullable=True),
        sa.Column("num_integraciones", sa.Integer(), nullable=True),
        sa.Column("consumo_ia_estimado", sa.Integer(), nullable=True),
        sa.Column("nivel_soporte", sa.String(40), nullable=True),
        sa.Column("sla_requerido", sa.String(40), nullable=True),
        sa.Column("riesgo", sa.String(40), nullable=True),
        sa.Column("potencial_valor", sa.Numeric(18, 4), nullable=True),
        sa.Column("presupuesto_estimado", sa.Numeric(18, 4), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("evaluado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", name="uq_org_commercial_profile"),
    )

    op.create_table(
        "commercial_capabilities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_commercial_capability_code"),
    )

    op.create_table(
        "commercial_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("commercial_plans.id"), nullable=True),
        sa.Column("segment_id", sa.String(36), sa.ForeignKey("commercial_segments.id"), nullable=True),
        sa.Column("sector_id", sa.String(36), sa.ForeignKey("commercial_sectors.id"), nullable=True),
        sa.Column("base_package_id", sa.String(36), sa.ForeignKey("commercial_packages.id"), nullable=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("empleados_ia_incluidos", sa.Integer(), nullable=True),
        sa.Column("usuarios_incluidos", sa.Integer(), nullable=True),
        sa.Column("automatizaciones_incluidas", sa.Integer(), nullable=True),
        sa.Column("consumo_ia_incluido_tokens", sa.Integer(), nullable=True),
        sa.Column("presupuesto_ia_incluido", sa.Numeric(18, 4), nullable=True),
        sa.Column("integraciones_incluidas", sa.Integer(), nullable=True),
        sa.Column("almacenamiento_gb", sa.Integer(), nullable=True),
        sa.Column("sla_nivel", sa.String(40), nullable=True),
        sa.Column("soporte_nivel", sa.String(40), nullable=True),
        sa.Column("excedente_ia_por_millon", sa.Numeric(18, 8), nullable=True),
        sa.Column("alerta_consumo_pct", sa.Numeric(7, 4), nullable=True),
        sa.Column("bloqueo_excedente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("credential_modes_json", sa.Text(), nullable=True),
        sa.Column("capabilities_json", sa.Text(), nullable=True),
        sa.Column("servicios_incluidos_json", sa.Text(), nullable=True),
        sa.Column("servicios_opcionales_json", sa.Text(), nullable=True),
        sa.Column("custom_overrides_json", sa.Text(), nullable=True),
        sa.Column("precio_estimado", sa.Numeric(18, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "code", name="uq_commercial_package_org_code"),
    )

    op.create_table(
        "commercial_package_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("commercial_packages.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("package_id", "version_number", name="uq_package_version"),
    )

    op.create_table(
        "commercial_plan_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("commercial_plans.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("plan_id", "version_number", name="uq_plan_version"),
    )

    op.create_table(
        "commercial_discounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("target_type", sa.String(30), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("valor_descuento", sa.Numeric(18, 4), nullable=False),
        sa.Column("valor_original", sa.Numeric(18, 4), nullable=False),
        sa.Column("valor_final", sa.Numeric(18, 4), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("vigencia_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.add_column("commercial_plans", sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="ACTIVO"))
    op.add_column("commercial_plans", sa.Column("segment_id", sa.String(36), nullable=True))
    op.add_column("commercial_plans", sa.Column("sector_id", sa.String(36), nullable=True))
    op.add_column("commercial_plans", sa.Column("base_plan_id", sa.String(36), nullable=True))
    op.add_column("commercial_plans", sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("commercial_plans", sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.add_column("commercial_proposals", sa.Column("package_id", sa.String(36), nullable=True))
    op.add_column("commercial_proposals", sa.Column("package_version_id", sa.String(36), nullable=True))
    op.add_column("commercial_proposals", sa.Column("plan_version_id", sa.String(36), nullable=True))
    op.add_column("commercial_proposals", sa.Column("segment_id", sa.String(36), nullable=True))
    op.add_column("commercial_proposals", sa.Column("profile_snapshot_json", sa.Text(), nullable=True))
    op.add_column("commercial_proposals", sa.Column("catalog_snapshot_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("commercial_proposals", "catalog_snapshot_json")
    op.drop_column("commercial_proposals", "profile_snapshot_json")
    op.drop_column("commercial_proposals", "segment_id")
    op.drop_column("commercial_proposals", "plan_version_id")
    op.drop_column("commercial_proposals", "package_version_id")
    op.drop_column("commercial_proposals", "package_id")
    op.drop_column("commercial_plans", "is_custom")
    op.drop_column("commercial_plans", "version_number")
    op.drop_column("commercial_plans", "base_plan_id")
    op.drop_column("commercial_plans", "sector_id")
    op.drop_column("commercial_plans", "segment_id")
    op.drop_column("commercial_plans", "lifecycle_status")
    op.drop_table("commercial_discounts")
    op.drop_table("commercial_plan_versions")
    op.drop_table("commercial_package_versions")
    op.drop_table("commercial_packages")
    op.drop_table("commercial_capabilities")
    op.drop_table("organization_commercial_profiles")
    op.drop_table("commercial_segments")
    op.drop_index("ix_commercial_sectors_org", table_name="commercial_sectors")
    op.drop_table("commercial_sectors")
