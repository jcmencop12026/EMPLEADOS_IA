"""Fencing de ejecución commit-gated para timeouts de automatizaciones (CURSOR-810C v2)."""
from __future__ import annotations

import contextvars
import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.automation_models import AutomationRun


class ExecutionCancelledError(RuntimeError):
    """La ejecución fue cancelada o venció; no se permiten efectos confirmados."""


@dataclass(frozen=True)
class FenceToken:
    run_id: str
    generation: int


class RunFenceController:
    """Controlador atómico de generación/fencing por ejecución."""

    def __init__(self, run_id: str, generation: int) -> None:
        self.run_id = run_id
        self._generation = generation
        self._lock = threading.Lock()
        self._subprocesses: list[subprocess.Popen] = []

    def snapshot(self) -> FenceToken:
        with self._lock:
            return FenceToken(self.run_id, self._generation)

    def verify(self, token: FenceToken) -> bool:
        with self._lock:
            return token.run_id == self.run_id and token.generation == self._generation

    def invalidate(self) -> None:
        with self._lock:
            self._generation += 1
            procs = list(self._subprocesses)
            self._subprocesses.clear()
        for proc in procs:
            _terminate_process_tree(proc)

    def register_subprocess(self, proc: subprocess.Popen) -> None:
        with self._lock:
            self._subprocesses.append(proc)

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation


_controllers: dict[str, RunFenceController] = {}
_controllers_lock = threading.Lock()

_fence_token_var: contextvars.ContextVar[FenceToken | None] = contextvars.ContextVar(
    "automation_fence_token",
    default=None,
)


def bind_fence_token(token: FenceToken | None) -> contextvars.Token:
    return _fence_token_var.set(token)


def reset_fence_token(ctx_token: contextvars.Token) -> None:
    _fence_token_var.reset(ctx_token)


def current_fence_token() -> FenceToken | None:
    return _fence_token_var.get()


def register_fence(run_id: str, generation: int) -> RunFenceController:
    controller = RunFenceController(run_id, generation)
    with _controllers_lock:
        _controllers[run_id] = controller
    return controller


def get_fence_controller(run_id: str) -> RunFenceController | None:
    with _controllers_lock:
        return _controllers.get(run_id)


def release_fence(run_id: str) -> None:
    with _controllers_lock:
        _controllers.pop(run_id, None)


def require_execution_allowed() -> None:
    token = current_fence_token()
    if token is None:
        return
    controller = get_fence_controller(token.run_id)
    if controller is None or not controller.verify(token):
        raise ExecutionCancelledError("Ejecución cancelada por timeout")


def commit_gated(db: Session) -> None:
    """Confirma cambios solo si el fencing de ejecución sigue vigente."""
    from app.automation_models import AutomationRun
    from app.enums import AutomationRunStatus

    token = current_fence_token()
    if token is None:
        db.commit()
        return

    controller = get_fence_controller(token.run_id)
    if controller is None or not controller.verify(token):
        db.rollback()
        raise ExecutionCancelledError("Fence invalidado — commit rechazado")

    row = (
        db.query(AutomationRun)
        .filter(AutomationRun.id == token.run_id)
        .with_for_update()
        .first()
    )
    if (
        row is None
        or row.execution_generation != token.generation
        or row.status != AutomationRunStatus.RUNNING
    ):
        db.rollback()
        raise ExecutionCancelledError("Ejecución vencida — commit rechazado")
    db.commit()


def invalidate_run_execution(
    db: Session,
    *,
    run: AutomationRun,
    token: FenceToken,
    error: str,
) -> bool:
    """Invalida fencing en memoria y en BD de forma atómica."""
    from app.enums import AutomationRunStatus

    controller = get_fence_controller(token.run_id)
    if controller:
        controller.invalidate()

    row = (
        db.query(type(run))
        .filter(
            type(run).id == run.id,
            type(run).execution_generation == token.generation,
            type(run).status == AutomationRunStatus.RUNNING,
        )
        .with_for_update()
        .first()
    )
    if row is None:
        db.rollback()
        return False

    row.status = AutomationRunStatus.FAILED
    row.error = error
    row.finished_at = _utcnow()
    row.execution_generation = token.generation + 1
    db.commit()
    db.refresh(run)
    return True


def run_subprocess(cmd: list[str], **kwargs) -> subprocess.Popen:
    """Lanza subprocess registrado para terminación en timeout."""
    token = current_fence_token()
    popen_kwargs = dict(kwargs)
    if os.name != "nt" and "start_new_session" not in popen_kwargs:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **popen_kwargs)
    if token is not None:
        controller = get_fence_controller(token.run_id)
        if controller:
            controller.register_subprocess(proc)
    return proc


def promote_file_if_valid(tmp_path: str, final_path: str) -> bool:
    """Promueve archivo temporal solo si el fence sigue vigente."""
    require_execution_allowed()
    if not os.path.exists(tmp_path):
        return False
    if os.path.exists(final_path):
        os.remove(final_path)
    os.replace(tmp_path, final_path)
    return True


def _terminate_process_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, OSError):
        proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            if os.name != "nt":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, OSError):
            proc.kill()
        proc.wait(timeout=2)


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
