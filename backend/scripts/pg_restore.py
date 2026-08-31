#!/usr/bin/env python3
"""Restore controlado PostgreSQL para EMPLEADOS_IA V1."""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402

logger = logging.getLogger("empleados_ia.restore")


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + database_url.split("://", 1)[1]
    return database_url


def _parse_pg_url(database_url: str) -> dict[str, str]:
    normalized = _normalize_database_url(database_url)
    if not normalized.startswith("postgresql://"):
        raise ValueError(
            "Restore V1 solo soporta PostgreSQL. "
            f"URL actual: {normalized.split('://', 1)[0]}://..."
        )
    parsed = urlparse(normalized)
    if not parsed.hostname or not parsed.path:
        raise ValueError("DATABASE_URL PostgreSQL inválida")
    return {
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": parsed.path.lstrip("/"),
    }


def _require_psql() -> str:
    psql = shutil.which("psql")
    if not psql:
        raise RuntimeError(
            "psql no encontrado en PATH. Instale el cliente PostgreSQL "
            "(postgresql-client / postgresql16-client)."
        )
    return psql


def _validate_guards(target_env: str, *, confirm_destructive: bool, confirm_prod: bool) -> None:
    if not confirm_destructive:
        raise RuntimeError(
            "Operación destructiva bloqueada. Use --confirm-destructive para continuar."
        )
    if target_env == "prod" and not confirm_prod:
        raise RuntimeError(
            "Restore en PROD bloqueado. Use --confirm-prod además de --confirm-destructive."
        )


def run_restore(
    *,
    database_url: str,
    backup_file: Path,
    target_env: str,
    confirm_destructive: bool,
    confirm_prod: bool,
    verbose: bool = False,
) -> None:
    _configure_logging(verbose)
    _validate_guards(
        target_env,
        confirm_destructive=confirm_destructive,
        confirm_prod=confirm_prod,
    )

    if not backup_file.exists():
        raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_file}")
    if backup_file.stat().st_size == 0:
        raise ValueError(f"Archivo de backup vacío: {backup_file}")

    psql = _require_psql()
    params = _parse_pg_url(database_url)

    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = params["password"]

    logger.warning(
        "RESTORE DESTRUCTIVO env=%s host=%s db=%s archivo=%s",
        target_env,
        params["host"],
        params["dbname"],
        backup_file,
    )

    command = [
        psql,
        "--host",
        params["host"],
        "--port",
        params["port"],
        "--username",
        params["user"],
        "--dbname",
        params["dbname"],
        "--single-transaction",
        "--set",
        "ON_ERROR_STOP=1",
        "--file",
        str(backup_file),
    ]

    try:
        subprocess.run(command, check=True, env=env, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.error("Restore falló (exit=%s): %s", exc.returncode, exc.stderr.strip())
        raise RuntimeError("Restore PostgreSQL falló") from exc

    logger.info("Restore completado correctamente en %s", params["dbname"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore PostgreSQL EMPLEADOS_IA V1")
    parser.add_argument("--file", required=True, help="Ruta al archivo .sql de backup")
    parser.add_argument(
        "--env",
        choices=["test", "prod", "other"],
        required=True,
        help="Ambiente destino (guardas de seguridad)",
    )
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", settings.database_url))
    parser.add_argument(
        "--confirm-destructive",
        action="store_true",
        help="Confirma que se sobrescribirán datos existentes",
    )
    parser.add_argument(
        "--confirm-prod",
        action="store_true",
        help="Guarda adicional obligatoria para ambiente PROD",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    try:
        run_restore(
            database_url=args.database_url,
            backup_file=Path(args.file),
            target_env=args.env,
            confirm_destructive=args.confirm_destructive,
            confirm_prod=args.confirm_prod,
            verbose=args.verbose,
        )
        return 0
    except Exception as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
