"""salud_ips_engine_960

Revision ID: 960a1b2c3d4e
Revises: 5b2eb2437398
Create Date: 2026-08-25 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '960a1b2c3d4e'
down_revision: Union[str, Sequence[str], None] = '5b2eb2437398'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ips_datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('ips_name', sa.String(length=200), nullable=False),
        sa.Column('source_type', sa.String(length=60), nullable=False),
        sa.Column('filename', sa.String(length=300), nullable=True),
        sa.Column('profile_code', sa.String(length=80), nullable=True),
        sa.Column('records_count', sa.Integer(), nullable=False),
        sa.Column('data_json', sa.Text(), nullable=False),
        sa.Column('quality_json', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ips_datasets_org', 'ips_datasets', ['organization_id'])
    op.create_index('ix_ips_datasets_ips', 'ips_datasets', ['ips_name'])
    op.create_index('ix_ips_datasets_source', 'ips_datasets', ['source_type'])

    op.create_table(
        'ips_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('ips_name', sa.String(length=200), nullable=False),
        sa.Column('analysis_type', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('request_text', sa.Text(), nullable=True),
        sa.Column('work_plan_id', sa.String(length=36), nullable=True),
        sa.Column('data_profile_json', sa.Text(), nullable=True),
        sa.Column('available_analyses_json', sa.Text(), nullable=True),
        sa.Column('indicators_json', sa.Text(), nullable=True),
        sa.Column('traceability_json', sa.Text(), nullable=True),
        sa.Column('summary_json', sa.Text(), nullable=True),
        sa.Column('specialists_json', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ips_analyses_org', 'ips_analyses', ['organization_id'])

    op.create_table(
        'ips_hallazgos',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('evidence_json', sa.Text(), nullable=True),
        sa.Column('indicator_code', sa.String(length=80), nullable=True),
        sa.Column('indicator_value', sa.String(length=120), nullable=True),
        sa.Column('period', sa.String(length=60), nullable=True),
        sa.Column('scope', sa.String(length=200), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=False),
        sa.Column('confidence_criteria_json', sa.Text(), nullable=True),
        sa.Column('probable_cause', sa.Text(), nullable=True),
        sa.Column('economic_impact', sa.Float(), nullable=True),
        sa.Column('sources_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['ips_analyses.id']),
        sa.ForeignKeyConstraint(['employee_id'], ['ai_employees.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_propuestas',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('hallazgo_id', sa.String(length=36), nullable=True),
        sa.Column('problema', sa.Text(), nullable=False),
        sa.Column('evidencia', sa.Text(), nullable=False),
        sa.Column('causa_probable', sa.Text(), nullable=True),
        sa.Column('impacto', sa.Text(), nullable=False),
        sa.Column('accion_propuesta', sa.Text(), nullable=False),
        sa.Column('responsable_sugerido', sa.String(length=120), nullable=True),
        sa.Column('plazo', sa.String(length=60), nullable=True),
        sa.Column('indicador_seguimiento', sa.String(length=120), nullable=True),
        sa.Column('meta', sa.String(length=120), nullable=True),
        sa.Column('impacto_esperado', sa.Text(), nullable=True),
        sa.Column('confianza', sa.String(length=20), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('selected_for_plan', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['ips_analyses.id']),
        sa.ForeignKeyConstraint(['hallazgo_id'], ['ips_hallazgos.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_action_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('work_plan_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('tasks_json', sa.Text(), nullable=False),
        sa.Column('created_by_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['ips_analyses.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['work_plan_id'], ['work_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_experience_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('ips_name', sa.String(length=200), nullable=False),
        sa.Column('analysis_type', sa.String(length=80), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('context_json', sa.Text(), nullable=True),
        sa.Column('indicators_json', sa.Text(), nullable=True),
        sa.Column('hallazgos_json', sa.Text(), nullable=True),
        sa.Column('recommendations_json', sa.Text(), nullable=True),
        sa.Column('human_decision', sa.Text(), nullable=True),
        sa.Column('action_applied', sa.Text(), nullable=True),
        sa.Column('later_result', sa.Text(), nullable=True),
        sa.Column('evaluation', sa.String(length=40), nullable=True),
        sa.Column('employee_ids_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['ips_analyses.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_feedbacks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('target_type', sa.String(length=40), nullable=False),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('feedback_type', sa.String(length=40), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_action_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('propuesta_id', sa.String(length=36), nullable=False),
        sa.Column('meta', sa.String(length=200), nullable=True),
        sa.Column('resultado', sa.String(length=200), nullable=True),
        sa.Column('outcome', sa.String(length=40), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['propuesta_id'], ['ips_propuestas.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_historical_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('ips_name', sa.String(length=200), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('metrics_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ips_employee_performances',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=False),
        sa.Column('specialty', sa.String(length=120), nullable=False),
        sa.Column('metrics_json', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['ai_employees.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ips_employee_performances')
    op.drop_table('ips_historical_profiles')
    op.drop_table('ips_action_results')
    op.drop_table('ips_feedbacks')
    op.drop_table('ips_experience_cases')
    op.drop_table('ips_action_plans')
    op.drop_table('ips_propuestas')
    op.drop_table('ips_hallazgos')
    op.drop_table('ips_analyses')
    op.drop_index('ix_ips_datasets_source', 'ips_datasets')
    op.drop_index('ix_ips_datasets_ips', 'ips_datasets')
    op.drop_index('ix_ips_datasets_org', 'ips_datasets')
    op.drop_table('ips_datasets')
