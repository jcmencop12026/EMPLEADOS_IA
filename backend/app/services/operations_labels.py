"""Etiquetas y utilidades del Centro de Operaciones — OPERACIONES-940."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.orchestration_models import WorkPlan

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

TERMINAL_STATUSES = frozenset({"COMPLETED", "CANCELLED", "FAILED"})

# Horas para considerar "próximo a vencer" (V1)
DUE_SOON_HOURS = 48

PRIORITY_LABELS: dict[str, str] = {
    "BAJA": "Baja",
    "MEDIA": "Media",
    "ALTA": "Alta",
    "CRITICA": "Crítica",
}

PRIORITY_ALIASES: dict[str, str] = {
    "BAJA": "BAJA",
    "Baja": "BAJA",
    "baja": "BAJA",
    "MEDIA": "MEDIA",
    "Media": "MEDIA",
    "media": "MEDIA",
    "Normal": "MEDIA",
    "normal": "MEDIA",
    "ALTA": "ALTA",
    "Alta": "ALTA",
    "alta": "ALTA",
    "CRITICA": "CRITICA",
    "Crítica": "CRITICA",
    "Critica": "CRITICA",
    "critica": "CRITICA",
    "crítica": "CRITICA",
}

PRIORITY_ORDER: dict[str, int] = {
    "CRITICA": 0,
    "ALTA": 1,
    "MEDIA": 2,
    "BAJA": 3,
}

SUMMARY_BUCKETS = {
    "running": {"RUNNING", "PARTIAL"},
    "pending": {"CREATED", "PLANNING", "READY"},
    "approval": {"WAITING_APPROVAL"},
    "error": {"FAILED"},
    "overdue": set(),
    "due_soon": set(),
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

DUE_STATE_LABELS = {
    "sin_vencimiento": "Sin vencimiento",
    "vencido": "Vencido",
    "vence_hoy": "Vence hoy",
    "proximo": "Próximo a vencer",
    "vigente": "Vigente",
}


def display_status(status: str) -> str:
    return DISPLAY_STATUS.get(status, status)


def priority_label(code: str | None) -> str:
    if not code:
        return PRIORITY_LABELS["MEDIA"]
    return PRIORITY_LABELS.get(code.upper(), code)


def normalize_priority(value: str) -> str:
    if value in PRIORITY_ALIASES:
        return PRIORITY_ALIASES[value]
    upper = value.upper()
    if upper in PRIORITY_LABELS:
        return upper
    raise ValueError(f"Prioridad inválida: {value}")


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_open_for_due(plan: WorkPlan) -> bool:
    return plan.status not in TERMINAL_STATUSES


def due_state(plan: WorkPlan, now: datetime | None = None) -> str:
    """Estado temporal calculado en backend."""
    now = now or datetime.now(timezone.utc)
    if plan.vencimiento is None:
        return "sin_vencimiento"
    if not is_open_for_due(plan):
        return "vigente"
    due = _aware(plan.vencimiento)
    if due < now:
        return "vencido"
    if due.date() == now.date():
        return "vence_hoy"
    if due <= now + timedelta(hours=DUE_SOON_HOURS):
        return "proximo"
    return "vigente"


def due_state_label(plan: WorkPlan, now: datetime | None = None) -> str:
    return DUE_STATE_LABELS.get(due_state(plan, now), "Vigente")


def is_overdue(plan: WorkPlan, now: datetime | None = None) -> bool:
    return due_state(plan, now) == "vencido"


def is_due_soon(plan: WorkPlan, now: datetime | None = None) -> bool:
    state = due_state(plan, now)
    return state in {"vence_hoy", "proximo"}


def task_progress(tasks: list) -> tuple[int, int]:
    if not tasks:
        return 0, 0
    done = sum(1 for task in tasks if task.status in {"COMPLETED", "CANCELLED"})
    return done, len(tasks)
