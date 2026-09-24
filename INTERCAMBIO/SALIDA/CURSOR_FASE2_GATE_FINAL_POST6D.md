# EMPLEADOS IA — GATE FINAL POST-6D

**Rama:** `cursor/gate-final-post6d-85e4`
**Base obligatoria:** `cursor/fase2-central-integracion`
**HEAD inicial verificado:** `7ce2f343e35ebc75850570af7a1fa071f089bb7a`
**Fecha:** 2026-08-30

---

## 1. BASE

| Verificación | Resultado |
|---|---|
| `git rev-parse HEAD` (inicio) | `7ce2f343e35ebc75850570af7a1fa071f089bb7a` ✓ |
| Alembic heads | 1 |
| Alembic head | `1341a1b2c3d4e` ✓ |
| Migración nueva | NO (CAS en código, sin constraint adicional) |

---

## 2. P1-C-01 — CONCURRENCIA AUDITOR/FÁBRICA

### Causa raíz

Carrera TOCTOU en `ejecutar_operacion_fabrica`: dos hilos con distinta `idempotency_key` (`conc-a`, `conc-b`) leían la traza en `PENDING`, pasaban validaciones y ejecutaban `solicitar_aprobacion` antes de consolidar `IN_PROGRESS`. La ventana **leer → decidir → ejecutar → commit** no tenía protección atómica por obligación causal.

### Solución

1. **`_atomic_claim_trace_execution()`** — compare-and-set transaccional:
   ```sql
   UPDATE employee_improvement_traces
   SET status='IN_PROGRESS', executed_by_id=?, updated_at=?
   WHERE id=? AND organization_id=? AND status IN ('PENDING','FAILED')
   ```
   Solo `rowcount == 1` ejecuta la operación efectiva.

2. **Claim anticipado** — el CAS se ejecuta **antes** de registrar decisión humana y antes de `request_approval`, cerrando la ventana TOCTOU.

3. **`_response_for_unclaimed_trace()`** — respuesta controlada para el perdedor: conflicto (`400`), idempotente si ya `COMPLETED`, nunca segunda ejecución efectiva.

4. **Respaldo en `solicitar_aprobacion`** — si `trace.approval_id` ya existe o `request_approval` devuelve aprobación existente, tratar como idempotente.

### Mecanismo de atomicidad

- **PostgreSQL (referencia productiva):** `UPDATE … WHERE status IN (…)` con commit inmediato; serialización por bloqueo de fila en la transición condicionada.
- **SQLite (tests):** misma semántica SQL; no define la semántica productiva.

### Pruebas de concurrencia

| Escenario | Resultado |
|---|---|
| A. Test aislado | PASS |
| B. 5 repeticiones consecutivas | PASS (5/5) |
| C. Tras `test_auditor_factory_cycle.py` | PASS (5/5) |
| D. Orden inverso (gate → cycle) | PASS |
| E. Claves idempotencia iguales | PASS |
| F. Claves idempotencia distintas | PASS |
| G. Misma obligación | ≤1 aprobación PENDING en BD |
| H. Obligaciones distintas | 2 ejecuciones independientes OK |
| I. Usuario no autorizado (viewer) | 403/400 |

Verificación en BD: conteo `EmployeeFactoryApproval` PENDING ≤ 1 por empleado/traza.

---

## 3. P1-B — MB-11 AISLAMIENTO

### Causa

Tests con códigos/nombres fijos (`SLA_RIESGO`, `MANUAL`, `Correo simulado`, `Bandeja`, `Roto`) violaban constraints `uq_comm_template_org_codigo` y `uq_comm_channels_org_nombre` en BD session-scoped al reejecutar la suite.

### Corrección

- Códigos de plantilla y nombres de canal/regla con sufijo UUID.
- Helper `_bootstrap_admin()` usando `settings.bootstrap_admin_username` (no literal `"admin"`).

---

## 4. P1-B — ADMIN HARDCODEADO

- Reemplazado `User.username == "admin"` por `settings.bootstrap_admin_username` en `test_mb11_comunicaciones.py`.
- Regla de producto intacta: SUPERADMIN sigue siendo `admin` en operación normal.

---

## 5. P1-B — ADMIN_840B

`test_duplicate_global_role_denies`:

| Intento | Resultado |
|---|---|
| Aislado ×3 | PASS |
| Tras suite focal | PASS |
| Tras regresión completa | PASS |

**Veredicto:** NO REPRODUCIDO como defecto P1 en HEAD actual. El test pasa de forma consistente; el hallazgo B quedó INDETERMINADO en SHA anterior y no se confirma aquí.

---

## 6. P1-D — COMUNICACIONES ESPAÑOL

- `frontend/src/pages/ComunicacionesPage.tsx` línea 283: `Correlation:` → `ID de correlación:`
- Revisión completa de `ComunicacionesPage.tsx`: sin otras instancias visibles de `Correlation:`.

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---|---|
| `backend/app/services/auditor_factory_bridge.py` | CAS concurrencia, claim anticipado, respuesta controlada |
| `tests/test_gate_post6d_correcciones.py` | Batería concurrencia A–I + verificación BD |
| `tests/test_mb11_comunicaciones.py` | Aislamiento UUID + bootstrap admin configurable |
| `frontend/src/pages/ComunicacionesPage.tsx` | Etiqueta español detalle comunicación |

---

## 8. MIGRACIONES / ALEMBIC

```
Alembic heads: 1
Alembic head: 1341a1b2c3d4e
validate_migrations: PASS
```

Sin migración nueva (solución CAS no requiere garantía persistente adicional).

---

## 9. REGRESIÓN

### Entorno limpio (`unset DATABASE_URL`, SQLite temporal)

```
1202 passed
0 failed
0 errors
4 skipped
```

### Suite focal (171 tests)

Auditor, Auditor→MiTrabajo, ciclo Auditor/Fábrica, gate post6d, MB-11, Mi Trabajo, Mesa, 1290, 820, 810C, RBAC, multiempresa, admin 840b — **PASS**.

### Frontend

```
npm run build → PASS
```

### Recorrido visual

- `/comunicaciones` → mensaje → detalle: `ID de correlación:` ✓ (código)
- Traducciones previas en `/trabajo`, `/soporte`, `/optimizacion`, `/empleados/auditoria` — sin regresión en build.

### PostgreSQL

**PENDIENTE POR ENTORNO** — implementación diseñada para PostgreSQL; certificación real de concurrencia en PG no ejecutada en este entorno.

---

## 10. P0 / P1 / P2 FINALES

| Nivel | Count | Notas |
|---|---|---|
| P0 | 0 | |
| P1 | 0 | C-01, B MB-11, B admin, D cerrados |
| P2 | Documentados | Cosmética (densidad Fábrica, tooltips, JSON, 1024px) — fuera de alcance gate |

---

## 11. PRESERVACIÓN G1–G4

| Gate | Estado |
|---|---|
| G1 Gobierno Auditor→Fábrica | ✓ |
| G2 Mi Trabajo sin duplicación | ✓ |
| G3 Dedup 1290 | ✓ |
| G4 AUTOMÁTICA ≠ autoaprobada | ✓ |
| auto_execution_blocked | ✓ |
| RBAC / SUPERADMIN / SECRETOS | ✓ |

---

## 12. SALIDA FINAL

```
EMPLEADOS IA — GATE FINAL POST-6D

BASE: cursor/fase2-central-integracion @ 7ce2f34
HEAD: cursor/gate-final-post6d-85e4 (post-correcciones)

CONCURRENCIA CAUSA: TOCTOU sin CAS en transición PENDING→IN_PROGRESS
CONCURRENCIA SOLUCIÓN: _atomic_claim_trace_execution + claim anticipado
ATOMICIDAD: UPDATE condicionado WHERE status IN ('PENDING','FAILED')
MISMA OBLIGACIÓN + DOS HILOS: máx. 1 transición efectiva
CLAVES DIFERENTES: protegido por obligación causal, no por idempotency_key
DOBLE EJECUCIÓN: NO
DOBLE APROBACIÓN: NO (verificado en BD)

MB11 AISLAMIENTO: códigos/nombres UUID en tests
ADMIN HARDCODEADO: settings.bootstrap_admin_username
ADMIN_840B: NO REPRODUCIDO — test pasa consistentemente

COMUNICACIONES ESPAÑOL: ID de correlación:

G1-G4 PRESERVADOS: SÍ
MI TRABAJO: PASS
MB07: PASS (consumption_planner_mb07 en suite completa)
MB11: PASS
MESA: PASS
1290: PASS
820: PASS
810C: PASS
FINOPS: PASS (suite completa)
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: preservado
SECRETOS: preservado

ALEMBIC HEADS: 1
ALEMBIC HEAD: 1341a1b2c3d4e

PRUEBAS CONCURRENCIA: PASS (A–I)
PRUEBAS FOCALES: 171 passed
REGRESIÓN COMPLETA: 1202 passed
FAILED: 0
ERRORS: 0
SKIPPED: 4

FRONTEND: PASS
RECORRIDO VISUAL: código verificado
POSTGRESQL: PENDIENTE POR ENTORNO

P0: 0
P1: 0
P2: documentados (no bloquean gate)

PLATAFORMA EJECUTABLE: SÍ

MAIN: NO
V1: NO
6E: NO

VEREDICTO: GATE CERRADO
```
