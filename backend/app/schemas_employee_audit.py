"""Esquemas API — Auditor Empleados IA."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmployeeAuditPolicyIn(BaseModel):
    enabled: bool | None = None
    frequency: str | None = None
    window_days: int | None = Field(None, ge=1, le=90)
    thresholds: dict[str, Any] | None = None
    metrics_active: list[str] | None = None
    allowed_actions: dict[str, str] | None = None
    budget_usd: float | None = None
    max_runs_per_window: int | None = Field(None, ge=1, le=100)
    window_hours: int | None = Field(None, ge=1, le=168)
    automation_id: str | None = None


class EmployeeAuditPolicyOut(BaseModel):
    id: str
    organization_id: str
    employee_id: str | None = None
    enabled: bool
    frequency: str
    window_days: int
    thresholds: dict[str, Any] = Field(default_factory=dict)
    metrics_active: list[str] = Field(default_factory=list)
    allowed_actions: dict[str, str] = Field(default_factory=dict)
    budget_usd: float | None = None
    max_runs_per_window: int
    window_hours: int
    automation_id: str | None = None
    last_executed_at: datetime | None = None
    next_scheduled_at: datetime | None = None


class EmployeeAuditExecuteIn(BaseModel):
    employee_id: str | None = None
    employee_ids: list[str] | None = None
    scope: str | None = Field(None, description="ACTIVE | ALL | LIST")
    organization_id: str | None = None
    trigger_ref: str | None = None


class EmployeeAuditFindingOut(BaseModel):
    id: str
    run_id: str
    assessment_id: str
    employee_id: str
    rule_code: str
    metric_name: str
    observed_value: str | None = None
    threshold_value: str | None = None
    severity: str
    semantic_kind: str
    title: str
    detail: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None
    status: str
    correlation_id: str
    created_at: datetime | None = None


class EmployeeAuditAssessmentOut(BaseModel):
    id: str
    run_id: str
    employee_id: str
    employee_name: str | None = None
    health_status: str
    score: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    lifecycle_status: str | None = None
    findings: list[EmployeeAuditFindingOut] = Field(default_factory=list)


class EmployeeAuditRunOut(BaseModel):
    id: str
    organization_id: str
    trigger_type: str
    trigger_ref: str | None = None
    status: str
    correlation_id: str
    employee_count: int
    findings_count: int
    cost_usd: float
    started_at: datetime | None = None
    finished_at: datetime | None = None
    assessments: list[EmployeeAuditAssessmentOut] = Field(default_factory=list)


class EmployeeHealthOut(BaseModel):
    employee_id: str
    employee_name: str | None = None
    organization_id: str
    health_status: str
    score: float | None = None
    lifecycle_status: str | None = None
    last_audit_at: datetime | None = None
    open_findings: int = 0
    critical_findings: int = 0


class CentroControlSaludEmpleadosOut(BaseModel):
    organization_id: str
    total: int
    saludables: int
    en_observacion: int
    requieren_mejora: int
    requieren_intervencion: int
    criticos: int
    ultima_auditoria_at: datetime | None = None
    hallazgos_abiertos: int
    auditorias_vencidas: int


class TrabajoContractItemOut(BaseModel):
    """Contrato portable para bandeja Mi Trabajo (sin modificar trabajo_service)."""

    id: str
    tipo: str
    asunto: str
    modulo: str
    employee_id: str
    severity: str
    health_status: str
    recommended_action: str | None = None
    correlation_id: str
    enlace: str
    requires_action: bool
