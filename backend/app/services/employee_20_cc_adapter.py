"""Adapter señales Centro de Control — sin modificar CC estable."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.employee_20_models import EmployeeLearningProposal, EmployeePerformanceIndicator
from app.enums import EmployeeLifecycleStatus
from app.orchestration_models import AIEmployee, ApprovalRequest, FinOpsRecord


def collect_control_center_signals(db: Session, org_id: str) -> dict[str, Any]:
    """Señales preparadas para integración futura con Centro de Control."""
    empleados_problema = (
        db.query(AIEmployee)
        .filter(
            AIEmployee.organization_id == org_id,
            AIEmployee.lifecycle_status.in_([
                EmployeeLifecycleStatus.FAILED_TEST,
                EmployeeLifecycleStatus.PAUSED,
            ]),
        )
        .count()
    )
    aprobaciones_pendientes = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.organization_id == org_id,
            ApprovalRequest.status == "PENDING",
        )
        .count()
    )
    alertas_indicadores = (
        db.query(EmployeePerformanceIndicator)
        .filter(
            EmployeePerformanceIndicator.organization_id == org_id,
            EmployeePerformanceIndicator.alerta.isnot(None),
        )
        .count()
    )
    propuestas_mejora = (
        db.query(EmployeeLearningProposal)
        .filter(
            EmployeeLearningProposal.organization_id == org_id,
            EmployeeLearningProposal.estado.in_(("PROPUESTA", "EN_PRUEBA")),
        )
        .count()
    )
    costo_hoy = (
        db.query(func.coalesce(func.sum(FinOpsRecord.cost), 0.0))
        .filter(FinOpsRecord.organization_id == org_id)
        .scalar()
    ) or 0.0

    return {
        "adapter": "employee_20_cc_signals_v1",
        "integrado": False,
        "nota": "Señales listas para consumo por Centro de Control — no modifica CC estable.",
        "senal": {
            "empleados_con_problemas": empleados_problema,
            "aprobaciones_pendientes": aprobaciones_pendientes,
            "indicadores_en_alerta": alertas_indicadores,
            "propuestas_mejora_pendientes": propuestas_mejora,
            "consumo_acumulado": float(costo_hoy),
        },
    }
