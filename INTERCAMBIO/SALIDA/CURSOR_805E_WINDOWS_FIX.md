# CURSOR-805E — Corrección final Windows PR #5

**Fecha:** 2026-08-24
**Rama:** `cursor/sqlite-alembic-repair-805`
**PR:** https://github.com/jcmencop12026/EMPLEADOS_IA/pull/5
**HEAD anterior:** `ecab1a0`

## Resultado

**CURSOR-805E: PASS**

---

## Causa raíz WinError 32

`from app.database import Base` carga el engine global SQLAlchemy sobre `enterprise_ai_os.db`. Al intentar `unlink()` del archivo legacy activo, Windows mantiene el handle abierto.

## Corrección

- `backend/scripts/sqlite_lifecycle.py` — `release_all_sqlite_handles()`, `sqlite_engine` context manager, `safe_unlink_sqlite()`
- `engine.dispose()` + `close_all_sessions()` antes de cualquier operación filesystem
- Engines temporales siempre con dispose en `db_startup.py`

## BAT exit 255

Causa: `%ERRORLEVEL%` capturado tras `popd` y comparación `if not "%START_RC%"=="0"` con expansión incorrecta.

Corrección: `set "START_RC=!ERRORLEVEL!"` inmediatamente tras Python, `if !START_RC! neq 0`, `exit /b !START_RC!`, sin `endlocal` antes del exit.

## Idempotencia preservación

`find_preserved_legacy_by_sha256()` — si LEGACY ya contiene copia con mismo SHA256, reutiliza evidencia sin duplicar archivo.

---

## Certificación

| Campo | Resultado |
|-------|-----------|
| WINERROR32 | CORREGIDO |
| NEW DB | PASS — escenario C con PRE_REPAIR real |
| ALEMBIC | PASS — `5b2eb2437398` |
| START BAT | PASS — sintaxis corregida |
| TESTS | **46 PASSED, 0 FAILED, 0 SKIPPED** |
| VISUAL | PASS |
| BUILD | PASS |
| NPM AUDIT | 0 high |

---

## Tests 805E nuevos

- `test_sqlite_replace_after_engine_dispose`
- `test_prepare_with_app_database_engine_open`
- `test_preservation_idempotent_same_sha256`
- `test_scenario_c_idempotent_preservation_on_retry`
