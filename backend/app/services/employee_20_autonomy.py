"""Autonomía controlada — extensión mínima del coordinador (sin reemplazarlo)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.employee_20_constants import AUTONOMY_LEVELS, default_autonomy_for_employee
from app.employee_20_models import EmployeeLaborProfile
from app.orchestration_models import AIEmployee
from app.services.authorization import ExecutionDecision


class AutonomyBlockedError(PermissionError):
    """El nivel de autonomía no permite ejecutar la acción."""


def _get_profile(db: Session, org_id: str, employee_id: str) -> EmployeeLaborProfile | None:
    return (
        db.query(EmployeeLaborProfile)
        .filter(
            EmployeeLaborProfile.organization_id == org_id,
            EmployeeLaborProfile.employee_id == employee_id,
        )
        .first()
    )


def resolve_autonomy_level(db: Session, org_id: str, employee: AIEmployee) -> str:
    profile = _get_profile(db, org_id, employee.id)
    if profile and profile.autonomy_level in AUTONOMY_LEVELS:
        return profile.autonomy_level
    return default_autonomy_for_employee(maturity=employee.maturity, shadow_mode=employee.shadow_mode)


def apply_autonomy_to_decision(
    db: Session,
    org_id: str,
    employee: AIEmployee,
    base_decision: ExecutionDecision,
) -> ExecutionDecision:
    """Ajusta la decisión de ejecución según autonomía y modo sombra."""
    if employee.shadow_mode:
        if base_decision == ExecutionDecision.ALLOW:
            return ExecutionDecision.REQUIRES_APPROVAL
        return base_decision

    level = resolve_autonomy_level(db, org_id, employee)
    if level == "RECOMIENDA":
        raise AutonomyBlockedError(
            "Autonomía RECOMIENDA: el empleado solo puede recomendar, no ejecutar herramientas."
        )
    if level == "PREPARA":
        return ExecutionDecision.REQUIRES_APPROVAL
    if level == "EJECUTA_CON_APROBACION":
        if base_decision == ExecutionDecision.ALLOW:
            return ExecutionDecision.REQUIRES_APPROVAL
        return base_decision
    # EJECUTA_DENTRO_LIMITES — respeta política existente (grants, límites, FinOps)
    return base_decision


def autonomy_execution_metadata(
    db: Session,
    org_id: str,
    employee: AIEmployee,
) -> dict[str, Any]:
    return {
        "autonomy_level": resolve_autonomy_level(db, org_id, employee),
        "shadow_mode": employee.shadow_mode,
        "maturity": employee.maturity,
        "adapter": "employee_20_autonomy_v1",
    }
