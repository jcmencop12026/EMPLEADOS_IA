"""Guardia de cancelación cooperativa para ejecuciones con timeout (CURSOR-810C)."""
from __future__ import annotations

import contextvars
import threading


class RunExecutionGuard:
    """Marca una ejecución como cancelada (p. ej. timeout) para bloquear efectos posteriores."""

    def __init__(self) -> None:
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()


class ExecutionCancelledError(RuntimeError):
    pass


_guard_var: contextvars.ContextVar[RunExecutionGuard | None] = contextvars.ContextVar(
    "automation_execution_guard",
    default=None,
)


def bind_guard(guard: RunExecutionGuard) -> contextvars.Token:
    return _guard_var.set(guard)


def reset_guard(token: contextvars.Token) -> None:
    _guard_var.reset(token)


def current_guard() -> RunExecutionGuard | None:
    return _guard_var.get()


def execution_allowed() -> bool:
    guard = current_guard()
    return guard is None or not guard.cancelled


def require_execution_allowed() -> None:
    if not execution_allowed():
        raise ExecutionCancelledError("Ejecución cancelada por timeout")
