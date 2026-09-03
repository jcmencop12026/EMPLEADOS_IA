"""Constantes — Empleado IA 2.0 (evolución aislada)."""

from __future__ import annotations

from app.enums import EmployeeLifecycleStatus, EmployeeMaturity

# Niveles de autonomía controlada
AUTONOMY_LEVELS = frozenset({
    "RECOMIENDA",
    "PREPARA",
    "EJECUTA_CON_APROBACION",
    "EJECUTA_DENTRO_LIMITES",
})

# Vocabulario misión → fase funcional (sin cambiar valores API de lifecycle_status)
LIFECYCLE_MISSION_PHASE = {
    EmployeeLifecycleStatus.DRAFT: "BORRADOR",
    EmployeeLifecycleStatus.CONFIGURING: "CONFIGURACION",
    EmployeeLifecycleStatus.READY_FOR_TEST: "CONFIGURACION",
    EmployeeLifecycleStatus.TESTING: "PRUEBAS",
    EmployeeLifecycleStatus.FAILED_TEST: "PRUEBAS",
    EmployeeLifecycleStatus.READY_FOR_CERTIFICATION: "PRUEBAS",
    EmployeeLifecycleStatus.CERTIFIED: "APROBADO",
    EmployeeLifecycleStatus.PUBLISHED: "APROBADO",
    EmployeeLifecycleStatus.ACTIVE: "ACTIVO",
    EmployeeLifecycleStatus.PAUSED: "SUSPENDIDO",
    EmployeeLifecycleStatus.RETIRED: "RETIRADO",
}

# Conceptos sin estado lifecycle dedicado — derivados
LIFECYCLE_CONCEPT_SANDBOX = "SANDBOX"  # TestLab + TESTING
LIFECYCLE_CONCEPT_MODO_SOMBRA = "MODO_SOMBRA"  # shadow_mode + maturity SHADOW

SUPERVISION_EVENT_TYPES = frozenset({
    "TRABAJO_ASIGNADO",
    "TRABAJO_COMPLETADO",
    "ERROR",
    "REINTENTO",
    "INTERVENCION_HUMANA",
    "ESCALAMIENTO",
    "APROBACION",
    "CALIDAD",
    "CUMPLIMIENTO",
    "RESULTADO",
})

LEARNING_PROPOSAL_STATES = frozenset({
    "OBSERVACION",
    "PROPUESTA",
    "APROBADA",
    "RECHAZADA",
    "EN_PRUEBA",
    "PROMOVIDA",
})


def default_autonomy_for_employee(*, maturity: str, shadow_mode: bool) -> str:
    if shadow_mode or maturity == EmployeeMaturity.SHADOW:
        return "EJECUTA_CON_APROBACION"
    if maturity in (EmployeeMaturity.DRAFT, EmployeeMaturity.LAB):
        return "PREPARA"
    if maturity == EmployeeMaturity.SUPERVISED:
        return "EJECUTA_CON_APROBACION"
    return "EJECUTA_DENTRO_LIMITES"


def mission_phase_for_employee(
    lifecycle_status: str,
    *,
    shadow_mode: bool = False,
    in_test_lab: bool = False,
) -> str:
    """Fase misión incluyendo conceptos derivados SANDBOX / MODO_SOMBRA."""
    if shadow_mode:
        return LIFECYCLE_CONCEPT_MODO_SOMBRA
    if in_test_lab or lifecycle_status in (
        EmployeeLifecycleStatus.TESTING,
        EmployeeLifecycleStatus.FAILED_TEST,
        EmployeeLifecycleStatus.READY_FOR_TEST,
    ):
        if lifecycle_status == EmployeeLifecycleStatus.TESTING:
            return LIFECYCLE_CONCEPT_SANDBOX
    return LIFECYCLE_MISSION_PHASE.get(lifecycle_status, lifecycle_status)
