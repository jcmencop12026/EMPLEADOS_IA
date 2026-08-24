"""Gestión de ciclo de vida de conexiones SQLite/SQLAlchemy (CURSOR-805E)."""
from __future__ import annotations

import gc
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def database_url_to_path(database_url: str) -> Path:
    return Path(database_url.removeprefix("sqlite:///"))


def release_app_database_engine() -> None:
    """Cierra el engine global de app.database si ya fue importado."""
    try:
        from sqlalchemy.orm import close_all_sessions

        close_all_sessions()
        from app import database as app_database

        app_database.engine.dispose()
    except Exception:
        pass
    gc.collect()


def release_all_sqlite_handles(database_url: str | None = None) -> None:
    """Libera handles SQLAlchemy antes de operaciones filesystem sobre la BD."""
    release_app_database_engine()
    if database_url:
        _ = database_url_to_path(database_url)
    gc.collect()


@contextmanager
def sqlite_engine(db_path: Path) -> Iterator[Engine]:
    """Engine temporal con dispose garantizado al salir."""
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    try:
        yield engine
    finally:
        engine.dispose()
        gc.collect()


def safe_unlink_sqlite(db_path: Path, database_url: str | None = None) -> None:
    """Elimina archivo SQLite tras liberar todos los handles conocidos."""
    url = database_url or f"sqlite:///{db_path.as_posix()}"
    release_all_sqlite_handles(url)
    if db_path.exists():
        db_path.unlink()


def verify_sqlite_closed(db_path: Path) -> None:
    """Comprueba que el archivo SQLite puede abrirse/cerrarse sin handles residuales."""
    conn = sqlite3.connect(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"integrity_check falló: {integrity}")
    finally:
        conn.close()
