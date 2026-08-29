# CURSOR 1350A — Reauditoría final de migraciones y base heredada

## Identificación

| Campo | Valor |
|-------|-------|
| Rama focal | `cursor/1350a-recert-migrations` |
| Rama 1350 feature | `cursor/1350-gobierno-datos-privacidad` |
| Base declarada | `cursor/1250a-fix-aislamiento-tests` @ `6352836813da85e31514e19cef125bcff53b4191` |
| HEAD 1350 (pre-recert) | `3216b7d826e4de7626a0cd59b9401b5722e11fee` |
| HEAD recert (final) | (ver commit en rama focal) |
| Alembic head | `1350a1b2c3d4e` |

## Resumen ejecutivo

El fallo `test_migration_roundtrip_upgrade_downgrade_upgrade` es **HEREDADO** de la cadena post-V1 convergida en 1250a. **1350 no lo introduce ni lo agrava**; solo extiende el head con `1350a1b2c3d4e` después del merge `1250a1b2c3d4e`.

**Causa raíz:** migraciones `1120` y `1110` incompatibles con SQLite batch mode (FK sin nombre / `create_foreign_key` fuera de `batch_alter_table`). En BD limpia SQLite, `upgrade head` falla antes de alcanzar 1250a o 1350.

**Corrección aplicada** (rama `cursor/1350a-recert-migrations`, alineada con fix ya probado en `cursor/1250b-fix-migration-roundtrip-85e4` para 1120, más fix equivalente para 1110 requerido por la línea 1250a):

- `1120a1b2c3d4e`: FK `fk_proactive_signals_source_id` nombrada vía `batch_op.create_foreign_key`
- `1110a1b2c3d4e`: FK `fk_finops_records_opportunity_id` vía `batch_alter_table`

Revision IDs **sin cambio**; solo contenido reversible de migraciones protegidas (mismo patrón documentado en commit `ef1717b` de 1250b).

## FASE 1 — Base 1250a (sin 1350)

| Atributo | Valor |
|----------|-------|
| SHA base | `6352836813da85e31514e19cef125bcff53b4191` |
| Motor | SQLite |
| Test | `test_migration_roundtrip_upgrade_downgrade_upgrade` |
| Resultado | **FAIL** |
| Error | `ValueError: Constraint must have a name` |
| Migración | `1120a1b2c3d4e` upgrade, `proactive_signals.source_id` |
| Evidencia | `INTERCAMBIO/SALIDA/evidencia_1350a/base_1250a_roundtrip_traceback.txt` |

## FASE 2 — Rama 1350 (antes de corrección)

| Comparación | Base 1250a | 1350 @ 3216b7d |
|-------------|------------|----------------|
| Primer error | Constraint must have a name (1120) | Idéntico |
| Tras fix solo 1120 | — | NotImplementedError SQLite en 1110 |
| Clasificación | HEREDADO | HEREDADO (+ segundo defecto 1110 expuesto) |

1350 **no modifica** archivos `1110` ni `1120` en su feature commit `a17cb6c`.

## FASE 3 — Diagnóstico técnico

| Verificación | Estado |
|--------------|--------|
| Un solo head | `1350a1b2c3d4e` ✓ |
| down_revision 1350 | `1250a1b2c3d4e` ✓ |
| merge 1250a | `1200`, `1210`, `1220` → `1250a1b2c3d4e` ✓ |
| Ledger | `baseline_head` y `protected_revisions` incluyen 1350 ✓ |
| Dependencias rotas | No |
| Downgrade incompleto 1350 | No (tablas gov_* reversibles) |

**Defectos heredados (no atribuibles a 1350):**

1. **1120** — `ForeignKey` inline en `batch_op.add_column` → SQLite exige nombre en `add_constraint`
2. **1110** — `op.create_foreign_key` directo → SQLite no soporta ALTER de constraints sin batch

## FASE 4 — Corrección

Rama: `cursor/1350a-recert-migrations` (derivada de `cursor/1350-gobierno-datos-privacidad`)

No se creó revisión Alembic nueva: el fallo ocurre **antes** de aplicar 1350 en BD limpia; corrección en migraciones `1110`/`1120` con mismo revision ID (requerido para instalaciones desde cero).

Compatibilidad: `1250a` → `1350` intacta; head final `1350a1b2c3d4e`.

## FASE 5 — Roundtrip SQLite

```
BD limpia → upgrade head → downgrade a840c4d5e6f7 → upgrade head
```

| Paso | Resultado |
|------|-----------|
| pytest roundtrip | **PASS** |
| `alembic heads` | `1350a1b2c3d4e` (único) |
| Índice `uq_roles_global_code` | Presente tras roundtrip |
| Orphans role_permissions | 0 |

## FASE 6 — PostgreSQL

Motor: PostgreSQL 16 (Docker `postgres:16-alpine`, puerto 55433)

| Paso | Resultado |
|------|-----------|
| upgrade head | `1350a1b2c3d4e` |
| downgrade a840 | OK (múltiples heads parciales esperados en merge) |
| re-upgrade head | `1350a1b2c3d4e` |
| FK constraints | 242 |
| Índices | 264 |
| Tablas gov_* | 17 |

**PostgreSQL roundtrip: PASS**

## FASE 7 — Regresión tests

| Suite | Resultado |
|-------|-----------|
| `tests/test_governance_1350.py` | 28 passed |
| `tests/test_admin_840b_v3.py::test_migration_roundtrip_*` | 1 passed |
| `pytest tests/` | **714 passed, 0 failed, 2 skipped** |

Skipped (justificados, preexistentes): certificación/condicionales en suite, no relacionados con 1350.

## FASE 8 — Regresión funcional 1350

Sin cambios de comportamiento en gobierno de datos (solo migraciones 1110/1120). Áreas 1350 revalidadas vía suite completa + `test_governance_1350.py`: **PASS**.

## FASE 9 — Frontend

| Check | Resultado |
|-------|-----------|
| `npm run build` | PASS |
| `npm audit --audit-level=high` | 0 vulnerabilities |
| `/gobernanza-datos` | UI español (sin rediseño) |

## FASE 10 — Git / CI

| Check | Resultado |
|-------|-----------|
| `git diff --check` | PASS |
| Backend/PostgreSQL | PASS (roundtrip + suite) |
| Frontend | PASS |
| Validación Git | PASS |
| Windows CI | No ejecutado en VM Linux cloud (pendiente pipeline Windows del repo) |

CI efectivo en este entorno: **3/4** (Windows no disponible localmente).

## Veredicto

**1350 GOBIERNO DE DATOS — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

Condiciones cumplidas en entorno de certificación:

- 0 tests fallidos
- Roundtrip SQLite PASS
- Roundtrip PostgreSQL PASS
- Gobierno de datos funcional sin regresión

Pendiente real: ejecución CI Windows en pipeline del repositorio y merge explícito (instrucción: **NO MERGE** automático).

## Referencias

- Fix 1120 equivalente: `origin/cursor/1250b-fix-migration-roundtrip-85e4` @ `ef1717b`
- Evidencia: `INTERCAMBIO/SALIDA/evidencia_1350a/`
- PR 1350 feature: #51
- PR recert migraciones: (draft en rama focal)

## NO MERGE

Ramas listas para revisión humana e integración controlada.
