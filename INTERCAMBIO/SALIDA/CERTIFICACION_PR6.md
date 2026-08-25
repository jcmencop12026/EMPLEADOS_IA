# CERTIFICACIÓN PR #6 — Scheduler Timeout / Fencing (CURSOR-810C)

**Estado:** `LISTO PARA CERTIFICACIÓN GITHUB`  
**Rama:** `cursor/automations-scheduler-810`  
**HEAD inicial:** `5bd8744`  
**HEAD final:** `6169fb2`  
**NO MERGE**

---

## Tests agregados

| Archivo | Descripción |
|---------|-------------|
| `tests/certification/test_scheduler_timeout_certification.py` | Suite permanente — 10 vectores históricos + variantes |
| `tests/certification/scheduler_helpers.py` | Helpers compartidos (`run_timeout_scenario`, fixtures org/user) |
| `tests/certification/conftest.py` | Fixture PostgreSQL vía `DATABASE_URL` (skip si no disponible) |
| `pytest.ini` | Markers `certification`, `certification_intensive`, `postgresql`, `concurrency`, `windows` |

## Defectos históricos cubiertos

| # | Vector | Test(s) |
|---|--------|---------|
| 1 | Commit directo tardío tras invalidación → 0 efectos | `test_cert_01_commit_tardio_cero_efectos` |
| 2 | `get_bind` / conexión sin autoridad worker | `test_cert_02_get_bind_sin_autoridad` |
| 3 | Rutas `db.session` / `db._session` bloqueadas | `test_cert_03_rutas_session_bloqueadas` |
| 4 | SQL directo post-invalidación → 0 efectos | `test_cert_04_sql_directo_sin_persistencia` |
| 5 | SQL transaccional (COMMIT/ROLLBACK/BEGIN) bloqueado | `test_cert_05_sql_transaccional_bloqueado` |
| 6 | `materialize_gated` válido (RUNNING→commit) e inválido (FAILED→no commit) | `test_cert_06_materialize_gated_valido`, `test_cert_06_materialize_gated_invalido_tras_invalidacion` |
| 7 | Race invalidación/materialización (barrera + intensiva 100) | `test_cert_07_race_barrera_cero_efectos`, `test_cert_07_race_intensiva_100_cero_efectos` |
| 8 | Rollback worker + timeout → cero persistencia | `test_cert_08_rollback_worker_sin_persistencia` |
| 9 | Process tree padre→hijo→nieto sin descendientes vivos | `test_cert_09_process_tree_sin_descendientes_vivos`, `test_cert_09_process_tree_unitario` |
| 10 | Estado terminal: timeout no puede terminar SUCCESS | `test_cert_10_timeout_no_becomes_success` |
| PG | Commit tardío sin persistencia en PostgreSQL | `test_cert_pg_commit_tardio_sin_persistencia` |

## Resultados

### Certificación rápida

```bash
PYTHONPATH=backend:. pytest -m certification -q
```

**16 passed, 2 skipped** (PostgreSQL local no disponible)

### Certificación intensiva (race 100 iteraciones)

```bash
PYTHONPATH=backend:. pytest -m certification_intensive -q
```

**1 passed — 0/100 efectos tardíos**

### Suite completa

```bash
PYTHONPATH=backend:. pytest -q
```

**129 passed, 10 failed, 2 skipped**

Los 10 fallos son **problemas de aislamiento preexistentes** entre suites (los mismos tests pasan en ejecución focal/aislada). No se debilitaron pruebas de certificación.

### Build / audit / Git

| Comando | Resultado |
|---------|-----------|
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |

## PostgreSQL

- Tests `@pytest.mark.postgresql` requieren `DATABASE_URL` PostgreSQL.
- Local (sin PG): **2 skipped** — comportamiento esperado.
- En GitHub (QA-INFRA #12, servicio `postgres:16`):

```bash
DATABASE_URL=postgresql+psycopg2://empleados_test:empleados_test@localhost:5432/empleados_ia_test \
  PYTHONPATH=backend:. pytest -m "certification and postgresql" -v
```

## Windows

- Tests `@pytest.mark.windows` para árbol de procesos (`test_cert_09_process_tree_*`).
- Ejecutar en job Windows de QA-INFRA #12:

```bash
PYTHONPATH=backend:. pytest -m "certification and windows" -v
```

- En Linux: `test_cert_09_process_tree_unitario` valida lógica productiva; el test de subprocess real se omite si no es Windows.

## Comandos GitHub (post QA-INFRA #12 en main)

```bash
# Certificación rápida por PR
PYTHONPATH=backend:. pytest -m certification -v

# Certificación intensiva (manual / workflow_dispatch)
PYTHONPATH=backend:. pytest -m certification_intensive -v

# Grupo focal automations (workflow existente)
pytest -m automations -v
```

No duplicar `.github/workflows/qa.yml` en esta rama — ampliar QA-INFRA cuando #12 esté en `main`.

## Notas de diseño

- Timeout modelado como `AutomationRunStatus.FAILED` (diseño v4), no enum `TIMED_OUT` separado.
- Coordinación race: `threading.Barrier` / `threading.Event`, sin depender solo de `sleep`.

## Commits

| SHA | Mensaje |
|-----|---------|
| `2c97939` | `docs(cert): corregir HEAD final en CERTIFICACION_PR6` |
| `046b4f7` | `docs(cert): informe CERTIFICACION_PR6 y limpieza imports` |
| `dbe4012` | `test(cert): suite permanente scheduler timeout PR #6` |

## Pendientes

- Integrar `pytest -m certification` en workflow QA-INFRA tras merge de #12.
- Investigar 10 fallos de aislamiento en suite completa (fuera del alcance de certificación focal).
- Ejecutar tests `windows` y `postgresql` en CI multi-OS.

---

**LISTO PARA CERTIFICACIÓN GITHUB — NO MERGE**
