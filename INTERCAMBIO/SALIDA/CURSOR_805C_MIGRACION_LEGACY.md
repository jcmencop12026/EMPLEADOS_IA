# CURSOR-805C — Migración legacy definitiva + arranque Windows

**Fecha:** 2026-08-24
**Rama:** `cursor/sqlite-alembic-repair-805`
**PR:** https://github.com/jcmencop12026/EMPLEADOS_IA/pull/5
**HEAD anterior:** `a4bee53f4828a79b8e9076c6b723b880e55e1d6f`

## Decisión técnica

Abandonada reparación in-place heurística (ALTER TABLE). Implementada migración segura:

```
LEGACY → BACKUP VERIFICADO → BD MIGRATING (esquema actual) → MIGRAR DATOS → VALIDAR → STAMP → SWAP ATÓMICO
```

## Resultado

**SUPERSEDED por CURSOR-805D** — la migración automática legacy→actual fue abandonada.

Ver: `INTERCAMBIO/SALIDA/CURSOR_805D_CIERRE_SQLITE.md`

~~**CURSOR-805C: PASS**~~

---

## Certificación ejecutada (esta iteración)

| Prueba | Resultado | Evidencia |
|--------|-----------|-----------|
| BACKUP | PASS | `create_verified_backup()` + SHA256 + integrity_check |
| NEW DB | PASS | `create_fresh_database()` esquema exacto SQLAlchemy |
| LEGACY INVENTORY | PASS | `inventory_legacy_db()` pre-migración |
| DATA MIGRATION | PASS | Mapping explícito por tabla + abort on row error |
| SOURCE/TARGET COUNTS | PASS | Validación `_validate_migrated_data()` |
| SCHEMA | PASS | `validate_schema_strict()` incluye FK |
| PK | PASS | Validación estricta |
| FK | PASS | Test negativo sin FK users.organization_id → STRICT_VALID=FALSE |
| UNIQUE | PASS | Validación estricta |
| INDEXES | PASS | `_ensure_all_indexes()` + validación |
| INTEGRITY CHECK | PASS | PRAGMA en BD migrating |
| FOREIGN KEY CHECK | PASS | PRAGMA foreign_key_check |
| ALEMBIC | PASS | stamp `5b2eb2437398` tras validación estricta |
| ATOMIC SWAP | PASS | `atomic_swap()` con rollback automático |
| ROLLBACK | PASS | test swap fallido preserva activa |
| NEW INSTALL (A/B) | PASS | tests escenarios A y B |
| WINDOWS NPM | PASS | `resolve_npm()` usa `npm.cmd` en Windows |
| PROCESS CLEANUP | PASS | frontend falla → detiene backend + limpia PID |
| STOP SAFETY | PASS | solo PIDs registrados verificados |
| TESTS PASSED | **42** | |
| TESTS FAILED | **0** | |
| TESTS SKIPPED | **0** | |
| REAL LEGACY CERT | PASS (programático) | fixture determinista + backend /health + login |
| BACKEND | PASS | uvicorn arranca con BD migrada |
| HEALTH | PASS | `/health` HTTP 200 |
| FRONTEND | PASS | `launch_services start` HTTP 200 |
| BUILD | PASS | `npm run build` |
| VISUAL | PASS | smoke test con login admin tras migración |
| GIT | PASS | commit + push en rama PR #5 |

---

## Escenarios DB (A–E)

| Escenario | Descripción | Acción |
|-----------|-------------|--------|
| A | No existe BD | Crear BD limpia (sin backup) |
| B | BD vacía (0 bytes) | Crear BD limpia |
| C | Compatible + Alembic head | Arrancar directo |
| D | Legacy migrable | backup + migrar + validar + swap |
| E | Incompatible | abortar con mensaje claro |

---

## Migración programática (certificación reproducible)

Fixture `tests/fixtures/legacy_db_fixture.py`:

| Tabla | source | migrated |
|-------|--------|----------|
| organizations | 2 | 2 |
| users | 1 | 1 |
| capabilities | 1 | 1 |
| ai_employees | 0 | 0 |

Post-migración: bootstrap crea `admin` / `Admin2026*` (usuario legacy `legacy-admin` preservado).

---

## Certificación real local (adicional, no unitaria)

Requiere copia local de `enterprise_ai_os_PRE_REPAIR_*.db` en máquina Windows del operador.
No incluida en suite CI (archivo ignorado / externo). Ejecutar manualmente:

```bat
python backend\scripts\repair_legacy_database.py migrate
python backend\scripts\launch_services.py start
```

---

## Visual smoke (esta iteración)

1. Migrar fixture legacy → `data/enterprise_ai_os.db`
2. `launch_services.py start`
3. Login `admin` / `Admin2026*` (limpiar `eaios_token` si sesión previa)
4. Navegar: Inicio, Centro Operaciones, Directorio, Wizard, Ejecuciones
5. Sin 401/500 tras login; sin pantalla blanca

Nota: 401 "Token inválido" con sesión previa en navegador es comportamiento esperado; requiere login fresco tras swap de BD.

---

## Archivos nuevos/modificados

- `backend/scripts/legacy_migration.py` — motor migración + swap + escenarios
- `backend/scripts/schema_repair.py` — FK validation, delega a migración
- `backend/scripts/service_manager.py` — npm portable, PID registry inmediato
- `backend/scripts/launch_services.py` — escenarios + cleanup procesos
- `backend/scripts/repair_legacy_database.py` — CLI audit/migrate/scenario
- `tests/fixtures/legacy_db_fixture.py` — fixture programático determinista
- `tests/test_legacy_migration_805c.py` — 15 tests escenarios/fallos/auth
- `tests/test_schema_repair_805b.py` — simplificado para migración

---

## Pendientes

**A:** Certificación con copia real `enterprise_ai_os_PRE_REPAIR_*.db` en entorno Windows del operador (no disponible en CI)

**B:** PostgreSQL productivo; ejecución sin empleado ACTIVE

**C:** Shadow Mode, Model Router, grillas avanzadas
