"""Migración 1720 — Continuidad comercial y operacional EIAAX."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1720a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1710a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("impl_proyectos", sa.Column("opportunity_id", sa.String(36), nullable=True))
    op.add_column("impl_proyectos", sa.Column("evaluacion_id", sa.String(36), nullable=True))
    op.add_column("impl_proyectos", sa.Column("contract_id", sa.String(36), nullable=True))
    op.add_column("impl_proyectos", sa.Column("version_contratada", sa.Integer(), nullable=True))
    op.add_column("impl_proyectos", sa.Column("documento_contrato_id", sa.String(36), nullable=True))
    op.add_column("impl_proyectos", sa.Column("compromiso_contractual_json", sa.Text(), nullable=True))
    op.add_column("impl_proyectos", sa.Column("finops_budget_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_impl_proy_opp", "impl_proyectos", "opportunities", ["opportunity_id"], ["id"])
    op.create_foreign_key("fk_impl_proy_contract", "impl_proyectos", "negocio_contract_records", ["contract_id"], ["id"])
    op.create_foreign_key("fk_impl_proy_doc", "impl_proyectos", "negocio_proposal_documents", ["documento_contrato_id"], ["id"])
    op.create_foreign_key("fk_impl_proy_budget", "impl_proyectos", "finops_budgets", ["finops_budget_id"], ["id"])
    op.create_index("ix_impl_proy_opp", "impl_proyectos", ["opportunity_id"])
    op.create_index("ix_impl_proy_contract", "impl_proyectos", ["contract_id"])

    op.create_table(
        "impl_entregables",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=False),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("nombre", sa.String(300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_objetivo", _ts(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("documento_id", sa.String(36), sa.ForeignKey("negocio_proposal_documents.id"), nullable=True),
        sa.Column("aceptacion", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("version_referencia", sa.String(40), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
    )
    op.create_index("ix_impl_entregable_proy", "impl_entregables", ["proyecto_id"])

    op.create_table(
        "continuidad_cambios_alcance",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("negocio_contract_records.id"), nullable=True),
        sa.Column("estado", sa.String(30), nullable=False, server_default="SOLICITADO"),
        sa.Column("solicitud", sa.Text(), nullable=False),
        sa.Column("analisis", sa.Text(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("impacto_json", sa.Text(), nullable=True),
        sa.Column("negociacion_entry_id", sa.String(36), sa.ForeignKey("negocio_negotiation_entries.id"), nullable=True),
        sa.Column("nueva_version_id", sa.String(36), sa.ForeignKey("negocio_proposal_versions.id"), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
    )
    op.create_index("ix_cont_cambio_prop", "continuidad_cambios_alcance", ["proposal_id"])
    op.create_index("ix_cont_cambio_proy", "continuidad_cambios_alcance", ["proyecto_id"])

    op.create_table(
        "negocio_contract_closures",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("negocio_contract_records.id"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("proyecto_id", sa.String(36), sa.ForeignKey("impl_proyectos.id"), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("fecha_cierre", _ts(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="INICIADO"),
        sa.Column("pendientes_json", sa.Text(), nullable=True),
        sa.Column("empleados_retirar_json", sa.Text(), nullable=True),
        sa.Column("accesos_retirar_json", sa.Text(), nullable=True),
        sa.Column("exportaciones_json", sa.Text(), nullable=True),
        sa.Column("confirmacion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
    )
    op.create_index("ix_contract_closure_contract", "negocio_contract_closures", ["contract_id"])

    op.add_column("exito_renovaciones", sa.Column("opportunity_id", sa.String(36), nullable=True))
    op.add_column("exito_expansiones", sa.Column("opportunity_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_renov_opp", "exito_renovaciones", "opportunities", ["opportunity_id"], ["id"])
    op.create_foreign_key("fk_exp_opp", "exito_expansiones", "opportunities", ["opportunity_id"], ["id"])

    op.add_column("negocio_contract_records", sa.Column("finops_budget_id", sa.String(36), nullable=True))
    op.create_foreign_key(
        "fk_contract_finops_budget",
        "negocio_contract_records",
        "finops_budgets",
        ["finops_budget_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_contract_finops_budget", "negocio_contract_records", type_="foreignkey")
    op.drop_column("negocio_contract_records", "finops_budget_id")
    op.drop_constraint("fk_exp_opp", "exito_expansiones", type_="foreignkey")
    op.drop_constraint("fk_renov_opp", "exito_renovaciones", type_="foreignkey")
    op.drop_column("exito_expansiones", "opportunity_id")
    op.drop_column("exito_renovaciones", "opportunity_id")
    op.drop_table("negocio_contract_closures")
    op.drop_table("continuidad_cambios_alcance")
    op.drop_table("impl_entregables")
    op.drop_constraint("fk_impl_proy_budget", "impl_proyectos", type_="foreignkey")
    op.drop_constraint("fk_impl_proy_doc", "impl_proyectos", type_="foreignkey")
    op.drop_constraint("fk_impl_proy_contract", "impl_proyectos", type_="foreignkey")
    op.drop_constraint("fk_impl_proy_opp", "impl_proyectos", type_="foreignkey")
    op.drop_index("ix_impl_proy_contract", "impl_proyectos")
    op.drop_index("ix_impl_proy_opp", "impl_proyectos")
    for col in (
        "finops_budget_id", "compromiso_contractual_json", "documento_contrato_id",
        "version_contratada", "contract_id", "evaluacion_id", "opportunity_id",
    ):
        op.drop_column("impl_proyectos", col)
