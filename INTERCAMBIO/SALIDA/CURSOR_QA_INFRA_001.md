# CURSOR — QA-INFRA-001 Certificación automática V1

**Fecha:** 2026-08-25  
**Estado:** QA-INFRA-001 LISTO PARA VALIDACIÓN EN GITHUB  
**No declarado PASS en GitHub Actions remoto — NO MERGE**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| Código | QA-INFRA-001 |
| Rama | `cursor/qa-infra-001-12b6` |
| Base | `main` (`b887a2e`) |
| HEAD inicial | `b887a2e77c646a5b0c82d47837dfaaaed9c491ce` |
| HEAD final | *(ver commit en rama)* |

---

## ARCHIVOS CREADOS / MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `.github/workflows/qa.yml` | Workflow Certificación QA |
| `.python-version` | Python 3.12 (versión del proyecto) |
| `pytest.ini` | Marcadores focales para CI |
| `tests/conftest.py` | Respeta `DATABASE_URL` externo (PostgreSQL CI) |
| `tests/test_*.py` | Marcadores `auth`, `tenant`, `operations`, `migrations`, `windows` |
| `DOCS/QA_INFRA_001.md` | Documentación en español |

---

## JOBS DEL WORKFLOW

| Job (español) | Runner | Controles |
|---------------|--------|-----------|
| Backend y PostgreSQL | `ubuntu-latest` | pip, pytest, Alembic, PostgreSQL 16 efímero |
| Frontend | `ubuntu-latest` | npm ci, build, audit |
| Validación Git | `ubuntu-latest` | git diff --check |
| Pruebas Windows | `windows-latest` | pytest test_db_startup_805e.py |

**Triggers:** `pull_request`, `workflow_dispatch` (con parámetro `grupo_focal`).

**Sin:** despliegues, `continue-on-error` en controles obligatorios, dashboard QA.

---

## POSTGRESQL

- Service container `postgres:16` en job Linux
- `DATABASE_URL=postgresql+psycopg2://empleados_test:empleados_test@localhost:5432/empleados_ia_test`
- Credenciales solo de testing; sin secretos reales
- Paso explícito de conexión (`SELECT 1`)

**PostgreSQL local en agente:** no disponible para certificación local completa.

---

## MIGRACIONES (CI)

Secuencia en job Backend:

1. `alembic upgrade head`
2. `alembic downgrade 4355c73adcb8` (revisión base)
3. `alembic upgrade head`

Head actual en main: `5b2eb2437398`. Sin múltiples heads detectados.

---

## MARCADORES PYTEST

`auth`, `tenant`, `knowledge`, `notifications`, `automations`, `migrations`, `operations`, `windows`

Ejemplo CI manual: `grupo_focal: operations` o `grupo_focal: tests/test_orchestrator_e2e.py`

---

## RESULTADOS LOCALES

| Comando | Resultado |
|---------|-----------|
| `python -m pytest` | PASS (46) |
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |
| Sintaxis `qa.yml` | PASS (YAML válido) |
| GitHub Actions remoto | **NO EJECUTADO** — validar al abrir PR |

---

## LIMITACIONES

1. No se afirma PASS remoto de GitHub sin ejecución allí.
2. Tests `automations` / scheduler de PR #6 no existen en `main`; marcador preparado.
3. Job Windows ejecuta tests SQLite existentes; listo para `-m windows` cuando se integren tests de automatizaciones.
4. PostgreSQL real certificado en CI solo tras primera ejecución en GitHub.

---

## QUÉ SE VALIDARÁ AUTOMÁTICAMENTE AL ABRIR PR

- Tests backend completos contra PostgreSQL efímero
- Migraciones Alembic upgrade/downgrade/upgrade
- Build frontend y auditoría npm
- Espacios en blanco conflictivos en diff
- Tests Windows de arranque SQLite

---

## ESTADO FINAL

**QA-INFRA-001 LISTO PARA VALIDACIÓN EN GITHUB**

No merge.
