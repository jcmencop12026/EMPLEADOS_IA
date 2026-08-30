# EMPLEADOS_IA — CORRECCIÓN P1 MIGRATION ROUNDTRIP 1250B

**Rama:** `cursor/1250b-fix-migration-roundtrip-85e4`  
**Base:** `af26097ee48d34255b2ffa6ba79ba977c2d7b1a24`  
**Fecha:** 2026-08-29

---

## Causa raíz confirmada

| Campo | Valor |
|-------|-------|
| **Error** | `ValueError: Constraint must have a name` |
| **Migración** | `1120a1b2c3d4e` |
| **Tabla** | `proactive_signals` |
| **Columna** | `source_id` |
| **FK** | `proactive_signals.source_id → signal_sources.id` |
| **Operación** | `upgrade` (primera aplicación desde BD vacía) |
| **Mecanismo** | `op.batch_alter_table()` + `add_column` con `ForeignKey` inline sin nombre |
| **Motor** | SQLite (Alembic `SQLiteImpl`, modo batch) |

Alembic en modo batch para SQLite exige restricciones con nombre explícito. La columna `source_id` se añadía con `sa.ForeignKey("signal_sources.id")` sin `name`, lo que impide el roundtrip `upgrade → downgrade → upgrade`.

---

## Corrección aplicada

**Tipo:** Opción A — corregir operación de constraint en migración histórica `1120a1b2c3d4e`  
**Revision IDs modificados:** NO (solo contenido de la migración existente)

Cambios en `backend/alembic/versions/1120a1b2c3d4e_senales_reales_deteccion.py`:

1. Constante `FK_PROACTIVE_SIGNALS_SOURCE = "fk_proactive_signals_source_id"`
2. **Upgrade:** añadir columna `source_id` sin FK inline; crear FK con `batch_op.create_foreign_key(...)` nombrada
3. **Downgrade:** `batch_op.drop_constraint(FK_PROACTIVE_SIGNALS_SOURCE, type_="foreignkey")` antes de `drop_column("source_id")`

No se creó migración nueva. Head Alembic se mantiene en `1250b1c2d3e4f`.

---

## Pruebas ejecutadas

| Prueba | Resultado |
|--------|-----------|
| `test_migration_roundtrip_upgrade_downgrade_upgrade` | **PASS** (×2) |
| `test_migration_control.py` (7 tests) | **PASS** |
| Upgrade desde cero → head | **PASS** |
| Downgrade → `a840c4d5e6f7` | **PASS** |
| Re-upgrade → head | **PASS** |
| 1120 focal (11) | **PASS** |
| 1220 focal (15) | **PASS** |
| 1240 focal (14) | **PASS** |
| 1250B convergencia (11) | **PASS** |
| Suite SQLite completa | **655 passed, 0 failed, 2 skipped** |
| `npm run build` | **PASS** |

---

## Salida final

```
EMPLEADOS_IA — CORRECCIÓN P1 1250B TERMINADA

BASE:
af26097ee48d34255b2ffa6ba79ba977c2d7b1a24

RAMA:
cursor/1250b-fix-migration-roundtrip-85e4

HEAD:
<SHA post-commit>

CAUSA RAÍZ:
FK sin nombre en batch_alter_table de 1120a1b2c3d4e (proactive_signals.source_id)

MIGRACIÓN AFECTADA:
1120a1b2c3d4e

TIPO DE CORRECCIÓN:
create_foreign_key / drop_constraint con nombre explícito fk_proactive_signals_source_id

REVISION IDS MODIFICADOS:
NO

ALEMBIC: PASS
HEAD ALEMBIC: 1250b1c2d3e4f
UPGRADE DESDE CERO: PASS
DOWNGRADE: PASS
RE-UPGRADE: PASS
ROUNDTRIP: PASS
1120: PASS
1220: PASS
1240: PASS
1250B: PASS
TESTS FOCALES: 51/51 PASS
TESTS CONVERGENCIA: 11/11 PASS
SUITE GENERAL: 655 passed / 0 failed / 2 skipped / 0 errors
FRONTEND: PASS
P0: 0
P1: 0
P2: 0
VEREDICTO: APTO LIMPIO
NO MERGE.
```

EMPLEADOS IA. Corrección de migración 1250B terminada.
