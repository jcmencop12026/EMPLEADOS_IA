"""Frontera ejecución/materialización — CURSOR-810C v4.1.

Los workers cancelables reciben una interfaz DB mínima. La Session SQLAlchemy real
vive en un registro interno inaccesible desde la capacidad entregada al worker.
"""
from __future__ import annotations

import contextvars
import re
import weakref
from typing import Any

from sqlalchemy.orm import Session

from app.services.execution_guard import ExecutionCancelledError, flush_gated

_execution_phase: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "automation_execution_phase",
    default=None,
)
_worker_inner_session_var: contextvars.ContextVar[Session | None] = contextvars.ContextVar(
    "automation_worker_inner_session",
    default=None,
)

_TRANSACTION_SQL = re.compile(
    r"^\s*(COMMIT|ROLLBACK|BEGIN(\s+TRANSACTION)?|SAVEPOINT|RELEASE|END\s+TRANSACTION)\b",
    re.IGNORECASE,
)


class WorkerCommitForbiddenError(ExecutionCancelledError):
    """El worker intentó confirmar o acceder a conexión sin autorización."""


class WorkerExecutionSession:
    """Interfaz DB mínima para workers — sin Session/Engine/Connection expuestos."""

    __slots__ = ("__weakref__",)

    def query(self, *entities: Any, **kwargs: Any):
        return _resolve_inner(self).query(*entities, **kwargs)

    def add(self, instance: object, _warn: bool = True) -> None:
        _resolve_inner(self).add(instance, _warn=_warn)

    def add_all(self, instances: Any) -> None:
        _resolve_inner(self).add_all(instances)

    def delete(self, instance: object) -> None:
        _resolve_inner(self).delete(instance)

    def execute(self, statement: Any, params: Any = None, **kwargs: Any):
        _guard_sql(statement)
        inner = _resolve_inner(self)
        if params is not None:
            return inner.execute(statement, params, **kwargs)
        return inner.execute(statement, **kwargs)

    def flush(self, objects: Any = None) -> None:
        flush_gated(_resolve_inner(self))

    def refresh(
        self,
        instance: object,
        attribute_names: Any = None,
        with_for_update: Any = None,
    ) -> None:
        inner = _resolve_inner(self)
        if attribute_names is not None or with_for_update is not None:
            inner.refresh(instance, attribute_names=attribute_names, with_for_update=with_for_update)
        else:
            inner.refresh(instance)

    def expunge(self, instance: object) -> None:
        _resolve_inner(self).expunge(instance)

    def merge(self, instance: object, *, load: bool = True, options: Any = None):
        inner = _resolve_inner(self)
        if options is not None:
            return inner.merge(instance, load=load, options=options)
        return inner.merge(instance, load=load)

    def rollback(self) -> None:
        _resolve_inner(self).rollback()

    def commit(self) -> None:
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede invocar commit(); "
            "la materialización la controla el dispatcher."
        )

    def get_bind(self):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede obtener engine/bind."
        )

    def connection(self, *args: Any, **kwargs: Any):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede abrir connection()."
        )

    def bind_mapper(self, *args: Any, **kwargs: Any):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede acceder a bind_mapper()."
        )

    def bind_table(self, *args: Any, **kwargs: Any):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede acceder a bind_table()."
        )

    def begin(self, *args: Any, **kwargs: Any):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede iniciar transacciones."
        )

    def close(self) -> None:
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: el worker no puede cerrar la sesión propietaria."
        )

    @property
    def session(self):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: Session interna no expuesta al worker."
        )

    def __getattr__(self, name: str):
        if name in {"_session", "__dict__", "__weakref__"}:
            raise WorkerCommitForbiddenError(
                f"Ejecución cancelable: atributo '{name}' no disponible para el worker."
            )
        raise AttributeError(f"{type(self).__name__!r} no expone {name!r}")


# Registro interno: facade → Session real (no expuesto al worker).
_facade_registry: weakref.WeakKeyDictionary[WorkerExecutionSession, Session] = (
    weakref.WeakKeyDictionary()
)


def get_execution_phase() -> str | None:
    return _execution_phase.get()


def set_execution_phase(phase: str | None) -> contextvars.Token:
    return _execution_phase.set(phase)


def reset_execution_phase(token: contextvars.Token) -> None:
    _execution_phase.reset(token)


def bind_worker_session(session: Session | None) -> contextvars.Token:
    return _worker_inner_session_var.set(session)


def reset_worker_session(token: contextvars.Token) -> None:
    _worker_inner_session_var.reset(token)


def current_worker_session() -> Session | None:
    return _worker_inner_session_var.get()


def _resolve_inner(facade: WorkerExecutionSession) -> Session:
    try:
        return _facade_registry[facade]
    except KeyError as exc:
        raise RuntimeError("Sesión worker no registrada") from exc


def create_worker_execution_session(inner: Session) -> WorkerExecutionSession:
    """Crea facade worker; la Session real queda solo en registro interno."""
    facade = WorkerExecutionSession.__new__(WorkerExecutionSession)
    _facade_registry[facade] = inner
    return facade


def resolve_inner_session(facade: WorkerExecutionSession) -> Session:
    """Solo para dispatcher/controlador — nunca entregar al código worker."""
    return _resolve_inner(facade)


def unwrap_db_session(db: Session | WorkerExecutionSession) -> Session:
    """Resuelve facade worker a Session real para capa de guardia/dispatcher."""
    if isinstance(db, WorkerExecutionSession):
        return _resolve_inner(db)
    return db


def release_worker_session(facade: WorkerExecutionSession, *, close: bool = True) -> None:
    inner = _facade_registry.pop(facade, None)
    if inner is not None and close:
        inner.close()


def _guard_sql(statement: Any) -> None:
    sql: str | None = None
    if isinstance(statement, str):
        sql = statement
    else:
        text = getattr(statement, "text", None)
        if text is not None:
            sql = str(text)
    if sql and _TRANSACTION_SQL.search(sql.strip()):
        raise WorkerCommitForbiddenError(
            "Ejecución cancelable: SQL transaccional (COMMIT/ROLLBACK/BEGIN/…) bloqueado."
        )
