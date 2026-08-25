"""Frontera ejecución/materialización — CURSOR-810C v4.

Los workers cancelables reciben una sesión restringida sin autoridad de commit
ni acceso a engine/conexión. Solo el dispatcher materializa tras validar fence.
"""
from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.services.execution_guard import ExecutionCancelledError

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_execution_phase: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "automation_execution_phase",
    default=None,
)
_worker_session_var: contextvars.ContextVar[Session | None] = contextvars.ContextVar(
    "automation_worker_session",
    default=None,
)


class WorkerCommitForbiddenError(ExecutionCancelledError):
    """El worker intentó confirmar o acceder a conexión sin autorización."""


def get_execution_phase() -> str | None:
    return _execution_phase.get()


def set_execution_phase(phase: str | None) -> contextvars.Token:
    return _execution_phase.set(phase)


def reset_execution_phase(token: contextvars.Token) -> None:
    _execution_phase.reset(token)


def bind_worker_session(session: Session | None) -> contextvars.Token:
    return _worker_session_var.set(session)


def reset_worker_session(token: contextvars.Token) -> None:
    _worker_session_var.reset(token)


def current_worker_session() -> Session | None:
    return _worker_session_var.get()


class WorkerExecutionSession:
    """Proxy de Session sin commit ni acceso a engine/conexión cruda."""

    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        object.__setattr__(self, "_session", session)

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede invocar commit(); "
            "la materialización la controla el dispatcher."
        )

    def get_bind(self):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede obtener engine/bind."
        )

    def connection(self, *args, **kwargs):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede abrir connection()."
        )

    def bind_mapper(self, *args, **kwargs):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede acceder a bind_mapper()."
        )

    def bind_table(self, *args, **kwargs):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede acceder a bind_table()."
        )

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        self._session.close()

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    def __setattr__(self, name: str, value) -> None:
        if name == "_session":
            object.__setattr__(self, name, value)
        else:
            setattr(self._session, name, value)


class GuardedEngine:
    """Engine proxy que bloquea commit en conexiones durante ejecución cancelable."""

    __slots__ = ("_engine",)

    def __init__(self, engine: Engine) -> None:
        object.__setattr__(self, "_engine", engine)

    def connect(self, *args, **kwargs):
        from app.services.execution_guard import current_fence_token, require_execution_allowed

        if current_fence_token() is not None:
            require_execution_allowed()
        conn = self._engine.connect(*args, **kwargs)
        return _GuardedConnection(conn)

    def __getattr__(self, name: str):
        return getattr(self._engine, name)


class _GuardedConnection:
    __slots__ = ("_conn",)

    def __init__(self, conn) -> None:
        object.__setattr__(self, "_conn", conn)

    def commit(self) -> None:
        from app.services.execution_guard import current_fence_token

        if current_fence_token() is not None:
            raise WorkerCommitForbiddenError(
                "Ejecución cancelable: commit en conexión cruda bloqueado."
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __getattr__(self, name: str):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def wrap_engine_if_guarded(engine: Engine) -> Engine:
    from app.services.execution_guard import current_fence_token

    if current_fence_token() is not None:
        return GuardedEngine(engine)  # type: ignore[return-value]
    return engine
