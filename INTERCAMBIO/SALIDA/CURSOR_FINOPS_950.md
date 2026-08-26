# CURSOR FINOPS-950 — Costos y valor

**Fecha:** 2026-08-25
**Rama:** `cursor/finops-value-950-12b6`
**HEAD:** `f3c5c9f`
**Main base:** `1697dd2`
**Estado:** **FINOPS-950 LISTO PARA REAUDITORÍA**
**NO MERGE**

---

## Alcance implementado

### Backend

| Componente | Descripción |
|------------|-------------|
| `finops_models.py` | `FinOpsRate`, `FinOpsValueRecord`, `FinOpsBudget` |
| `orchestration_models.FinOpsRecord` | Extendido: employee, categoría, moneda, cantidad, tarifa |
| `finops_service.py` | `registrar_consumo()`, `registrar_valor()`, ROI, dashboard, drill-down |
| `routers/finops.py` | API `/api/finops/*` |
| `permissions.py` | `finops.view`, `finops.manage`, `finops.budget`, `finops.rates` |
| Migración | `c950a1b2c3d4_finops_value_950.py` |

### Categorías soportadas

Modelo IA, OCR, API externa, Integración, Almacenamiento, Procesamiento, Ejecución, Otro

### Tarifas

Parametrización por proveedor/modelo/categoría/unidad con `Numeric` (sin precios hardcodeados).

### Valor y ROI

Tipos de valor (Ahorro de tiempo, Reducción de costo, etc.) con certeza Real/Estimado/No disponible.
ROI reproducible con manejo de costo cero, desconocido y monedas.

### Presupuestos

Por empresa/empleado/proceso con estados Normal → Límite alcanzado y políticas (sin bloqueo automático).

### Frontend

- Ruta `/costos-valor` — dashboard compacto
- Nav "Costos y valor" en `AppShell`

---

## Validación local

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_finops_950.py` | 14/14 PASS |
| Migración upgrade → downgrade → upgrade | PASS (SQLite) |
| `npm run build` | PASS |
| `npm audit --audit-level=moderate` | 0 vulnerabilities |
| `git diff --check origin/main...HEAD` | PASS |

---

## Tests incluidos

Registro consumo, tarifa vigente/inexistente, Decimal, costo/costo cero, valor real/estimado, ROI, presupuesto, proyección, tenant, permisos, PATCH parcial, trazabilidad.

---

## Multi-tenant

Filtrado por `organization_id` en todas las consultas. Test `test_tenant_isolation` PASS.

---

## Integración futura

Contratos `registrar_consumo()` y `registrar_valor()` listos para Orquestador, Scheduler, Operaciones e Integraciones.

---

## CI

Push realizado — pendiente run GitHub Actions en rama `cursor/finops-value-950-12b6`.
