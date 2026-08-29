#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for EMPLEADOS_IA (FastAPI backend + Vite/React frontend).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Python venv requires ensurepip (python3.x-venv). Install it if the base image lacks it.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  echo "[install] python venv module missing; installing python3-venv..."
  sudo apt-get update -qq
  PY_MINOR="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  sudo apt-get install -y -qq "python${PY_MINOR}-venv"
fi

# Backend virtualenv + dependencies.
if [ ! -x ".venv/bin/python" ]; then
  echo "[install] creating .venv..."
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/pip install -q -r backend/requirements.txt

# Runtime data directory for the SQLite database.
mkdir -p data

# Frontend dependencies (reproducible install from the committed lockfile).
cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "[install] done."
