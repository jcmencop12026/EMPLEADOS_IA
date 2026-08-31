#!/usr/bin/env bash
# Certificación BP1 — ejecución focal Agente C
set -euo pipefail
cd /workspace
export PYTHONPATH=backend

echo "=== BP1 BLOQUE PRODUCTO 1 ==="
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py -q --tb=short

echo "=== CERTIFICACION RECORRIDO BP1 ==="
python3 -m pytest tests/test_certificacion_bp1_recorrido.py -q --tb=short

echo "=== REGRESION UX (C2/C1-R1/login/trabajo) ==="
python3 -m pytest \
  tests/test_convergencia_c2.py \
  tests/test_c1_r1_home_route.py \
  tests/test_v1_hotfix_login.py \
  tests/test_bandeja_trabajo_humano.py::test_trabajo_items_api \
  tests/test_bandeja_trabajo_humano.py::test_trabajo_deduplicacion_aprobacion_notificacion \
  -q --tb=short

echo "=== FRONTEND BUILD ==="
cd frontend && npm run build
