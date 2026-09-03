# EIAAX — Cierre certificación CI PR #169

**Fecha:** 2026-09-03
**Rama:** `cursor/revision-integral-completa-85e4`
**PR:** [#169](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/169)
**Base:** `cursor/convergencia-comercial-v1-85e4` (`1416671`)
**HEAD final:** _pendiente push — ver sección C tras commit_
**NO merge · NO promoción Windows · NO comando al usuario**

---

## A. Causas exactas de las 3 fallas GitHub (run `33796055739` sobre `17c5d31`)

### 1. Backend — Certificación rápida (PR)

**Síntoma:** 4 tests ERROR en `test_notifications_certification.py` (tests 05, 06, 07, 11) durante setup del fixture `client`.

**Causa raíz:** `JWT_SECRET` del workflow CI (`ci-test-secret-qa-infra-001`, 28 caracteres) no cumple `MIN_JWT_SECRET_LENGTH=32` en `backend/app/security_config.py` cuando `DATABASE_URL` es PostgreSQL. El lifespan de FastAPI falla al arrancar la app de test.

**Evidencia:**
```
RuntimeError: JWT_SECRET demasiado corto: use al menos 32 caracteres en producción.
backend/app/security_config.py:36
```

**Clasificación:** configuración CI / tests — no defecto de producto.

### 2. Windows — Pruebas de arranque SQLite

**Síntoma:** 3/4 tests FAIL en `tests/test_db_startup_805e.py`; `create_fresh_database` lanza `SchemaRepairError`.

**Causa raíz:** `validate_schema_strict` en `backend/scripts/schema_repair.py` no mapeaba `LargeBinary` → `BLOB`. La columna `negocio_proposal_documents.content_bytes` es `LargeBinary` en el modelo y `BLOB` en SQLite; el validador esperaba `TEXT` por defecto.

**Evidencia:**
```
issues 1
type negocio_proposal_documents content_bytes Tipo incompatible: esperado TEXT, actual BLOB
```

**Clasificación:** bug en validador de esquema startup — no en scripts/windows.

### 3. Validación Git — espacios en blanco conflictivos

**Síntoma:** `git diff --check origin/main...HEAD` → FAILURE (391+ líneas `trailing whitespace`).

**Causa raíz:** archivos `INTERCAMBIO/SALIDA/CURSOR_*.md` y documentos de entrega con espacios finales de línea (`  `) en líneas añadidas en el diff del PR vs `main`.

**Clasificación:** whitespace real en documentación — sin cambio de lógica.

---

## B. Correcciones aplicadas

| Falla | Archivo(s) | Corrección |
|---|---|---|
| JWT CI | `.github/workflows/qa.yml` | `JWT_SECRET: ci-test-secret-qa-infra-001-min-32-chars` (≥32) |
| Windows/SQLite startup | `backend/scripts/schema_repair.py` | `LargeBinary: "BLOB"` en `_TYPE_MAP`; normalización `BINARY` |
| Git whitespace | `INTERCAMBIO/SALIDA/*.md` (solo archivos del diff) | strip trailing whitespace — sin reformateo masivo |
| Persistencia simulada | `tests/test_cierre_brechas_horizonte.py` | `test_documentos_persisten_tras_reinicio_real`: uvicorn stop/start, PDF+CSV+logo+Horizonte |

**scripts/windows:** sin cambios de lógica startup (solo `integration_sha` metadata post-commit).

---

## C. HEAD final

_Completar tras push._

---

## D–M. Certificación sobre HEAD final

_Completar tras push y workflow GitHub PASS._

---

*Entrega exclusiva ChatGPT — decisión de promoción pendiente.*
