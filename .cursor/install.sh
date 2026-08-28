#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for EMPLEADOS_IA (backend + frontend).
set -euo pipefail

cd "$(dirname "$0")/.."

# Backend: Python 3.12 virtualenv + pinned requirements.
# The default image ships Python 3.12 but not the venv stdlib module; install it
# only when missing so repeated runs stay fast and idempotent.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y --no-install-recommends python3.12-venv
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r backend/requirements.txt

# Frontend: reproducible install from the committed lockfile.
cd frontend
npm ci
