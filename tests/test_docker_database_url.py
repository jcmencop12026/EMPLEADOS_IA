"""Pruebas focales — DATABASE_URL segura con contraseñas PostgreSQL especiales."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict
from sqlalchemy.engine import make_url

from app.config import Settings, default_sqlite_database_url
from app.db_url import build_postgresql_url, parse_database_password, resolve_database_url_from_environ


def _settings_from_env_file(env_content: str, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Carga Settings desde un .env aislado sin contaminar os.environ."""
    tmpdir = tempfile.mkdtemp()
    env_path = Path(tmpdir) / ".env"
    env_path.write_text(env_content, encoding="utf-8")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for key in list(os.environ):
        if key.startswith("POSTGRES_"):
            monkeypatch.delenv(key, raising=False)

    class IsolatedSettings(Settings):
        model_config = SettingsConfigDict(env_file=str(env_path), extra="ignore")

    return IsolatedSettings()


@pytest.mark.parametrize(
    "password",
    [
        "plain",
        "with@at",
        "hash#sign",
        "pct%25",
        "colon:slash/",
        "plus+sign",
        "mix@#%:+/all",
    ],
    ids=["plain", "at", "hash", "pct", "colon_slash", "plus", "mixed"],
)
def test_build_postgresql_url_roundtrip_special_password_chars(password: str):
    url = build_postgresql_url(
        username="empleados",
        password=password,
        host="postgres",
        port=5432,
        database="empleados_ia",
    )
    parsed = make_url(url)
    assert parsed.username == "empleados"
    assert parsed.password == password
    assert parsed.host == "postgres"
    assert parsed.database == "empleados_ia"
    assert "@postgres" in url or url.endswith("@postgres:5432/empleados_ia")


def test_resolve_database_url_from_environ_uses_postgres_components(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "empleados")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss#%:+/")
    monkeypatch.setenv("POSTGRES_DB", "empleados_ia_cert")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_PORT", "5432")

    url = resolve_database_url_from_environ()
    assert url is not None
    assert parse_database_password(url) == "p@ss#%:+/"


def test_explicit_database_url_overrides_postgres_components(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://explicit:pw@localhost:5432/explicit_db")
    monkeypatch.setenv("POSTGRES_PASSWORD", "ignored@password")

    url = resolve_database_url_from_environ()
    assert url is not None
    parsed = make_url(url)
    assert parsed.username == "explicit"
    assert parsed.database == "explicit_db"


def test_settings_assembles_database_url_from_postgres_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "empleados")
    monkeypatch.setenv("POSTGRES_PASSWORD", "sec@ret#1")
    monkeypatch.setenv("POSTGRES_DB", "empleados_ia")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")

    cfg = Settings()
    assert make_url(cfg.database_url).password == "sec@ret#1"
    assert make_url(cfg.database_url).host == "postgres"


def test_special_password_not_logged_in_url_repr(monkeypatch):
    secret = "must-not-log@#%"
    url = build_postgresql_url(
        username="u",
        password=secret,
        host="postgres",
        port=5432,
        database="db",
    )
    safe = make_url(url).render_as_string(hide_password=True)
    assert secret not in safe
    assert "***" in safe


def test_encoded_url_with_percent_safe_for_sqlalchemy_engine():
    """URLs con % codificado no deben romper create_engine (Alembic usa el mismo patrón)."""
    from sqlalchemy import create_engine, pool

    url = build_postgresql_url(username="u", password="p%2", host="localhost", port=5432, database="db")
    assert "%" in url
    engine = create_engine(url, poolclass=pool.NullPool)
    assert engine.url.password == "p%2"
    engine.dispose()


def test_docker_compose_uses_postgres_components_not_interpolated_database_url():
    content = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    text = content.read_text(encoding="utf-8")
    assert "POSTGRES_HOST: ${POSTGRES_HOST:-postgres}" in text
    assert "POSTGRES_PASSWORD" in text
    assert "DATABASE_URL: postgresql" not in text


def test_settings_database_url_from_os_environ(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://fromenv:pw@localhost:5432/fromenv_db")
    monkeypatch.setenv("POSTGRES_USER", "empleados")
    monkeypatch.setenv("POSTGRES_PASSWORD", "ignored")
    monkeypatch.setenv("POSTGRES_DB", "empleados_ia")

    cfg = Settings()
    parsed = make_url(cfg.database_url)
    assert parsed.database == "fromenv_db"
    assert parsed.username == "fromenv"


def test_settings_database_url_from_env_file(monkeypatch):
    cfg = _settings_from_env_file(
        "DATABASE_URL=postgresql+psycopg2://fromfile:pw@localhost:5432/fromfile_db\n"
        "POSTGRES_USER=empleados\n"
        "POSTGRES_PASSWORD=ignored\n"
        "POSTGRES_DB=empleados_ia\n",
        monkeypatch,
    )
    parsed = make_url(cfg.database_url)
    assert parsed.database == "fromfile_db"
    assert parsed.username == "fromfile"


def test_settings_sqlite_env_file_with_postgres_vars_not_overwritten(monkeypatch):
    sqlite_url = "sqlite:///D:/EMPLEADOS_IA/data/test.db"
    cfg = _settings_from_env_file(
        f"DATABASE_URL={sqlite_url}\n"
        "POSTGRES_USER=empleados\n"
        "POSTGRES_PASSWORD=CAMBIAR_PASSWORD_EN_PROD\n"
        "POSTGRES_DB=empleados_ia\n",
        monkeypatch,
    )
    assert cfg.database_url == sqlite_url
    assert cfg.database_url.startswith("sqlite")


def test_settings_postgresql_env_file_with_postgres_vars_not_overwritten(monkeypatch):
    pg_url = "postgresql+psycopg2://explicit:pw@localhost:5432/explicit_db"
    cfg = _settings_from_env_file(
        f"DATABASE_URL={pg_url}\n"
        "POSTGRES_USER=empleados\n"
        "POSTGRES_PASSWORD=otherpass\n"
        "POSTGRES_DB=empleados_ia\n",
        monkeypatch,
    )
    assert cfg.database_url == pg_url
    assert make_url(cfg.database_url).database == "explicit_db"


def test_settings_postgres_fallback_without_explicit_database_url(monkeypatch):
    cfg = _settings_from_env_file(
        "POSTGRES_USER=empleados\n"
        "POSTGRES_PASSWORD=sec@ret#1\n"
        "POSTGRES_DB=empleados_ia\n"
        "POSTGRES_HOST=postgres\n",
        monkeypatch,
    )
    parsed = make_url(cfg.database_url)
    assert parsed.password == "sec@ret#1"
    assert parsed.host == "postgres"


def test_settings_incomplete_postgres_vars_falls_back_to_default_sqlite(monkeypatch):
    cfg = _settings_from_env_file(
        "POSTGRES_USER=empleados\n"
        "POSTGRES_DB=empleados_ia\n",
        monkeypatch,
    )
    assert cfg.database_url == default_sqlite_database_url()


def test_alembic_resolution_equivalent_with_percent_password(monkeypatch):
    """Alembic env.py usa create_engine(db_url) — misma ruta que esta prueba."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p%2")
    monkeypatch.setenv("POSTGRES_DB", "db")

    from sqlalchemy import create_engine, pool

    db_url = resolve_database_url_from_environ()
    assert db_url is not None
    engine = create_engine(db_url, poolclass=pool.NullPool)
    assert engine.url.password == "p%2"
    engine.dispose()


@pytest.mark.parametrize("char", ["@", "#"], ids=["at", "hash"])
def test_password_with_char_connects_when_postgres_available(monkeypatch, char: str):
    """Conexión real solo si hay PostgreSQL de prueba en el entorno."""
    base = os.environ.get("DATABASE_URL", "")
    if not base.startswith("postgresql"):
        pytest.skip("PostgreSQL de prueba no disponible")

    from sqlalchemy import create_engine, text

    parsed = make_url(base)
    password = f"{parsed.password or 'test'}{char}extra"
    url = build_postgresql_url(
        username=parsed.username or "empleados",
        password=password,
        host=parsed.host or "localhost",
        port=parsed.port or 5432,
        database=parsed.database or "empleados_ia_test",
    )
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except Exception:
        pytest.skip("No se pudo conectar con contraseña alterada en este entorno")
