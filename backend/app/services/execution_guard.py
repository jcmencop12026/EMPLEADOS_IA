"""Fencing de ejecución — CURSOR-810C v4 (ejecución vs materialización)."""
from __future__ import annotations

import contextvars
import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import text

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
        self._worker_sessions: list[Session] = []

    def register_worker_session(self, session: Session) -> None:
        with self._lock:
            self._worker_sessions.append(session)

    def unregister_worker_session(self, session: Session) -> None:
        with self._lock:
            try:
                self._worker_sessions.remove(session)
            except ValueError:
                pass

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
            sessions = list(self._worker_sessions)
            self._worker_sessions.clear()
        for proc in procs:
            terminate_process_tree(proc)
        for session in sessions:
            try:
                session.rollback()
            except Exception:  # noqa: BLE001 — invalidación best-effort
                pass

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


def require_execution_allowed(db: Session | None = None) -> None:
    from app.enums import AutomationRunStatus

    token = current_fence_token()
    if token is None:
        return
    controller = get_fence_controller(token.run_id)
    if controller is None or not controller.verify(token):
        raise ExecutionCancelledError("Ejecución cancelada por timeout")
    if db is not None:
        from app.services.execution_workspace import unwrap_db_session

        inner = unwrap_db_session(db)
        with inner.no_autoflush:
            status, generation = _read_run_fence_state(inner, token.run_id)
            if (
                status is None
                or generation != token.generation
                or status != AutomationRunStatus.RUNNING
            ):
                raise ExecutionCancelledError("Ejecución invalidada en BD")


def _validate_fence_for_persist(db: Session, token: FenceToken) -> None:
    from app.enums import AutomationRunStatus

    controller = get_fence_controller(token.run_id)
    if controller is None or not controller.verify(token):
        raise ExecutionCancelledError("Fence invalidado — persistencia rechazada")
    with db.no_autoflush:
        status, generation = _read_run_fence_state(db, token.run_id)
        if (
            status is None
            or generation != token.generation
            or status != AutomationRunStatus.RUNNING
        ):
            raise ExecutionCancelledError("Ejecución vencida — persistencia rechazada")


def flush_gated(db: Session) -> None:
    """Flush validado sin commit — fase worker."""
    from app.services.execution_workspace import unwrap_db_session

    inner = unwrap_db_session(db)
    token = current_fence_token()
    if token is None:
        inner.flush()
        return
    _validate_fence_for_persist(inner, token)
    inner.flush()


def materialize_gated(db: Session, token: FenceToken) -> None:
    """Único commit autorizado tras validación de generación/estado (dispatcher)."""
    from app.enums import AutomationRunStatus

    from app.services.execution_workspace import (
        reset_execution_phase,
        set_execution_phase,
        unwrap_db_session,
    )

    inner = unwrap_db_session(db)
    phase_token = set_execution_phase("materialization")
    fence_ctx = bind_fence_token(token)
    try:
        with inner.no_autoflush:
            status, generation = _read_run_fence_state(inner, token.run_id)
            if (
                status is None
                or generation != token.generation
                or status != AutomationRunStatus.RUNNING
            ):
                inner.rollback()
                raise ExecutionCancelledError("Ejecución vencida — materialización rechazada")

            controller = get_fence_controller(token.run_id)
            if controller is None or not controller.verify(token):
                inner.rollback()
                raise ExecutionCancelledError("Fence invalidado — materialización rechazada")

            _lock_run_for_update(inner, token.run_id)

        inner.flush()
        with inner.no_autoflush:
            status, generation = _read_run_fence_state(inner, token.run_id)
            if (
                status is None
                or generation != token.generation
                or status != AutomationRunStatus.RUNNING
            ):
                inner.rollback()
                raise ExecutionCancelledError("Ejecución vencida — materialización rechazada")
            controller = get_fence_controller(token.run_id)
            if controller is None or not controller.verify(token):
                inner.rollback()
                raise ExecutionCancelledError("Fence invalidado — materialización rechazada")

        inner.commit()
    finally:
        reset_execution_phase(phase_token)
        reset_fence_token(fence_ctx)


def commit_gated(db: Session) -> None:
    """Durante ejecución worker: flush validado. Fuera de fence: commit normal."""
    from app.services.execution_workspace import get_execution_phase, unwrap_db_session

    inner = unwrap_db_session(db)
    token = current_fence_token()
    if token is None:
        inner.commit()
        return

    phase = get_execution_phase()
    if phase == "worker":
        flush_gated(db)
        return

    if phase == "materialization":
        materialize_gated(db, token)
        return

    _commit_gated_legacy(inner, token)


def _commit_gated_legacy(db: Session, token: FenceToken) -> None:
    """Commit gated legacy (sin fase worker) — compat tests directos."""
    from app.enums import AutomationRunStatus

    with db.no_autoflush:
        status, generation = _read_run_fence_state(db, token.run_id)
        if (
            status is None
            or generation != token.generation
            or status != AutomationRunStatus.RUNNING
        ):
            db.rollback()
            raise ExecutionCancelledError("Ejecución vencida — commit rechazado")

        controller = get_fence_controller(token.run_id)
        if controller is None or not controller.verify(token):
            db.rollback()
            raise ExecutionCancelledError("Fence invalidado — commit rechazado")

        _lock_run_for_update(db, token.run_id)

    db.flush()
    with db.no_autoflush:
        status, generation = _read_run_fence_state(db, token.run_id)
        if (
            status is None
            or generation != token.generation
            or status != AutomationRunStatus.RUNNING
        ):
            db.rollback()
            raise ExecutionCancelledError("Ejecución vencida — commit rechazado")
        controller = get_fence_controller(token.run_id)
        if controller is None or not controller.verify(token):
            db.rollback()
            raise ExecutionCancelledError("Fence invalidado — commit rechazado")

    db.commit()


def _read_run_fence_state(db: Session, run_id: str) -> tuple[str | None, int | None]:
    row = db.execute(
        text("SELECT status, execution_generation FROM automation_runs WHERE id = :id"),
        {"id": run_id},
    ).one_or_none()
    if row is None:
        return None, None
    return str(row[0]), int(row[1])


def _lock_run_for_update(db: Session, run_id: str):
    from app.automation_models import AutomationRun

    return (
        db.query(AutomationRun)
        .filter(AutomationRun.id == run_id)
        .with_for_update()
        .populate_existing()
        .first()
    )


def invalidate_run_execution(
    db: Session,
    *,
    run: AutomationRun,
    token: FenceToken,
    error: str,
) -> bool:
    """Invalida fencing en BD y memoria con orden de locks consistente."""
    from app.enums import AutomationRunStatus

    controller = get_fence_controller(token.run_id)
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
    updated = False
    if row is None:
        db.rollback()
    else:
        row.status = AutomationRunStatus.FAILED
        row.error = error
        row.finished_at = _utcnow()
        row.execution_generation = token.generation + 1
        db.commit()
        db.refresh(row)
        if run in db:
            db.refresh(run)
        updated = True
    if controller:
        controller.invalidate()
    return updated


def run_subprocess(cmd: list[str], **kwargs) -> subprocess.Popen:
    """Lanza subprocess registrado para terminación en timeout."""
    token = current_fence_token()
    popen_kwargs = dict(kwargs)
    if os.name == "nt":
        creationflags = popen_kwargs.pop("creationflags", 0)
        popen_kwargs["creationflags"] = creationflags | subprocess.CREATE_NEW_PROCESS_GROUP
    elif "start_new_session" not in popen_kwargs:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **popen_kwargs)
    if token is not None:
        controller = get_fence_controller(token.run_id)
        if controller:
            controller.register_subprocess(proc)
    return proc


def promote_file_if_valid(tmp_path: str, final_path: str) -> bool:
    """Promueve archivo temporal solo si el fence sigue vigente."""
    from app.services.execution_workspace import current_worker_session

    require_execution_allowed(current_worker_session())
    if not os.path.exists(tmp_path):
        return False
    if os.path.exists(final_path):
        os.remove(final_path)
    os.replace(tmp_path, final_path)
    return True


def _list_child_pids(pid: int) -> list[int]:
    if os.name == "nt":
        try:
            out = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-CimInstance Win32_Process -Filter \"ParentProcessId={pid}\").ProcessId",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            children: list[int] = []
            for line in out.stdout.splitlines():
                line = line.strip()
                if line.isdigit():
                    val = int(line)
                    if val != pid:
                        children.append(val)
            return children
        except (OSError, subprocess.SubprocessError, ValueError):
            return []
    children: list[int] = []
    proc_root = "/proc"
    if not os.path.isdir(proc_root):
        return children
    for entry in os.listdir(proc_root):
        if not entry.isdigit():
            continue
        try:
            with open(os.path.join(proc_root, entry, "stat"), encoding="utf-8") as handle:
                stat = handle.read()
            ppid = int(stat.split()[3])
            if ppid == pid:
                children.append(int(entry))
        except (OSError, ValueError, IndexError):
            continue
    return children


def _signal_process_tree(pid: int, sig: signal.Signals) -> None:
    for child in _list_child_pids(pid):
        _signal_process_tree(child, sig)
    try:
        if os.name != "nt":
            os.kill(pid, sig)
    except (ProcessLookupError, OSError):
        pass


def terminate_process_tree(proc: subprocess.Popen) -> None:
    """Termina el árbol completo de procesos (padre + descendientes)."""
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                timeout=8,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            if proc.poll() is None:
                proc.kill()
        if proc.poll() is None:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        return

    if proc.poll() is not None:
        return

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, OSError):
        _signal_process_tree(proc.pid, signal.SIGTERM)
        try:
            proc.terminate()
        except (ProcessLookupError, OSError):
            pass

    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            _signal_process_tree(proc.pid, signal.SIGKILL)
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
        proc.wait(timeout=2)

    if proc.poll() is None:
        _signal_process_tree(proc.pid, signal.SIGKILL)
        try:
            proc.kill()
        except (ProcessLookupError, OSError):
            pass
        proc.wait(timeout=2)


def process_tree_alive(pid: int) -> bool:
    """Indica si un PID o alguno de sus descendientes sigue vivo."""
    parent_alive = True
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, OSError):
        parent_alive = False
    for child in _list_child_pids(pid):
        if process_tree_alive(child):
            return True
    return parent_alive


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
