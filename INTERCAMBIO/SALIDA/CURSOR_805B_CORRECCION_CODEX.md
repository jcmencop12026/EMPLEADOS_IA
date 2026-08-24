# CURSOR-805B — Corrección bloqueantes auditoría Codex (PR #5)

**Fecha:** 2026-08-24
**Rama:** cursor/sqlite-alembic-repair-805
**PR:** https://github.com/jcmencop12026/EMPLEADOS_IA/pull/5
**HEAD anterior:** 139cc7c60809337268269d1f2463718b0d6ea4c0

## Resumen

Corrección de los bloqueantes A1–A8 identificados por auditoría independiente Codex sobre PR #5.

**Resultado:** CURSOR-805B: PASS

---

## A1 — Validación estricta antes de stamp

| Estado | Evidencia |
|--------|-----------|
| **PASS** | `validate_schema_strict()` verifica tablas, columnas, tipos, PK, nullable, UNIQUE, índices, columnas extra bloqueantes |
| **PROBADO** | `test_incompatible_schema_rejected_for_stamp` — PK compuesta incompatible → stamp rechazado |
| **PROBADO** | `sync_alembic_revision()` verifica esquema válido antes de stamp y confirma revisión escrita |

## A2 — Backend sobre BD legacy real

| Estado | Evidencia |
|--------|-----------|
| **PASS** | Copia legacy simulada (sin `requires_approval`, con `capabilities.status` NOT NULL) |
| **PROBADO** | `test_legacy_codex_db_repair_and_backend_health` — repair + uvicorn + `/health` HTTP 200 |
| **Corrección** | Elimina columnas legacy `status`; backfill seguro; tipos DATETIME/TEXT compatibles |

## A3 — Backup automático

| Estado | Evidencia |
|--------|-----------|
| **PASS** | `create_verified_backup()` antes de cada repair |
| **PROBADO** | `test_backup_creation_and_verification` — tamaño > 0, sqlite abre, PRAGMA integrity_check, SHA256 |
| **Comportamiento** | Si backup falla → `SchemaRepairError` → repair abortado |

## A4 — DETENER sin matar procesos ajenos

| Estado | Evidencia |
|--------|-----------|
| **PASS** | Solo termina PIDs registrados en `data/empleados_ia.pids` |
| **PROBADO** | `test_foreign_process_not_killed` — PID ajeno no pertenece → skipped, no killed |
| **Corrección** | Eliminado `taskkill` por puerto; verificación por cmdline + cwd del proyecto |

## A5 — INICIAR secuencia obligatoria

| Estado | Evidencia |
|--------|-----------|
| **PASS** | `launch_services.py prepare` → audit → backup → repair → audit → alembic |
| **PASS** | `launch_services.py start` → backend → `/health` 200 → frontend → verificación |
| **PROBADO** | Arranque sobre copia `enterprise_ai_os_805b_test.db` reparada |
| **Corrección** | No declara éxito antes de `/health`; credencial demo eliminada del BAT |

## A6 — Tests portables

| Estado | Evidencia |
|--------|-----------|
| **PASS** | 32/32 tests (25 MVP + 7 repair 805B) |
| **Corrección** | `test_alembic_chain_present` usa ruta relativa al proyecto |

## A7 — Control visual real

| Estado | Evidencia |
|--------|-----------|
| **PASS** | Smoke test sobre BD legacy reparada |
| **PROBADO** | Inicio, Centro Operaciones, Directorio, Detalle, Wizard, Ejecuciones — sin 500 ni pantallas blancas |

## A8 — Informe honesto

| Estado | Evidencia |
|--------|-----------|
| **PASS** | Este documento distingue PROBADO vs PASS por inferencia |

---

## Certificación ejecutada

| Prueba | Resultado |
|--------|-----------|
| Backup | PASS |
| Esquema incompatible rechazado | PASS |
| Idempotencia | PASS |
| Preservación datos | PASS |
| Reparación BD legacy (copia) | PASS |
| Backend /health 200 | PASS |
| Suite >= 25/25 | 32/32 PASS |
| npm build | PASS |
| Proceso ajeno no terminado | PASS |
| INICIAR (launch_services start) | PASS |
| DETENER (launch_services stop) | PASS |
| Visual autenticado | PASS |
| git diff --check | PASS |

---

## B — Pendientes

| Item | Clasificación | Nota |
|------|---------------|------|
| PostgreSQL productivo | B | Sin cambio |
| nanoid HIGH (transitiva) | **Resuelto** | `npm audit fix` → 0 vulnerabilidades |

## C — Pendientes

- Código inalcanzable en `_default_sql` corregido
- Shadow Mode, Model Router, grillas avanzadas — sin cambio

---

## Cambios técnicos clave

1. `schema_repair.py` — validación estricta, backup verificado, fix Alembic stamp con `DATABASE_URL`
2. `alembic/env.py` — respeta `DATABASE_URL` del entorno
3. `service_manager.py` + `launch_services.py` — PID registry con verificación cwd/cmdline
4. BAT actualizados para delegar en scripts Python
5. `tests/test_schema_repair_805b.py` — 7 tests nuevos

---

## RESULTADO FINAL

**CURSOR-805B: PASS**
