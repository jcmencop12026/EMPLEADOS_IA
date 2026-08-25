# CURSOR — QA-INFRA-001 Certificación automática V1

**Fecha:** 2026-08-25
**Estado:** Pendiente verificación GitHub Actions tras corrección focal
**No declarado PASS en GitHub Actions remoto — NO MERGE**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| Código | QA-INFRA-001 |
| PR | #12 |
| Rama | `cursor/qa-infra-001-12b6` |
| HEAD anterior (auditado) | `d0a119823178a5b918248f23cc429a20a0dcf955` |
| HEAD nuevo | `eb78ac0` → *(ver commit downgrade FK)* |

---

## CORRECCIÓN FOCAL (post-auditoría GitHub)

### 1. Backend y PostgreSQL — FAIL

| Campo | Detalle |
|-------|---------|
| Migración | `5b2eb2437398_agent_factory_802.py` |
| SQL problemático | `UPDATE ai_employees SET shadow_mode = 0 WHERE shadow_mode IS NULL` |
| Excepción | `psycopg2.errors.DatatypeMismatch: column "shadow_mode" is of type boolean but expression is of type integer` |
| Causa | PostgreSQL no acepta literal entero `0` en columna `BOOLEAN`; SQLite sí lo tolera |
| Corrección | `op.get_bind().execute(sa.text(...), {"shadow_mode": False})` con bindparam tipado |

### 2. Validación Git — FAIL

| Archivo | Líneas | Causa |
|---------|--------|-------|
| `INTERCAMBIO/SALIDA/CURSOR_QA_INFRA_001.md` | 3-4 | Trailing whitespace (`  ` al final de línea markdown) |

Eliminado sin desactivar `git diff --check`.

### 3. Búsqueda de patrones equivalentes

Revisadas todas las migraciones en `upgrade head`:

- Único patrón `boolean = 0` encontrado: `shadow_mode` en `5b2eb2437398`
- `version = 1` es entero → compatible con PostgreSQL

### 4. Nuevo bloqueo tras shadow_mode (downgrade PostgreSQL)

| Campo | Detalle |
|-------|---------|
| Paso CI | `alembic downgrade 4355c73adcb8` |
| Migración | `5b2eb2437398_agent_factory_802.py` (downgrade) |
| SQL/op | `op.drop_constraint(None, 'ai_employees', type_='foreignkey')` |
| Excepción | `CompileError: Can't emit DROP CONSTRAINT ... it has no name` |
| Causa | PostgreSQL exige nombre explícito; upgrade crea `fk_ai_employees_owner` y `fk_ai_employees_created_by` |
| Corrección | `drop_constraint` con nombres explícitos en downgrade |

**Nota:** `upgrade head` ya PASS en GitHub tras corrección `shadow_mode`.

---

| Campo | Valor |
|-------|-------|
| Archivo migración | `backend/alembic/versions/5b2eb2437398_agent_factory_802.py` |
| Archivo informe | `INTERCAMBIO/SALIDA/CURSOR_QA_INFRA_001.md` |

---

## RESULTADOS LOCALES (post-corrección)

| Comando | Resultado |
|---------|-----------|
| `python -m pytest` | PASS (46) |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |
| PostgreSQL real local | **NO DISPONIBLE** en este entorno |

---

## GITHUB ACTIONS

Tras push, verificar ejecución del workflow **Certificación QA** en PR #12.

Objetivo (4 jobs):

| Job | Estado esperado |
|-----|-----------------|
| Backend y PostgreSQL | PASS |
| Frontend | PASS |
| Validación Git | PASS |
| Pruebas Windows | PASS |

**Estado final:** *(completar tras ejecución remota)*

---

## ESTADO FINAL

Pendiente de los 4 checks verdes en GitHub.

No merge.
