"""Migración 1730 — Flujo comercial V1 EIAAX."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1730a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "1720a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts():
    return sa.DateTime(timezone=True)


def upgrade() -> None:
    op.add_column("evaluaciones_expediente", sa.Column("sector", sa.String(80), nullable=True))
    op.create_index("ix_eval_exp_sector", "evaluaciones_expediente", ["sector"])

    op.add_column("opportunities", sa.Column("origen_comercial", sa.String(20), nullable=False, server_default="SOLICITADA"))
    op.add_column("opportunities", sa.Column("presentar_cliente", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_opp_origen_comercial", "opportunities", ["origen_comercial"])
    op.create_index("ix_opp_presentar_cliente", "opportunities", ["presentar_cliente"])

    op.create_table(
        "comercial_presentaciones_ejecutivas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("evaluacion_id", sa.String(36), sa.ForeignKey("evaluaciones_expediente.id"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=True),
        sa.Column("titulo", sa.String(300), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("hallazgos_ids_json", sa.Text(), nullable=True),
        sa.Column("oportunidades_ids_json", sa.Text(), nullable=True),
        sa.Column("secciones_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
    )
    op.create_index("ix_pres_ejec_eval", "comercial_presentaciones_ejecutivas", ["evaluacion_id"])

    op.create_table(
        "comercial_instrumentos_contractuales",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("negocio_contract_records.id"), nullable=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("contenido_resumen", sa.Text(), nullable=True),
        sa.Column("documento_id", sa.String(36), sa.ForeignKey("negocio_proposal_documents.id"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
    )
    op.create_index("ix_inst_prop", "comercial_instrumentos_contractuales", ["proposal_id"])

    op.create_table(
        "comercial_compromisos_garantia",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("commercial_proposals.id"), nullable=False),
        sa.Column("tipo_compromiso", sa.String(30), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("baseline", sa.Text(), nullable=True),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("dependencias_json", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("atribucion", sa.Text(), nullable=True),
        sa.Column("cumplimiento_estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", _ts(), nullable=False),
        sa.Column("updated_at", _ts(), nullable=False),
    )
    op.create_index("ix_garant_prop", "comercial_compromisos_garantia", ["proposal_id"])


def downgrade() -> None:
    op.drop_index("ix_garant_prop", table_name="comercial_compromisos_garantia")
    op.drop_table("comercial_compromisos_garantia")
    op.drop_index("ix_inst_prop", table_name="comercial_instrumentos_contractuales")
    op.drop_table("comercial_instrumentos_contractuales")
    op.drop_index("ix_pres_ejec_eval", table_name="comercial_presentaciones_ejecutivas")
    op.drop_table("comercial_presentaciones_ejecutivas")
    op.drop_index("ix_opp_presentar_cliente", table_name="opportunities")
    op.drop_index("ix_opp_origen_comercial", table_name="opportunities")
    op.drop_column("opportunities", "presentar_cliente")
    op.drop_column("opportunities", "origen_comercial")
    op.drop_index("ix_eval_exp_sector", table_name="evaluaciones_expediente")
    op.drop_column("evaluaciones_expediente", "sector")
