# CURSOR — E2E-INTEGRAL-1020

**Fecha:** 2026-08-27  
**Rama:** `cursor/e2e-integral-1020-12b6`  
**Base:** `main` @ `cc77d83` (PR #22 integrado)  
**Veredicto:** **E2E-INTEGRAL-1020 — APTO PARA REAUDITORÍA**  
**NO MERGE**

---

## A. Arquitectura real encontrada

Flujo principal certificado vía SALUD:

`solicitud natural → run_ips_analysis → select_specialists(1010) → motor analítico → diagnóstico → plan-accion → WorkPlan → Operaciones → resultado → experiencia core`

Componentes reutilizados (sin duplicar): Shell, permisos, Orquestador 1010, Conocimiento, MOTOR-1000, WorkPlan bridge, Operaciones-940, Scheduler, Notificaciones, FINOPS-950.

Ver mapa detallado: `INTERCAMBIO/SALIDA/E2E_1020_MAPA_INTEGRACION_REAL.md`

## B. Gaps encontrados

| ID | Descripción | Estado |
|----|-------------|--------|
| G-01 | Coordinator no llama SALUD integral | Documentado |
| G-02 | FINOPS sin work_plan_id en valores motor | Documentado |
| G-03 | Experiencia IPS no alimentaba core | **Corregido** |
| G-04 | Conocimiento sensible a keywords solicitud | Documentado |
| G-05 | E2E GUI no ejecutable en Cloud Agent | Pendiente local |

## C. Correcciones realizadas

1. **`sync_action_result_to_core_experience`** en `salud_experience.py` — propaga `POST /api/salud/propuestas/{id}/resultado` a `EmployeeExperienceRecord`.
2. **Schema** `ActionResultRequest` ampliado con `kpi_antes`, `kpi_despues`, `feedback_humano`.
3. **Suite** `tests/test_e2e_integral_1020.py` (13 tests) + helpers.

## D. Flujo E2E #1 (feliz)

- Solicitud: lenguaje natural sobre recuperación de cartera y flujo de caja.
- Datasets: motor caso D sintético + contratos.
- Conocimiento: documento autorizado con grant.
- Líder dinámico con `razon_seleccion_global`.
- Motor: hipótesis, recomendación consolidada, FINOPS.
- WorkPlan + Operaciones con `analysis_id` en task payload.
- Evidencia: `INTERCAMBIO/SALIDA/e2e_1020/E2E_FLUJO_1.json`

## E. Resultado real

`POST /propuestas/{id}/resultado` con KPI antes/después (18→9 días radicación).

## F. Experiencia antes/después

- `experiencia_core_id` creado al registrar resultado.
- Peso y score de experiencia incrementan tras éxito documentado.
- Evidencia: `E2E_APRENDIZAJE.json`

## G. Flujo E2E #2 (segunda ejecución)

Segunda solicitud comparable tras aprendizaje — score experiencia ≥ anterior; explicación de selección presente.

## H. Cambio de decisión

No se exige líder distinto; se verifica coherencia con nueva evidencia (score experiencia sube).

## I. Prueba de fracaso

Feedback `CORRECTO` + outcome `FRACASO` + KPI empeora → `estado=FRACASO`, `peso < 0.75`.

## J. Tenant isolation

Cross-tenant en análisis, plan, operaciones — PASS.

## K. Permisos

Usuario `viewer` sin `salud.ejecutar_analisis` → 403 FAIL-CLOSED.

## L. Idempotencia / retry

Plan-accion idempotente; reintento no duplica WorkPlan.

## M. FINOPS

Valores registrados con `source=motor_analitico:{analysis_id}`.

## N. Trazabilidad

Cadena reconstruible: analysis_id → selection_log_id → work_plan_id → correlation_id → experiencia_core_id.

## O. GUI

**E2E GUI — PENDIENTE DE VALIDACIÓN LOCAL**

Instrucciones:
1. Login → Diagnóstico IPS
2. Cargar caso E2E, ejecutar análisis
3. Ver equipo/líder/razones
4. Crear plan de acción → Operaciones
5. Registrar resultado en propuesta

## P. Regresión

| Prueba | Resultado |
|--------|-----------|
| `test_e2e_integral_1020.py` | 13 passed |
| `pytest tests/` | 478 passed, 2 skipped |
| `npm run build` | OK |
| `npm audit --audit-level=high` | 0 vulnerabilities |
| `alembic heads` | `1010a1b2c3d4e` (único) |

## Q. CI

Pendiente ejecución CI en PR draft.

## R. Defectos pendientes

- G-01, G-02, G-04, G-05 (no bloqueantes para reauditoría backend/API).

---

## Artefactos

- `INTERCAMBIO/SALIDA/E2E_1020_MAPA_INTEGRACION_REAL.md`
- `INTERCAMBIO/SALIDA/e2e_1020/*.json`
- `tests/test_e2e_integral_1020.py`
- `tests/e2e_1020_helpers.py`
