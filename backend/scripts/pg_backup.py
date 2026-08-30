#!/usr/bin/env python3
"""Backup operativo PostgreSQL para EMPLEADOS_IA V1."""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings  # noqa: E402

logger = logging.getLogger("empleados_ia.backup")


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
            "Backup V1 solo soporta PostgreSQL. "
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


def _require_pg_dump() -> str:
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise RuntimeError(
            "pg_dump no encontrado en PATH. Instale el cliente PostgreSQL "
            "(postgresql-client / postgresql16-client)."
        )
    return pg_dump


def run_backup(
    *,
    database_url: str,
    output_dir: Path,
    target_env: str,
    label: str | None = None,
    verbose: bool = False,
) -> Path:
    _configure_logging(verbose)
    pg_dump = _require_pg_dump()
    params = _parse_pg_url(database_url)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    filename = f"empleados_ia_{target_env}_{timestamp}{suffix}.sql"
    output_path = output_dir / filename

    env = os.environ.copy()
    if params["password"]:
        env["PGPASSWORD"] = params["password"]

    command = [
        pg_dump,
        "--host",
        params["host"],
        "--port",
        params["port"],
        "--username",
        params["user"],
        "--dbname",
        params["dbname"],
        "--format",
        "plain",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(output_path),
    ]

    logger.info(
        "Iniciando backup env=%s destino=%s host=%s db=%s",
        target_env,
        output_path,
        params["host"],
        params["dbname"],
    )

    try:
        subprocess.run(command, check=True, env=env, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        logger.error("Backup falló (exit=%s): %s", exc.returncode, exc.stderr.strip())
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        raise RuntimeError("Backup PostgreSQL falló") from exc

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Backup generado vacío o ausente")

    logger.info("Backup completado: %s (%s bytes)", output_path, output_path.stat().st_size)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup PostgreSQL EMPLEADOS_IA V1")
    parser.add_argument(
        "--env",
        choices=["test", "prod", "other"],
        required=True,
        help="Ambiente destino del backup (metadato y guardas)",
    )
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", settings.database_url))
    parser.add_argument("--output-dir", default=settings.backup_dir)
    parser.add_argument("--label", default=None, help="Etiqueta opcional en el nombre del archivo")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    try:
        path = run_backup(
            database_url=args.database_url,
            output_dir=Path(args.output_dir),
            target_env=args.env,
            label=args.label,
            verbose=args.verbose,
        )
        print(path)
        return 0
    except Exception as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
