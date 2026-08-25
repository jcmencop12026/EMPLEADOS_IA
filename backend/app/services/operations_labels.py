"""Etiquetas y utilidades del Centro de Operaciones — OPERACIONES-940."""
from __future__ import annotations

DISPLAY_STATUS: dict[str, str] = {
    "CREATED": "Pendiente",
    "PLANNING": "Preparando",
    "READY": "Pendiente",
    "RUNNING": "En ejecución",
    "WAITING_DATA": "Pausado",
    "WAITING_APPROVAL": "Esperando aprobación",
    "PARTIAL": "En ejecución",
    "FAILED": "Fallido",
    "COMPLETED": "Completado",
    "CANCELLED": "Cancelado",
}

SUMMARY_BUCKETS = {
    "running": {"RUNNING", "PARTIAL"},
    "pending": {"CREATED", "PLANNING", "READY"},
    "approval": {"WAITING_APPROVAL"},
    "error": {"FAILED"},
    "overdue": set(),
}

APPROVAL_LABELS = {
    "NOT_REQUIRED": "No requerida",
    "PENDING": "Pendiente",
    "APPROVED": "Aprobada",
    "REJECTED": "Rechazada",
}

EVENT_LABELS = {
    "work.requested": "Solicitud creada",
    "work.planned": "Plan definido",
    "task.created": "Tarea creada",
    "task.started": "Tarea iniciada",
    "task.completed": "Tarea completada",
    "task.failed": "Tarea fallida",
    "approval.required": "Aprobación requerida",
    "approval.completed": "Aprobación completada",
    "work.completed": "Trabajo completado",
    "work.failed": "Trabajo fallido",
    "work.cancelled": "Trabajo cancelado",
}


def display_status(status: str) -> str:
    return DISPLAY_STATUS.get(status, status)


def task_progress(tasks: list) -> tuple[int, int]:
    if not tasks:
        return 0, 0
    done = sum(1 for task in tasks if task.status in {"COMPLETED", "CANCELLED"})
    return done, len(tasks)
