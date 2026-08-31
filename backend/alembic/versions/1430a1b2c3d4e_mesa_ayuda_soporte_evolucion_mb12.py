"""Alembic — Evolución Mesa de Ayuda y Soporte (MB-12). Depende de 1420a1b2c3d4e."""

from alembic import op
import sqlalchemy as sa

revision = "1430a1b2c3d4e"
down_revision = "1420a1b2c3d4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("support_sla_policies", sa.Column("tipo_caso", sa.String(length=40), nullable=True))
    op.add_column("support_sla_policies", sa.Column("servicio", sa.String(length=80), nullable=True))

    op.add_column("support_cases", sa.Column("problema_id", sa.String(length=36), nullable=True))
    op.add_column("support_cases", sa.Column("es_incidente_mayor", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("support_cases", sa.Column("coordinador_id", sa.String(length=36), nullable=True))
    op.add_column("support_cases", sa.Column("responsable_tecnico_id", sa.String(length=36), nullable=True))
    op.add_column("support_cases", sa.Column("responsable_funcional_id", sa.String(length=36), nullable=True))
    op.add_column("support_cases", sa.Column("prioridad_sugerida", sa.String(length=20), nullable=True))
    op.add_column("support_cases", sa.Column("prioridad_ajuste_motivo", sa.Text(), nullable=True))
    op.add_column("support_cases", sa.Column("prioridad_ajuste_por", sa.String(length=36), nullable=True))
    op.add_column("support_cases", sa.Column("clasificado_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("support_cases", sa.Column("validacion_solicitante", sa.String(length=20), nullable=True))
    op.add_column("support_cases", sa.Column("validacion_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("support_cases", sa.Column("sintoma", sa.Text(), nullable=True))
    op.add_column("support_cases", sa.Column("hipotesis", sa.Text(), nullable=True))
    op.add_column("support_cases", sa.Column("causa_probable", sa.Text(), nullable=True))
    op.add_column("support_cases", sa.Column("causa_validada", sa.Text(), nullable=True))
    op.add_column("support_cases", sa.Column("servicio_componente", sa.String(length=120), nullable=True))
    op.add_column("support_cases", sa.Column("sla_warning_emitido", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("support_cases", sa.Column("escalamiento_nivel", sa.Integer(), nullable=False, server_default="0"))
    op.create_foreign_key(
        "fk_support_case_coordinador",
        "support_cases",
        "users",
        ["coordinador_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_support_case_resp_tecnico",
        "support_cases",
        "users",
        ["responsable_tecnico_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_support_case_resp_funcional",
        "support_cases",
        "users",
        ["responsable_funcional_id"],
        ["id"],
    )
    op.create_index("ix_support_cases_problema", "support_cases", ["problema_id"])

    op.create_table(
        "support_problems",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=300), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="ABIERTO"),
        sa.Column("causa_raiz", sa.Text(), nullable=True),
        sa.Column("solucion_temporal", sa.Text(), nullable=True),
        sa.Column("solucion_definitiva", sa.Text(), nullable=True),
        sa.Column("acciones_preventivas", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cerrado_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "numero", name="uq_support_problem_org_numero"),
    )
    op.create_index("ix_support_problems_org", "support_problems", ["organization_id"])
    op.create_foreign_key(
        "fk_support_case_problema",
        "support_cases",
        "support_problems",
        ["problema_id"],
        ["id"],
    )

    op.create_table(
        "support_case_evidences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=False),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("referencia", sa.String(length=500), nullable=False),
        sa.Column("descripcion", sa.String(length=300), nullable=True),
        sa.Column("usuario_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_support_evidences_case", "support_case_evidences", ["case_id"])

    op.create_table(
        "support_knowledge_proposals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=True),
        sa.Column("problem_id", sa.String(length=36), sa.ForeignKey("support_problems.id"), nullable=True),
        sa.Column("titulo", sa.String(length=300), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("tipo_articulo", sa.String(length=40), nullable=False, server_default="PROCEDIMIENTO"),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
        sa.Column("propuesto_por", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revisado_por", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revisado_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_support_kb_prop_org", "support_knowledge_proposals", ["organization_id"])

    op.create_table(
        "support_post_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("support_cases.id"), nullable=False),
        sa.Column("que_ocurrio", sa.Text(), nullable=True),
        sa.Column("impacto", sa.Text(), nullable=True),
        sa.Column("causa", sa.Text(), nullable=True),
        sa.Column("que_se_hizo", sa.Text(), nullable=True),
        sa.Column("tiempos", sa.Text(), nullable=True),
        sa.Column("que_funciono", sa.Text(), nullable=True),
        sa.Column("que_fallo", sa.Text(), nullable=True),
        sa.Column("accion_preventiva", sa.Text(), nullable=True),
        sa.Column("responsable_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("fecha_objetivo", sa.DateTime(timezone=True), nullable=True),
        sa.Column("autor_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", name="uq_support_post_review_case"),
    )


def downgrade() -> None:
    op.drop_table("support_post_reviews")
    op.drop_table("support_knowledge_proposals")
    op.drop_table("support_case_evidences")
    op.drop_constraint("fk_support_case_problema", "support_cases", type_="foreignkey")
    op.drop_table("support_problems")
    op.drop_index("ix_support_cases_problema", table_name="support_cases")
    op.drop_constraint("fk_support_case_resp_funcional", "support_cases", type_="foreignkey")
    op.drop_constraint("fk_support_case_resp_tecnico", "support_cases", type_="foreignkey")
    op.drop_constraint("fk_support_case_coordinador", "support_cases", type_="foreignkey")
    for col in (
        "escalamiento_nivel",
        "sla_warning_emitido",
        "servicio_componente",
        "causa_validada",
        "causa_probable",
        "hipotesis",
        "sintoma",
        "validacion_at",
        "validacion_solicitante",
        "clasificado_at",
        "prioridad_ajuste_por",
        "prioridad_ajuste_motivo",
        "prioridad_sugerida",
        "responsable_funcional_id",
        "responsable_tecnico_id",
        "coordinador_id",
        "es_incidente_mayor",
        "problema_id",
    ):
        op.drop_column("support_cases", col)
    op.drop_column("support_sla_policies", "servicio")
    op.drop_column("support_sla_policies", "tipo_caso")
