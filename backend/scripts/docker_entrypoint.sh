#!/usr/bin/env bash
set -euo pipefail

cd /app/backend
export PYTHONPATH=/app/backend

echo "[entrypoint] Esperando PostgreSQL..."
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

from app.db_url import resolve_database_url_from_environ

url = resolve_database_url_from_environ() or ""
if url:
    os.environ["DATABASE_URL"] = url
if not url.startswith("postgresql"):
    print("[entrypoint] DATABASE_URL no es PostgreSQL; omitiendo espera.")
    sys.exit(0)

deadline = time.time() + 60
last_error = None
while time.time() < deadline:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print("[entrypoint] PostgreSQL disponible.")
        sys.exit(0)
    except Exception as exc:
        last_error = exc
        time.sleep(2)

print(f"[entrypoint] Timeout esperando PostgreSQL: {last_error}", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Validando gobierno de migraciones..."
python scripts/validate_migrations.py

echo "[entrypoint] Ejecutando alembic upgrade head..."
alembic upgrade head

echo "[entrypoint] Arrancando aplicación..."
exec "$@"
