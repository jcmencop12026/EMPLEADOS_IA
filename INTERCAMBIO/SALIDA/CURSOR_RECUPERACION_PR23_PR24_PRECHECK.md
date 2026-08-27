# CURSOR — Recuperación PR23 + PR24 — Precheck

**Fecha:** 2026-08-27
**Git root:** `/workspace` (equivalente `D:\EMPLEADOS_IA`)

## HEADs confirmados

| Referencia | SHA | Notas |
|------------|-----|-------|
| `origin/main` | `cc77d83` | PR #22 (ORQUESTADOR-1010) integrado |
| `origin/cursor/e2e-integral-1020-12b6` | `c3c8754` | PR #23 — 1 commit sobre main |
| `origin/cursor/oportunidades-proactivas-1030` | `922c8e1` | PR #24 — 1 commit sobre main |

## Ancestro común

- `1020` ∩ `main` = `cc77d83`
- `1030` ∩ `main` = `cc77d83`
- `1030` **NO contiene** commits de `1020` (`c3c8754`)

## Commits exclusivos

### En 1020, no en main
```
c3c8754 E2E-INTEGRAL-1020: certificación funcional integral y puente experiencia
```

### En 1030, no en main
```
922c8e1 feat(1030): inteligencia proactiva y centro de oportunidades
```

## CI GitHub al inicio

### PR #23
| Check | Estado |
|-------|--------|
| Frontend | PASS |
| Windows | PASS |
| Backend/PostgreSQL | **FAIL** |
| Validación Git | **FAIL** |

### PR #24
| Check | Estado |
|-------|--------|
| Backend/PostgreSQL | PASS |
| Frontend | PASS |
| Windows | PASS |
| Validación Git | **FAIL** |

## Diagnóstico preliminar FAIL

### PR #23 — Validación Git
Trailing whitespace en:
- `INTERCAMBIO/SALIDA/CURSOR_E2E_INTEGRAL_1020.md`
- `INTERCAMBIO/SALIDA/E2E_1020_MAPA_INTEGRACION_REAL.md`

### PR #23 — Backend/PostgreSQL
```
FAILED test_adversarial_race_zero_late_effects_100_iterations
AssertionError: Efectos tardíos detectados: 3/100
```
Causa raíz: `invalidate_run_execution` invalidaba fence en memoria **después** del lock BD; el worker podía despertar antes de la invalidación.

### PR #24 — Validación Git
Trailing whitespace en:
- `INTERCAMBIO/SALIDA/OPORTUNIDADES_1030_MAPA_CAPACIDADES.md`

## Paquete certificación externa

`INTERCAMBIO/ENTRADA/OPORTUNIDADES_PROACTIVAS_1030_CERTIFICACION.zip` — **NO DISPONIBLE**

## Orden de integración requerido

```
1010 (main @ cc77d83)
  ↓
1020 (PR #23) — corregir primero
  ↓
1030 (PR #24) — integrar sobre 1020 corregido
```

## Acción siguiente

1. Corregir PR #23 (git check + race fence)
2. Certificar PR #23 → APTO PARA MERGE
3. Crear `cursor/preintegracion-1020-1030` desde PR #23 corregido
4. Incorporar PR #24 semánticamente
5. Re-certificar integración
