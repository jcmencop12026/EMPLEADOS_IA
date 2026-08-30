# CURSOR 1110 — FinOps y trazabilidad económica

**Fecha:** 2026-08-29  
**Rama:** `cursor/1110-finops-trazabilidad-economica`  
**Base:** `4c03cbe`  
**HEAD:** _(ver sección final tras push)_  
**Estado:** **BLOQUE 1110 TERMINADO**  
**NO MERGE**

---

## Objetivo

Implementar **B1.2** (trazabilidad costo ↔ oportunidad) y **B1.3** (FinOps operativo) extendiendo el módulo FinOps existente (950) sin reconstruirlo.

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

Campos preservados en trazabilidad: `organization_id`, `employee_id`, `provider`, `model_name`, tokens, ejecución/proceso, oportunidad, fecha, costo.

### 2. Presupuestos operativos

| Campo / función | Descripción |
|-----------------|-------------|
| `alert_threshold_pct` | Umbral configurable (50–100 %, default 90) |
| `serialize_budget_detail()` | `spent`, `balance`, `state`, `blocks_execution` |
| API budgets | CRUD con detalle operativo en español |

### 3. Alertas

| Componente | Descripción |
|------------|-------------|
| `finops_budget_alert_states` | Dedupe por presupuesto / período / estado |
| `process_budget_alerts()` | Emite `FINOPS_LIMIT_REACHED` + auditoría `finops.budget.alert` |
| Post-consumo | Alertas automáticas tras `registrar_consumo()` |

### 4. Límites (enforcement)

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

### 6. Arquitectura futura

Sin pricing ni planes comerciales. Modelo abierto a IA administrada o credenciales propias de la institución (campos `provider` / tarifas por organización).

### 7. Seguridad

RBAC: `finops.view`, `finops.manage`, `finops.budget`, `finops.rates`. Aislamiento por `organization_id`. Sin exposición de credenciales de proveedores.

### 8. Migración

`backend/alembic/versions/1110a1b2c3d4e_finops_traceability_1110.py`

---

## Validación

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_finops_1110.py` | 8/8 PASS |
| `pytest tests/test_finops_950.py` | 15/15 PASS (regresión) |
| `pytest tests/test_finops_950_adversarial.py` | 11/11 PASS (regresión) |
| `npm run build` (frontend) | PASS |

---

## Tests focales 1110

- Registro costo con `opportunity_id`
- Resolución oportunidad desde `work_plan_id`
- Economía por oportunidad (costo + valor)
- Dedupe alertas presupuesto
- Bloqueo solo con política «Bloquear»
- Aislamiento multi-tenant
- RBAC API (economics / presupuestos)
- API presupuestos con umbral y saldo

---

## Restricciones respetadas

- NO PostgreSQL harness
- NO scheduler R2
- NO OpenAI real
- NO Docker
- NO pricing / ROI final / línea base
- NO Ollama
- NO tocar `cursor/v1-integracion-final` ni PR #32

---

## Veredicto

```
EMPLEADOS_IA — BLOQUE 1110 TERMINADO

RAMA: cursor/1110-finops-trazabilidad-economica
BASE: 4c03cbe
HEAD: <SHA tras commit>

COSTO↔OPORTUNIDAD: PASS
PRESUPUESTOS: PASS
ALERTAS: PASS
LÍMITES: PASS
UI FINOPS: PASS
RBAC: PASS
MULTIEMPRESA: PASS
TESTS: 34 passed (1110 + 950 + adversarial)
FRONTEND: PASS

VEREDICTO: APTO
NO MERGE
```
