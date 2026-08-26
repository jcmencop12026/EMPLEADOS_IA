"""Sesión limitada para listeners del event bus — sin commit externo."""
from __future__ import annotations

from sqlalchemy.orm import Session


class SubscriberCommitForbiddenError(RuntimeError):
    """Un listener intentó confirmar la transacción externa."""


class SubscriberSession:
    """Proxy de Session que impide commit/rollback de la transacción propietaria."""

    __slots__ = ("_session",)

    def __init__(self, session: Session) -> None:
        object.__setattr__(self, "_session", session)

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        raise SubscriberCommitForbiddenError(
            "Los listeners del event bus no pueden invocar commit(); use flush()."
        )

    def rollback(self) -> None:
        raise SubscriberCommitForbiddenError(
            "Los listeners del event bus no pueden invocar rollback(); el dispatcher controla SAVEPOINT."
        )

    def close(self) -> None:
        raise SubscriberCommitForbiddenError(
            "Los listeners del event bus no pueden cerrar la sesión propietaria."
        )

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    def __setattr__(self, name: str, value) -> None:
        if name == "_session":
            object.__setattr__(self, name, value)
        else:
            setattr(self._session, name, value)
