# CURSOR-805D — Cierre definitivo SQLite local / Windows

**Fecha:** 2026-08-24
**Rama:** `cursor/sqlite-alembic-repair-805`
**PR:** https://github.com/jcmencop12026/EMPLEADOS_IA/pull/5
**HEAD anterior:** `d6c9332`

## Decisión de arquitectura

**MIGRACIÓN LEGACY AUTOMÁTICA: NO SE REALIZA**

La BD legacy se preserva íntegramente. Se inventaria/exporta. Se crea una BD nueva con el esquema actual del MVP.

## Resultado

**CURSOR-805D: PASS**

---

## Política DB (A–D)

| Escenario | Acción |
|-----------|--------|
| A — no existe / vacía | crear BD actual + Alembic + seed |
| B — compatible actual | arrancar sin recrear |
| C — legacy detectada | preservar + inventario + export + BD nueva |
| D — dañada/incompatible | abortar (no reemplazar silenciosamente) |

---

## Certificación ejecutada

| Campo | Resultado |
|-------|-----------|
| LEGACY PRESERVED | PASS — copia verificada en `data/LEGACY/` |
| LEGACY SHA256 | PASS — verificado en preservación |
| INVENTORY | PASS — `LEGACY_INVENTORY.json` + `.csv` |
| EXPORT | PASS — `data/LEGACY/EXPORT/*.json` + `.csv` |
| NEW DB | PASS — esquema SQLAlchemy actual |
| SCHEMA | PASS — `validate_schema_strict()` |
| ALEMBIC HEAD | PASS — `5b2eb2437398` |
| SEED | PASS — bootstrap `admin` / `Admin2026*` |
| BACKEND / HEALTH | PASS — HTTP 200 |
| LOGIN | PASS — tras BD nueva |
| WINDOWS NPM | PASS — `resolve_npm()` |
| PROCESS TREE | PASS — `taskkill /T` + child PIDs |
| STOP SAFETY | PASS — solo árbol propio |
| TESTS PASSED | **42** |
| TESTS FAILED | **0** |
| TESTS SKIPPED | **0** |
| BUILD | PASS |
| VISUAL | PASS — smoke con login tras legacy→nueva |

---

## Archivos clave

- `backend/scripts/legacy_preservation.py` — preservar, inventario, export
- `backend/scripts/db_startup.py` — escenarios A–D, BD nueva, seed
- `backend/scripts/service_manager.py` — árbol de procesos Windows
- `backend/scripts/launch_services.py` — orquestador BAT
- `tests/test_db_startup_805d.py` — 15 tests política 805D

---

## Rollback manual

1. Detener con `DETENER_EMPLEADOS_IA.bat`
2. La BD legacy permanece en `data/LEGACY/enterprise_ai_os_LEGACY_<timestamp>.db`
3. Para restaurar manualmente: copiar el archivo legacy deseado a `data/enterprise_ai_os.db` (bajo su responsabilidad)

---

## Pendientes

**A:** Certificación con BD legacy real en Windows del operador (`D:\EMPLEADOS_IA`)

**B:** PostgreSQL productivo

**C:** Shadow Mode, Model Router, grillas avanzadas
