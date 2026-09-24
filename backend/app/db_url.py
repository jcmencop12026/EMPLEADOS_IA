"""Construcción segura de DATABASE_URL — contraseñas con caracteres especiales."""
from __future__ import annotations

import os

from sqlalchemy.engine import URL, make_url


def build_postgresql_url(
    *,
    username: str,
    password: str,
    host: str = "localhost",
    port: int = 5432,
    database: str,
    drivername: str = "postgresql+psycopg2",
) -> str:
    return URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    ).render_as_string(hide_password=False)


def resolve_database_url_from_environ() -> str | None:
    """Devuelve DATABASE_URL explícita o construida desde POSTGRES_*; None si no hay datos PG."""
    explicit = os.environ.get("DATABASE_URL", "").strip()
    if explicit:
        return explicit

    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    database = os.environ.get("POSTGRES_DB")
    if not (user and password and database):
        return None

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    return build_postgresql_url(
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def parse_database_password(database_url: str) -> str | None:
    """Round-trip de contraseña desde URL (para pruebas sin loguear el valor)."""
    return make_url(database_url).password
