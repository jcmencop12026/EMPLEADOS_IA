"""Modelos — Auditor determinístico de Empleados IA (Fase 1 MVP)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

HEALTH_STATUSES = frozenset(
    {
        "SALUDABLE",
        "OBSERVAR",
        "REQUIERE_MEJORA",
        "REQUIERE_INTERVENCION",
        "CRITICO",
    }
)

SEVERITY_LEVELS = frozenset({"NORMAL", "ADVERTENCIA", "CRITICO"})
SEMANTIC_KINDS = frozenset({"HECHO", "INFERENCIA", "RECOMENDACION"})
FINDING_STATUSES = frozenset({"ABIERTO", "CERRADO", "DESCARTADO"})
RUN_STATUSES = frozenset({"RUNNING", "COMPLETED", "FAILED", "SKIPPED"})
TRIGGER_TYPES = frozenset({"MANUAL", "SCHEDULE", "EVENT", "INTERNAL"})

RECOMMENDED_ACTIONS = frozenset(
    {
        "CAPACITAR",
        "ACTUALIZAR_CONOCIMIENTO",
        "MEJORAR_INSTRUCCIONES",
        "AGREGAR_HERRAMIENTA",
        "CAMBIAR_HERRAMIENTA",
        "CAMBIAR_MODELO",
        "CAMBIAR_PROVEEDOR",
        "AJUSTAR_AUTOMATIZACION",
        "REDISEÑAR_EMPLEADO",
        "SOLICITAR_REVISION_HUMANA",
    }
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmployeeAuditPolicy(Base):
    """Política de auditoría — org por defecto o override por empleado."""

    __tablename__ = "employee_audit_policies"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_id", name="uq_employee_audit_policy_org_emp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="WEEKLY")
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    thresholds_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_active_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    allowed_actions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_usd: Mapped[float | None] = mapped_column(nullable=True)
    max_runs_per_window: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    automation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("automations.id"), nullable=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class EmployeeAuditRun(Base):
    __tablename__ = "employee_audit_runs"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_employee_audit_run_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("employee_audit_policies.id"), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL", index=True)
    trigger_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    scope_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RUNNING", index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(nullable=False, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    initiated_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EmployeeAuditAssessment(Base):
    """Evaluación de salud por empleado en una ejecución."""

    __tablename__ = "employee_audit_assessments"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id", name="uq_employee_audit_assessment_run_emp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("employee_audit_runs.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    health_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(nullable=True)
    metrics_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class EmployeeAuditFinding(Base):
    __tablename__ = "employee_audit_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("employee_audit_runs.id"), nullable=False, index=True)
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("employee_audit_assessments.id"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_employees.id"), nullable=False, index=True)
    rule_code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(60), nullable=False)
    observed_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    threshold_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="ADVERTENCIA", index=True)
    semantic_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="HECHO")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTO", index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    notification_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("notifications.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
