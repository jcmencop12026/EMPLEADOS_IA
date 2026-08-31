#!/usr/bin/env bash
# C1-R1 — regresión funcional focal (sin repetir G01-G14 completo)
set -euo pipefail
cd /workspace
export PYTHONPATH=backend

echo "=== C1-R1 NAVEGACION ==="
python3 -m pytest tests/test_c1_r1_home_route.py -q --tb=short

echo "=== LOGIN HOTFIX C1 ==="
python3 -m pytest tests/test_v1_hotfix_login.py -q --tb=short

echo "=== CONVERGENCIA C1 ==="
python3 -m pytest tests/test_convergencia_c1.py -q --tb=short

echo "=== RBAC V1 ==="
python3 -m pytest tests/test_security_rbac_v1.py -q --tb=short

echo "=== MULTITENANT / SUPERADMIN ==="
python3 -m pytest tests/test_multitenant_v1.py::test_superadmin_can_list_and_create_company \
  tests/test_multitenant_v1.py::test_tenant_admin_cannot_create_company \
  tests/test_multitenant_v1.py::test_cross_tenant_knowledge_denied \
  tests/test_multitenant_v1.py::test_inactive_company_blocks_login \
  -q --tb=short

echo "=== CC FOCAL ==="
python3 -m pytest tests/test_convergencia_final_fase2.py -q --tb=short

echo "=== NX01 NX02 NX03 NX05 ==="
python3 -m pytest \
  tests/test_convergencia_gate_nx01_e2e_session.py \
  tests/test_convergencia_gate_nx02_cross_tenant_simultaneous.py \
  tests/test_convergencia_gate_nx03_rbac_fase2_matrix.py \
  tests/test_convergencia_gate_nx05_knowledge_auth.py \
  -q --tb=short

echo "=== FRONTEND BUILD ==="
cd frontend && npm run build
