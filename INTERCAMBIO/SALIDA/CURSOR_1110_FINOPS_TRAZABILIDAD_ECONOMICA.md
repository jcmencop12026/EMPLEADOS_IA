# CURSOR 1110 — FinOps y trazabilidad económica

**Fecha:** 2026-08-29  
**Rama:** `cursor/1110-finops-trazabilidad-economica`  
**Base:** `4c03cbe`  
**HEAD:** `5f8918e`  
**Estado:** **BLOQUE 1110 TERMINADO**  
**NO MERGE**

---

## Recuperación de sesión anterior

| Aspecto | Resultado |
|---------|-----------|
| Trabajo previo | **RECUPERADO** |
| Rama remota | `origin/cursor/1110-finops-trazabilidad-economica` — checkout local OK |
| Cambios sin commit | Ninguno (working tree limpio) |
| Commits exclusivos 1110 | 4 (`bc7e53c` … `5f8918e`) |
| Entregable parcial | Existía; actualizado con verificación de esta sesión |

**Commits recuperados (sobre base `4c03cbe`):**

1. `bc7e53c` — feat(finops): trazabilidad costo-oportunidad y FinOps operativo (bloque 1110)
2. `4a81336` — docs: actualizar HEAD en entregable bloque 1110
3. `2057e1e` — docs: HEAD final entregable 1110
4. `5f8918e` — docs: sincronizar HEAD entregable 1110

**Acción de esta sesión:** verificación de regresión (34 tests PASS), build frontend PASS, sincronización del entregable. Sin rediseño ni reset.

---

## Objetivo

Implementar **B1.2** (trazabilidad costo ↔ oportunidad) y **B1.3** (FinOps operativo) extendiendo el módulo FinOps existente (950) sin reconstruirlo.

---

## Arquitectura aplicada

Extensión del stack FinOps 950 existente:

```
coordinator.py ──► registrar_consumo(opportunity_id | work_plan_id)
                         │
                         ▼
                  finops_records (+ opportunity_id FK nullable)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
  summarize_opportunity  query_consumptions  dashboard_summary
  _economics()           (filtros API)       (período/empresa)
         │
         ▼
  GET /api/finops/opportunities/{id}/economics

finops_budgets (+ alert_threshold_pct)
         │
         ▼
  process_budget_alerts() ──► finops_budget_alert_states (dedupe)
         │                    notifications.emit_event(FINOPS_LIMIT_REACHED)
         ▼
  assert_budget_allows_consumption() ──► FinOpsBudgetBlockedError (403)
```

Campos de trazabilidad preservados/ampliados: `organization_id`, `employee_id`, `provider`, `model_name`, tokens entrada/salida, `work_plan_id`, `task_id`, `opportunity_id`, `execution_ref`, fecha, costo, moneda, `rate_id`/`rate_source`.

Arquitectura abierta a modalidades futuras (IA administrada vs credenciales propias) vía `provider` y tarifas por organización — sin pricing comercial ni ROI final.

---

## Alcance implementado

### 1. Oportunidad ↔ costo

| Componente | Descripción |
|------------|-------------|
| `finops_records.opportunity_id` | FK nullable a `opportunities` — no rompe histórico |
| `registrar_consumo()` | Acepta `opportunity_id`; resuelve desde `work_plan_id` vía oportunidad vinculada |
| `registrar_valor()` | Valida `opportunity_id` en tenant |
| `summarize_opportunity_economics()` | Costo, valor FinOps, consumos por oportunidad |
| `GET /api/finops/opportunities/{id}/economics` | API de economía por oportunidad |
| `coordinator.py` | Propaga `opportunity_id` en registros de ejecución |

### 2. Presupuestos operativos

| Campo / función | Descripción |
|-----------------|-------------|
| `alert_threshold_pct` | Umbral configurable por presupuesto (default 90 %) |
| `serialize_budget_detail()` | `spent`, `balance`, `state`, `blocks_execution` |
| API budgets | CRUD con detalle operativo en español |

### 3. Alertas

| Componente | Descripción |
|------------|-------------|
| `finops_budget_alert_states` | Dedupe por presupuesto / período / estado |
| `process_budget_alerts()` | Emite `FINOPS_LIMIT_REACHED` + auditoría `finops.budget.alert` |
| Post-consumo | Alertas automáticas tras `registrar_consumo()` |

Estados de presupuesto: Normal, Atención (≥75 %), Cerca del límite (≥ umbral configurable), Límite alcanzado (100 %).

### 4. Alerta vs bloqueo

| Política | Comportamiento |
|----------|----------------|
| Solo informar / Requiere aprobación | Alerta, **no bloquea** |
| Bloquear | `FinOpsBudgetBlockedError` → HTTP 403 con mensaje explícito |
| `assert_budget_allows_consumption()` | Invocado en coordinator y API antes de consumir |

### 5. Interfaz (español)

| Pantalla | Mejoras |
|----------|---------|
| `CostosValorPage` | Pestañas: Resumen, Consumos (filtros), Presupuestos, Tarifas |
| `OportunidadDetailPage` | Pestaña FinOps con economía y tabla de consumos |
| `api.ts` | Tipos y endpoints extendidos |

Filtros consumo: empleado, trabajo, oportunidad, proveedor, modelo, categoría, período.

### 6. Seguridad y auditoría

- RBAC: `finops.view`, `finops.manage`, `finops.budget`, `finops.rates`
- Aislamiento por `organization_id` — oportunidad de otra empresa rechazada
- Auditoría: `finops.consumption.registered`, `finops.budget.created/updated`, `finops.budget.alert`, `finops.value.registered`
- Sin exposición de credenciales de proveedores

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/alembic/versions/1110a1b2c3d4e_finops_traceability_1110.py` | Migración Alembic |
| `backend/app/finops_models.py` | `alert_threshold_pct`, `FinOpsBudgetAlertState` |
| `backend/app/orchestration_models.py` | `opportunity_id` en `FinOpsRecord` |
| `backend/app/services/finops_service.py` | Trazabilidad, presupuestos, alertas, bloqueo |
| `backend/app/services/coordinator.py` | Propagación `opportunity_id` |
| `backend/app/routers/finops.py` | Endpoints economics, filtros, budgets |
| `backend/app/schemas_finops.py` | Schemas ampliados |
| `frontend/src/api.ts` | Tipos y endpoints FinOps |
| `frontend/src/pages/CostosValorPage.tsx` | UI administrativa FinOps |
| `frontend/src/pages/OportunidadDetailPage.tsx` | Pestaña economía oportunidad |
| `tests/test_finops_1110.py` | 8 pruebas focales bloque 1110 |

---

## Migración

`backend/alembic/versions/1110a1b2c3d4e_finops_traceability_1110.py`

- `revision`: `1110a1b2c3d4e`
- `down_revision`: `d1e2f3a4b5c6`
- Cabeza única dentro de esta rama (sin tocar migraciones V1)

---

## Validación (sesión recuperación 2026-08-29)

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_finops_1110.py` | 8/8 PASS |
| `pytest tests/test_finops_950.py` | 15/15 PASS (regresión) |
| `pytest tests/test_finops_950_adversarial.py` | 11/11 PASS (regresión) |
| `npm run build` (frontend) | PASS |

**Total:** 34 passed

### Tests focales 1110

- Registro costo con `opportunity_id`
- Resolución oportunidad desde `work_plan_id`
- Economía por oportunidad (costo + valor)
- Dedupe alertas presupuesto
- Bloqueo solo con política «Bloquear»
- Aislamiento multi-tenant (oportunidad otra empresa rechazada)
- RBAC API (economics / presupuestos)
- API presupuestos con umbral y saldo

---

## Restricciones respetadas

- NO PostgreSQL harness V1
- NO scheduler R2
- NO `cursor/v1-integracion-final` ni PR #32
- NO OpenAI real / Ollama / Docker
- NO pricing comercial / ROI final / línea base
- NO bloques 1100 / 1120

---

## Riesgos

| ID | Nivel | Descripción |
|----|-------|-------------|
| R1 | P2 | Umbrales de estado (75 %/90 %) codificados en `budget_state()`; `alert_threshold_pct` solo afecta «Cerca del límite». Evolución futura: umbrales múltiples configurables por empresa. |
| R2 | P2 | Presupuestos por proveedor/modelo no implementados — arquitectura preparada vía `scope_type` pero solo empresa/empleado/proceso activos. |
| R3 | P3 | Modalidad IA administrada vs credenciales propias: diferenciación de costo asumido pendiente de facturación comercial (fuera de alcance). |

**P0:** 0  
**P1:** 0

---

## Pendientes reales (post-1110)

1. Umbrales múltiples parametrizables por empresa (50/75/90/100 % independientes).
2. Presupuestos por proveedor/modelo cuando se requiera en V1.2+.
3. Diferenciación costo asumido EMPLEADOS_IA vs pagado por cliente (modalidad B).
4. ROI / beneficio / periodo de recuperación (bloque futuro).

---

## Veredicto final

```
EMPLEADOS_IA — BLOQUE 1110 TERMINADO

RECUPERACIÓN SESIÓN ANTERIOR: RECUPERADA

RAMA: cursor/1110-finops-trazabilidad-economica
BASE: 4c03cbe
HEAD: 5f8918e

COSTO ↔ OPORTUNIDAD: PASS
TOKENS/COSTO: PASS
PRESUPUESTOS: PASS
UMBRALES: PASS
ALERTAS: PASS
MODO BLOQUEO: PASS
FINOPS UI: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS

MIGRACIÓN: 1110a1b2c3d4e

TESTS: 34 passed (1110 + 950 + adversarial)
FRONTEND: PASS

P0: 0
P1: 0

VEREDICTO: APTO
NO MERGE
```
