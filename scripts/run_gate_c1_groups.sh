#!/usr/bin/env bash
# Gate C1 — ejecución por grupos G01-G14 (solo instrumentación certificación)
set -euo pipefail
cd /workspace
export PYTHONPATH=backend

run_group() {
  local id="$1"
  shift
  echo "=== $id ==="
  python3 -m pytest "$@" -q --tb=no 2>&1 | tee "/tmp/gate_${id}.log" | tail -3
  local summary
  summary=$(grep -E '^[0-9]+ passed|failed|error' "/tmp/gate_${id}.log" | tail -1 || echo "NO_SUMMARY")
  echo "RESULT|$id|$summary"
}

run_group G01 \
  tests/test_shell_830.py \
  tests/test_security_rbac_v1.py \
  tests/test_multitenant_v1.py \
  tests/test_p0_precertificacion_v1.py \
  tests/test_prerelease_v1_corrections.py

run_group G02 \
  tests/test_multitenant_v1.py \
  tests/test_security_rbac_v1.py \
  tests/test_centro_control_tramo6e.py::test_centro_control_tenant_isolation \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_mb11_comunicaciones.py \
  tests/test_mesa_ayuda_mb12.py \
  tests/test_finops_950_adversarial.py::test_drill_down_cross_tenant_work_plan_404

run_group G03 \
  tests/test_multitenant_v1.py::test_superadmin_can_list_and_create_company \
  tests/test_multitenant_v1.py::test_tenant_admin_cannot_create_company \
  tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_superadmin_org_context \
  tests/test_centro_control_porque_p1.py::test_p1_superadmin_org_context \
  tests/test_convergencia_final_fase2.py::test_convergencia_kpi_organizaciones_enlace \
  tests/test_convergencia_final_fase2.py::test_convergencia_mi_trabajo_adapter_usa_viewer

run_group G04 \
  tests/test_centro_control_tramo6e.py \
  tests/test_centro_control_cableado_ejecutivo_fase2.py \
  tests/test_bloque_1250c_centro_control_integrado.py \
  tests/test_bloque_1230_centro_control.py \
  tests/test_centro_control_1240_gaps_ui.py \
  tests/test_correccion_focal_post6e_p1.py \
  tests/test_convergencia_final_fase2.py \
  tests/test_control_center_datetime_cc_dt.py

run_group G05 \
  tests/test_bandeja_trabajo_humano.py \
  tests/test_gate_post6d_correcciones.py::test_g2_solicitar_aprobacion_transitions_trabajo \
  tests/test_gate_post6d_correcciones.py::test_g3_dedup_oportunidad_vs_1290_humana \
  tests/test_auditor_integracion_mi_trabajo.py \
  tests/test_mb11_integracion_mi_trabajo.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_convergencia_final_fase2.py::test_convergencia_mi_trabajo_adapter_usa_viewer

run_group G06 \
  tests/test_employee_auditor_mvp.py \
  tests/test_auditor_integracion_mi_trabajo.py

run_group G07 \
  tests/test_agent_factory_e2e.py \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_auditor_factory_cycle.py \
  tests/test_gate_post6d_correcciones.py::test_g1_deviation_requires_explicit_authorization \
  tests/test_gate_post6d_correcciones.py::test_concurrency_auditor_factory_no_double_execution \
  tests/test_gate_post6d_correcciones.py::test_concurrency_same_obligation_idempotency_keys \
  tests/test_gate_post6d_correcciones.py::test_concurrency_different_obligations_both_succeed \
  tests/test_gate_post6d_correcciones.py::test_concurrency_unauthorized_user_denied \
  tests/test_gate_post6d_correcciones.py::test_concurrency_repeated_adversarial

run_group G08 \
  tests/test_oportunidades_proactivas_1030.py \
  tests/test_optimizacion_1290.py \
  tests/test_gate_post6d_correcciones.py::test_g4_automatica_no_autoaprueba_oportunidad \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_operations_940.py \
  tests/test_e2e_integral_1020.py

run_group G09 \
  tests/test_finops_1110.py \
  tests/test_finops_950.py \
  tests/test_finops_950_adversarial.py \
  tests/test_consumption_planner_mb07.py \
  tests/test_bloque_1270_multiproveedor.py

run_group G10 \
  tests/test_knowledge_930.py \
  tests/test_salud_conocimiento_971.py \
  tests/test_capabilities_850.py \
  tests/test_multitenant_v1.py::test_cross_tenant_knowledge_denied

run_group G11 \
  tests/test_mb11_comunicaciones.py \
  tests/test_mb11_integracion_mi_trabajo.py

run_group G12 \
  tests/test_mesa_ayuda_mb12.py \
  tests/test_mesa_ayuda_integracion_mi_trabajo.py

run_group G13 \
  tests/test_docker_database_url.py \
  tests/test_db_startup_805d.py \
  tests/test_db_startup_805e.py \
  tests/test_migration_control.py

run_group G14 \
  tests/test_multitenant_v1.py \
  tests/test_security_rbac_v1.py \
  tests/test_integration_v1_final.py \
  tests/test_llm_gateway_v1.py \
  tests/test_p0_precertificacion_v1.py \
  tests/test_prerelease_v1_corrections.py \
  tests/test_automations_810c.py \
  tests/test_notifications_820.py \
  tests/test_agent_factory_e2e.py \
  tests/test_integraciones_1330.py \
  tests/test_optimizacion_1290.py \
  tests/test_bloque_1100_oportunidades_operativo.py

echo "=== FRONTEND BUILD ==="
cd frontend && npm run build 2>&1 | tee /tmp/gate_frontend.log | tail -5
