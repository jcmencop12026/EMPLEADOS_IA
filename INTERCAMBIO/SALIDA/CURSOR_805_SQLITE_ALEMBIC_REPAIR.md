# CURSOR-805 — Reparación SQLite + Alembic + Arranque

**Fecha:** 2026-08-23
**Repositorio:** jcmencop12026/EMPLEADOS_IA
**Rama:** cursor/sqlite-alembic-repair-805
**HEAD inicial:** 02a0e0f7840f0462befd58655a375399a4814bb2
**Base:** main (post merge PR #4)

## Resumen

Reparación definitiva de la inconsistencia entre SQLite legacy, modelos SQLAlchemy, Alembic y arranque real del backend.

**Resultado:** CURSOR-805: PASS

---

## Fase 1 — Backup

| Campo | Valor |
|-------|-------|
| Archivo origen | `data/enterprise_ai_os.db` |
| Backup | `data/enterprise_ai_os_PRE_REPAIR_20260823_163607.db` |
| Tamaño | 212992 bytes |
| SHA256 | `059eb00e9f02826952bbc64a1d2c13bf05f2f186d9513ca817a7de9aa6339168` |
| Verificación sqlite3 | OK |
| **BACKUP** | **PASS** |

---

## Fase 2 — Auditoría de esquema (antes de reparación)

Estado inicial de `enterprise_ai_os.db`:

| Categoría | Detalle |
|-----------|---------|
| Alembic current | `4355c73adcb8` (no head) |
| Alembic head | `5b2eb2437398` |
| Tablas faltantes (802) | employee_templates, employee_certifications, employee_instructions, employee_knowledge_sources, employee_limits, employee_model_policies, employee_test_cases, employee_test_runs, employee_tool_grants, employee_versions |
| Columnas faltantes ai_employees | code, description, role, objective, lifecycle_status, maturity, risk_level, version, owner_id, created_by_id, shadow_mode, published_at, certified_at, updated_at |
| Columnas faltantes capabilities | inputs_json, outputs_json, executor_types_json |
| capabilities.requires_approval | **Presente** en esta copia (legacy Windows puede carecer de ella) |

**SCHEMA AUDIT:** PASS (diferencias identificadas correctamente)

---

## Fase 3 — Mecanismo de reparación legacy

Script idempotente: `backend/scripts/schema_repair.py` + CLI `backend/scripts/repair_legacy_database.py`

### Estrategia

1. `Base.metadata.create_all(checkfirst=True)` — crea tablas faltantes sin tocar existentes.
2. `ALTER TABLE ADD COLUMN` — añade columnas faltantes con DEFAULT seguro para NOT NULL.
3. Backfill de datos:
   - `ai_employees`: code, lifecycle_status, maturity, risk_level, version, shadow_mode, updated_at
   - `capabilities`/`tools`: requires_approval = 0 si NULL
4. Índices vía `CREATE INDEX IF NOT EXISTS`.
5. Verificación contra metadata SQLAlchemy.
6. `alembic stamp head` — **solo tras esquema satisfecho** (no `upgrade head` ciego).

### Por qué no `alembic upgrade head` directo

- Con tablas legacy preexistentes, `4355c73adcb8` falla al intentar `CREATE TABLE` duplicada.
- Tras reparación idempotente, `upgrade` a `5b2eb2437398` también falla si las tablas 802 ya fueron creadas por `create_all`.
- Solución: reparar esquema + `stamp 5b2eb2437398` cuando metadata coincide.

### Datos preservados

| Tabla | Filas antes | Filas después |
|-------|-------------|---------------|
| organizations | 1 | 1 |
| users | 1 | 1 |
| ai_employees | 2 | 2 |
| capabilities | 2 | 2 |

**LEGACY MIGRATION:** PASS

---

## Fase 4 — Alembic

```
CURRENT = 5b2eb2437398
HEAD    = 5b2eb2437398
```

---

## Fase 5 — Arranque real

| Prueba | Resultado |
|--------|-----------|
| Backend uvicorn :8010 | OK |
| GET /health | HTTP 200 |
| Startup/seed | Sin OperationalError, IntegrityError ni FK errors |
| **BACKEND** | **PASS** |
| **HEALTH** | **PASS** |

**Corrección aplicada:** backfill `updated_at` en ai_employees (evita `TypeError: fromisoformat` cuando el valor era `0`).

---

## Fase 6 — Regresión MVP

| Suite | Resultado |
|-------|-----------|
| Tests totales | 25/25 PASS |
| CURSOR-801 | 10/10 |
| CURSOR-802 | 9/9 |
| CURSOR-803 | 6/6 |
| npm run build | PASS |

---

## Fase 7 — Scripts BAT

| Archivo | Descripción |
|---------|-------------|
| `INICIAR_EMPLEADOS_IA.bat` | Verifica venv, deps, BD, Alembic; repara si necesario; inicia backend+frontend; abre navegador |
| `DETENER_EMPLEADOS_IA.bat` | Detiene solo procesos EMPLEADOS_IA (ventanas tituladas + puertos 8010/5180) |

**BAT:** PASS (creados y validados estructuralmente)

---

## Fase 8 — Prueba visual

| Vista | Resultado |
|-------|-----------|
| Inicio | PASS |
| Centro de Operaciones | PASS |
| Directorio | PASS |
| Detalle empleado | PASS |
| Ejecuciones | PASS |
| Navegación sidebar | PASS |
| Errores API/500 | Ninguno |

**VISUAL:** PASS

---

## Archivos modificados en PR

- `backend/scripts/schema_repair.py` (nuevo)
- `backend/scripts/repair_legacy_database.py` (nuevo)
- `backend/scripts/__init__.py` (nuevo)
- `INICIAR_EMPLEADOS_IA.bat` (nuevo)
- `DETENER_EMPLEADOS_IA.bat` (nuevo)
- `.gitignore` — excluye `data/*.db` y backups
- `INTERCAMBIO/SALIDA/ULTIMA_ENTREGA.md` (actualizado)

---

## RESULTADO FINAL

**CURSOR-805: PASS**
