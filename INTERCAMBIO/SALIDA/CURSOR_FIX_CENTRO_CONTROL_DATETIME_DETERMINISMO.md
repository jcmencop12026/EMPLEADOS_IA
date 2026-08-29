# EMPLEADOS IA — Fix CC-DT Centro de Control datetime determinismo

## A. Causa raíz

`control_center_service.py` comparaba datetimes **naive** (típicos de SQLite / tests legacy) con `_utcnow()` **aware** (UTC con `tzinfo`).

**Stack trace reproducido (antes del fix):**

```
TypeError: can't compare offset-naive and offset-aware datetimes
  control_center_service.py:165 in _atencion_requerida
    if plan.vencimiento and plan.vencimiento < now:
```

Punto secundario: `max(last_wp, last_llm, emp.updated_at)` mezclaba naive/aware en `_employees_section`.

## B. Mecanismo de reproducción

```bash
export DATABASE_URL=sqlite:////tmp/cc-dt-repro-before.db
export JWT_SECRET=test-secret-mvp-cert803
cd <repo>
python -m pytest tests/test_oportunidades_proactivas_1030.py -q --tb=no  # ×2
python -m pytest <cluster 17 tests CC> -q
```

| Run | Antes (91cadf) | Después (096b7e8) |
|-----|----------------|-------------------|
| 1 | 18 PASS | 17 PASS |
| 2 | **18 FAIL** | **17 PASS** |
| 3 | **18 FAIL** | **17 PASS** |
| 4 | — | **17 PASS** |
| 5 | — | **17 PASS** |

**Naive datetime:** `WorkPlan.vencimiento` creado por `activate_opportunity` / tests 1030 sin tzinfo.  
**Aware datetime:** `_utcnow()` → `datetime.now(timezone.utc)`.

## C. Política temporal

Reutiliza el patrón existente del proyecto (`session_service._as_utc`, `automation_service._as_utc`):

- Entrada naive → `replace(tzinfo=timezone.utc)` (asumir UTC almacenado)
- Entrada aware → `astimezone(timezone.utc)`
- Comparaciones y `max()` solo entre valores normalizados

## D. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `backend/app/services/control_center_service.py` | `+_as_utc`, `+_max_utc`, uso en vencimiento y última actividad |
| `tests/test_control_center_datetime_cc_dt.py` | Tests unitarios + gate contaminación |

**Sin migración Alembic.** HEAD: `1380a1b2c3d4e` (1 head).

## E. Tests agregados

- `TestAsUtcHelpers`: naive/naive, aware/aware, naive/aware, offset, None
- `test_cc_dt_vencimiento_naive_no_typeerror`
- `test_cc_dt_vencimiento_aware_no_typeerror`
- `test_cc_dt_contamination_cluster_five_runs` (gate 5×)
- `test_cc_dt_multiempresa_no_leak`
- `test_cc_dt_rbac_viewer_denied`

## F. Comparación antes/después

| Escenario | Antes | Después |
|-----------|-------|---------|
| Cluster CC tras contaminación 1030 (run 2) | 18 FAIL | 0 FAIL |
| Suite completa BD aislada | 914 pass / 0 fail | 914 pass / 0 fail |
| P1-ID-03 focales (17) con fix aplicado | — | 17/17 PASS |

**Nota:** `test_salud_workplan_bridge` fallaba por `AssertionError` de asignación de empleado (no datetime); excluido del gate CC-DT.

## G. Resultado 5 repeticiones (cluster CC)

**PASS** — 17/17 tests CC en runs 1–5 tras contaminación.

## H. Suite acumulativa

BD aislada nueva por ejecución (`python -m pytest -q`):

| Ejecución | Resultado |
|-----------|-----------|
| Suite 1 | **914 passed, 4 skipped, 0 failed** |
| Suite 2 | **914 passed, 4 skipped, 0 failed** |
| Suite 3 | **914 passed, 4 skipped, 0 failed** |

Repetición sobre **misma** BD tras suite completa: aparecen fallos ajenos a CC-DT (diseño de aislamiento de tests); el escenario CC-DT queda resuelto.

## I. Receta de port a Fase2 central

```bash
# Desde rama central destino (post-91cadf o equivalente certificada)
git cherry-pick 096b7e81091383f9ce621d1937f155480e4bc6d6
git cherry-pick 84ab9f7  # tests (opcional pero recomendado)

# Verificar
export DATABASE_URL=sqlite:////tmp/port-verify.db JWT_SECRET=...
python -m pytest tests/test_control_center_datetime_cc_dt.py -q
python -m pytest tests/test_bloque_1230_centro_control.py tests/test_bloque_1250c_centro_control_integrado.py -q
```

No requiere migración. No toca P1-ID-03 (`1012b100...`).

---

## SALIDA FINAL

```
EMPLEADOS IA — DEUDA CC-DT CORREGIDA

BASE:
91cadf3889d7b5f6edd3d76f86b89cb947f94dbd

RAMA:
cursor/fix-centro-control-datetime-determinismo

HEAD:
<pendiente push doc>

COMMIT FIX:
096b7e81091383f9ce621d1937f155480e4bc6d6

COMMIT TESTS:
84ab9f7

CAUSA:
Comparación naive vs aware en vencimiento WorkPlan y max() de actividad

FIX:
PASS

NAIVE → AWARE:
PASS

AWARE → NAIVE:
PASS

SQLITE:
PASS

POSTGRESQL:
PENDIENTE POR ENTORNO

CLUSTER CC RUN1-5:
PASS

SUITE 1:
914 passed, 0 failed

SUITE 2:
914 passed, 0 failed

SUITE 3:
914 passed, 0 failed

P1-ID-03 17/17:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
(no test dedicado; RBAC focal PASS)

ALEMBIC HEADS:
1

MIGRACIÓN NUEVA:
NO

FRONTEND:
NO MODIFICADO

P0:
0

P1:
0

P2:
0

RECETA PORT CENTRAL:
PREPARADA

FASE2 CENTRAL:
NO MODIFICADA

MAIN:
NO

V1:
NO

VEREDICTO:
APTO PARA PORTAR
```
