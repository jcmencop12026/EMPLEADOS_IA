"""Modelos persistentes del motor especializado IPS (SALUD-960)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IpsDataset(Base):
    __tablename__ = "ips_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ips_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    filename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    profile_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    data_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    quality_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsAnalysis(Base):
    __tablename__ = "ips_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ips_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    analysis_type: Mapped[str] = mapped_column(String(80), default="diagnostico_integral")
    status: Mapped[str] = mapped_column(String(40), default="CREATED", index=True)
    request_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    data_profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_analyses_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicators_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    traceability_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialists_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IpsHallazgo(Base):
    __tablename__ = "ips_hallazgos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("ips_analyses.id"), nullable=False, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="HECHO")
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicator_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    indicator_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    period: Mapped[str | None] = mapped_column(String(60), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIA")
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="MEDIA")
    confidence_criteria_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    probable_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    economic_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsPropuesta(Base):
    __tablename__ = "ips_propuestas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("ips_analyses.id"), nullable=False, index=True)
    hallazgo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ips_hallazgos.id"), nullable=True)
    problema: Mapped[str] = mapped_column(Text, nullable=False)
    evidencia: Mapped[str] = mapped_column(Text, nullable=False)
    causa_probable: Mapped[str | None] = mapped_column(Text, nullable=True)
    impacto: Mapped[str] = mapped_column(Text, nullable=False)
    accion_propuesta: Mapped[str] = mapped_column(Text, nullable=False)
    responsable_sugerido: Mapped[str | None] = mapped_column(String(120), nullable=True)
    plazo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    indicador_seguimiento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meta: Mapped[str | None] = mapped_column(String(120), nullable=True)
    impacto_esperado: Mapped[str | None] = mapped_column(Text, nullable=True)
    confianza: Mapped[str] = mapped_column(String(20), default="MEDIA")
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_for_plan: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsActionPlan(Base):
    __tablename__ = "ips_action_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("ips_analyses.id"), nullable=False, index=True)
    work_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("work_plans.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="BORRADOR")
    tasks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_by_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsExperienceCase(Base):
    __tablename__ = "ips_experience_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ips_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    analysis_type: Mapped[str] = mapped_column(String(80), nullable=False)
    analysis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ips_analyses.id"), nullable=True)
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicators_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    hallazgos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_applied: Mapped[str | None] = mapped_column(Text, nullable=True)
    later_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation: Mapped[str | None] = mapped_column(String(40), nullable=True)
    employee_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsFeedback(Base):
    __tablename__ = "ips_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(40), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsActionResult(Base):
    __tablename__ = "ips_action_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    propuesta_id: Mapped[str] = mapped_column(String(36), ForeignKey("ips_propuestas.id"), nullable=False, index=True)
    meta: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    outcome: Mapped[str] = mapped_column(String(40), default="NO_EVALUADO")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsHistoricalProfile(Base):
    __tablename__ = "ips_historical_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    ips_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class IpsEmployeePerformance(Base):
    __tablename__ = "ips_employee_performances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
