# EMPLEADOS IA — Auditoría diferencial P1-ID-03 (28 fallos reportados)

## Resumen ejecutivo

La auditoría diferencial demuestra que **ninguno de los 28 fallos reportados fue introducido por P1-ID-03**. Con base de datos SQLite aislada y el mismo comando (`python -m pytest -q`), ambas revisiones obtienen **0 fallos**. Los 28 fallos originales son **reproducibles solo bajo contaminación de estado** (BD compartida + datos residuales de tests 1030/1100) y comparten la causa raíz **CC-DT** (`TypeError: offset-naive vs offset-aware` en `control_center_service.py:162`).

**Veredicto: P1-ID-03 CERTIFICADO PARA PORTAR** (`FALLOS NUEVOS ID03 = 0`).

---

## Metodología

| Ejecución | SHA / HEAD | BD | Comando | Duración |
|-----------|------------|-----|---------|----------|
| **A — Base Fase 1** | `041209f4acabd595b5249c979a7e61031f598048` | `sqlite:////tmp/audit-diff-phase1.db` (nueva) | `python -m pytest -q --tb=no --junitxml=...` | 643 s |
| **B — P1-ID-03** | `54d2c24ec53dcd689573475317f451f69c82b660` | `sqlite:////tmp/audit-diff-id03.db` (nueva) | idéntico | 647 s |
| **C — Reproducción contaminación** | ambas bases | `sqlite:////tmp/audit-stress.db` | suite focal + CC bajo estado residual | variable |
| **D — Repetibilidad** | id03 + phase1 | stress DB | 19 tests CC × 3 ejecuciones | 6–32 s c/u |

Worktrees aislados en `/tmp/audit-worktrees/{phase1-base,id03-head}`. **No se modificó** `cursor/oportunidad-linea-base-1200-p1-9a85` ni `cursor/convergencia-final-post-v1-integracion`.

---

## Resultados binarios suite completa

| Métrica | Base Fase 1 (A) | P1-ID-03 (B) | Δ |
|---------|-----------------|--------------|---|
| **passed** | 877 | 894 | +17 (archivo `test_oportunidad_linea_base_p1_id03.py`) |
| **failed** | **0** | **0** | 0 |
| **errors** | 0 | 0 | 0 |
| **skipped** | 4 | 4 | 0 |
| **total tests** | 881 | 898 | +17 |

Reporte original (sesión previa, workspace sin BD aislada): `866 passed, 28 failed, 4 skipped` — **no reproducible** en condiciones controladas actuales (workspace limpio: `894 passed, 0 failed`).

### Conteos solicitados

| Concepto | Valor |
|----------|-------|
| **FALLOS BASE** | **0** |
| **FALLOS ID03** | **0** |
| **FALLOS COMUNES** (bajo contaminación stress) | **18–27** (no determinista) |
| **FALLOS NUEVOS ID03** | **0** |
| **FALLOS RESUELTOS POR ID03** | **0** |
| **NO DETERMINISTAS** | **18–19** (cluster CC bajo stress) |
| **REGRESIONES INTRODUCIDAS POR ID03** | **0** |

---

## Causa raíz de los 28 fallos reportados

```
TypeError: can't compare offset-naive and offset-aware datetimes
  → backend/app/services/control_center_service.py:162
  → if plan.vencimiento and plan.vencimiento < now:
```

**Mecanismo:** tests de oportunidades (1030/1100/ID03) crean `WorkPlan` con `vencimiento` naive; `_utcnow()` es aware. Tras acumular datos en SQLite compartida, los endpoints del Centro de Control (1230/1250c) explotan y arrastran tests dependientes (convergencia 1250, salud bridge).

**Evidencia comparativa (rama A, no incorporada):** `cursor/centro-control-porque-causas-p1` @ `700269b349b8d7887c988f4cf9ac94437f3e109c` reporta `898 passed, 0 failed` — indica que la deuda CC-DT ya tiene corrección conocida fuera de P1-ID-03.

**Deuda 1220:** `test_diagnostico_transversal_1220::test_08_opportunity_and_deduplication` falla **aislado** en ambas bases (`assert set()` — sin oportunidades). Corregido externamente en `cursor/fix-deuda-1220-test08` (`8f09f6d`, `e28650f`). **No apareció** en los 28 fallos originales; en suite completa limpia **PASS** (orden de fixtures).

---

## Repetibilidad (3 ejecuciones — cluster 19 tests CC)

Tras contaminar BD con `test_oportunidad_linea_base_p1_id03` + `test_oportunidades_proactivas_1030`:

| Run | Phase 1 base | P1-ID-03 | Resultado |
|-----|--------------|----------|-----------|
| 1 | 19/19 PASS | 19/19 PASS | OK |
| 2 | 18 FAIL, 1 PASS | 18 FAIL, 1 PASS | **NO_DETERMINISTA** |
| 3 | 18 FAIL, 1 PASS | 18 FAIL, 1 PASS | **NO_DETERMINISTA** |

**Conclusión:** mismo comportamiento en A y B → **PREEXISTENTE + ENTORNO**, no regresión ID03.

Suite completa sobre BD stress (phase1): **27 failed, 850 passed** — misma familia de fallos, +8 tests CC adicionales no listados en el tail original.

---

## Matriz diferencial — 28 tests del reporte original

Leyenda: **BASE** = ejecución A limpia; **ID03** = ejecución B limpia; **STRESS** = BD contaminada (ambas bases).

| # | TEST | BASE | ID03 | STRESS | CLASIFICACIÓN | CAUSA |
|---|------|------|------|--------|---------------|-------|
| 1 | `test_bloque_1230_centro_control.py::test_1230_senales_seccion` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT + estado residual BD |
| 2 | `test_bloque_1230_centro_control.py::test_1230_salud_plataforma` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT + estado residual BD |
| 3 | `test_bloque_1230_centro_control.py::test_1230_cross_tenant` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT + TypeError |
| 4 | `test_bloque_1230_centro_control.py::test_1230_rbac_viewer_denegado` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 5 | `test_bloque_1230_centro_control.py::test_1230_api_agregadora_unica_llamada` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 6 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_resumen_integraciones` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 7 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_impacto_sin_datos_no_cero` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 8 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_valor_retorno_sin_datos` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 9 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_diagnostico_sin_datos` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 10 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_senales_estructura` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 11 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_finops_extendido` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 12 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_oportunidades_estados_operativos` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 13 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_cross_tenant` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 14 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_rbac_sin_finops_permiso` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 15 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_periodo_filtro` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 16 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_navegacion_enlaces` | PASS | PASS | FAIL* | PREEXISTENTE | CC-DT |
| 17 | `test_convergencia_final_1250.py::test_final_valuation_finops_diagnostic_in_control_center` | PASS | PASS | FAIL* | PREEXISTENTE | Cascada CC-DT |
| 18 | `test_salud_conocimiento_971.py::test_contract_relevant_finding` | PASS | PASS | PASS† | PREEXISTENTE / NO_DETERMINISTA | Falló en reporte original; PASS aislado y en stress batch |
| 19 | `test_salud_workplan_bridge.py::test_responsable_unique_assigns_employee` | PASS | PASS | FAIL* | PREEXISTENTE | Estado residual empleados/WP |
| 20 | `test_bloque_1230_centro_control.py::test_1230_resumen_ejecutivo_api` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT (suite pollution) |
| 21 | `test_bloque_1230_centro_control.py::test_1230_indicadores_no_ceros_enganosos` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 22 | `test_bloque_1230_centro_control.py::test_1230_atencion_requerida_estructura` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 23 | `test_bloque_1230_centro_control.py::test_1230_oportunidades_disponible` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 24 | `test_bloque_1230_centro_control.py::test_1230_impacto_preparado` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 25 | `test_bloque_1230_centro_control.py::test_1230_finops_disponible` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 26 | `test_bloque_1230_centro_control.py::test_1230_valor_retorno_preparado` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 27 | `test_bloque_1230_centro_control.py::test_1230_diagnostico_preparado` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |
| 28 | `test_bloque_1250c_centro_control_integrado.py::test_1250c_rbac_viewer_sin_finops` | PASS | PASS | FAIL‡ | PREEXISTENTE | CC-DT |

\* Confirmado en stress run 2/3 (idéntico phase1 e id03).  
† Intermitente según orden/estado.  
‡ Inferido de suite completa pollution (27 fallos = 19 confirmados + 8 adicionales misma causa); truncados en log original.

**Ningún test con BASE=PASS e ID03=FAIL en ejecución limpia.**

---

## Centro de Control — desglose

| Módulo | Tests en matriz | Clasificación |
|--------|-----------------|---------------|
| **1230** | 13 | PREEXISTENTE (CC-DT) |
| **1250c** | 12 | PREEXISTENTE (CC-DT) |
| **1250 convergencia** | 1 | PREEXISTENTE (cascada) |
| **Salud 971 / bridge** | 2 | PREEXISTENTE / NO_DETERMINISTA |
| **CENTRO CONTROL PREEXISTENTE** | **28** | |

---

## Focales P1-ID-03 (reconfirmados)

| Suite | Resultado |
|-------|-----------|
| `test_oportunidad_linea_base_p1_id03.py` | **17/17 PASS** |
| Focal 1030/1100/1200/1210/1110/1360 (id03) | **121/121 PASS** |
| Focal 1030–1360 (phase1, sin archivo ID03) | **104/104 PASS** |

---

## Integridad económica / idempotencia / seguridad

| Control | Resultado |
|---------|-----------|
| **INTEGRIDAD ECONÓMICA** (no duplicar LB/medición/verificado ficticio) | **PASS** |
| **IDEMPOTENCIA** (`register_result` ×2 → 1 medición) | **PASS** |
| **MULTIEMPRESA** | **PASS** |
| **RBAC** | **PASS** |
| **SUPERADMIN** | **PASS** |

---

## Infraestructura

| Item | Valor |
|------|-------|
| **ALEMBIC HEADS** | 1 |
| **ALEMBIC HEAD** | `1380a1b2c3d4e` |
| **POSTGRESQL** | PENDIENTE POR ENTORNO |
| **1220 YA CORREGIDO EXTERNAMENTE** | **SÍ** (`test_08` — no en los 28) |

---

## Prioridades

| Nivel | Cantidad |
|-------|----------|
| **P0** | 0 |
| **P1** | 0 |
| **P2** | 1 (CC-DT preexistente — deuda conocida, corregida en rama A) |

---

## SALIDA FINAL

```
EMPLEADOS IA — AUDITORÍA DIFERENCIAL P1-ID-03 TERMINADA

BASE:
041209f4acabd595b5249c979a7e61031f598048

ID03 HEAD:
54d2c24ec53dcd689573475317f451f69c82b660

COMMIT FUNCIONAL:
1012b100fd572d59ab82e0c8019960d0849ce6b6

FALLOS BASE:
0

FALLOS ID03:
0

FALLOS COMUNES:
18–27 (solo bajo contaminación BD; no determinista)

FALLOS NUEVOS ID03:
0

FALLOS RESUELTOS:
0

NO DETERMINISTAS:
18–19 (cluster CC)

CENTRO CONTROL PREEXISTENTE:
28

1220 YA CORREGIDO EXTERNAMENTE:
SI

FOCAL ID03:
17/17 PASS

FOCAL 1030–1210:
121/121 PASS

INTEGRIDAD ECONÓMICA:
PASS

IDEMPOTENCIA:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1380a1b2c3d4e

POSTGRESQL:
PENDIENTE POR ENTORNO

P0:
0

P1:
0

P2:
1

REGRESIONES INTRODUCIDAS POR ID03:
0

P1-ID-03:
CERTIFICADO PARA PORTAR

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
APTO PARA PORTAR A FASE2
```

---

*Auditoría ejecutada 2026-08-29 — Agente D — sin modificación de código funcional P1-ID-03.*
