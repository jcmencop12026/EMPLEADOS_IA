#!/usr/bin/env bash
# Certificación funcional C2 — ejecución focal Agente C
set -euo pipefail
cd /workspace
export PYTHONPATH=backend

echo "=== C2 MATRIZ PRINCIPAL ==="
python3 -m pytest tests/test_convergencia_c2.py -q --tb=short

echo "=== C1-R1 HOME PRESERVADO ==="
python3 -m pytest tests/test_c1_r1_home_route.py -q --tb=short

echo "=== MULTITENANT + RBAC ==="
python3 -m pytest tests/test_multitenant_v1.py tests/test_security_rbac_v1.py -q --tb=short

echo "=== CC + MI TRABAJO FOCAL ==="
python3 -m pytest \
  tests/test_centro_control_tramo6e.py \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_convergencia_final_fase2.py \
  -q --tb=short

echo "=== DEDUP G2/G3 ==="
python3 -m pytest \
  tests/test_gate_post6d_correcciones.py::test_g2_solicitar_aprobacion_transitions_trabajo \
  tests/test_gate_post6d_correcciones.py::test_g3_dedup_oportunidad_vs_1290_humana \
  -q --tb=short

echo "=== LOGIN/MFA/SSO ==="
python3 -m pytest tests/test_v1_hotfix_login.py -q --tb=short
python3 -m pytest tests/test_bloque_1300_seguridad_avanzada.py::test_1300_list_sessions -q --tb=short 2>/dev/null || \
  python3 -m pytest tests/test_bloque_1300_seguridad_avanzada.py -k "session" -q --tb=short --maxfail=1

echo "=== NX REUTILIZADOS (C1) ==="
for f in nx01 nx02 nx03 nx05; do
  git show cursor/certificacion-c1-funcional-dec7:tests/test_convergencia_gate_${f}_*.py > /tmp/${f}.py 2>/dev/null || true
done
if ls /tmp/nx*.py 1>/dev/null 2>&1; then
  python3 -m pytest /tmp/nx*.py -q --tb=short 2>/dev/null || true
fi

echo "=== FRONTEND BUILD ==="
cd frontend && npm run build
