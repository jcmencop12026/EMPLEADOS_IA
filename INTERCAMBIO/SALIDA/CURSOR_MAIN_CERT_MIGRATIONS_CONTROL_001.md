# CURSOR — MAIN-CERT-001 + MIGRATIONS-CONTROL-001

**Fecha:** 2026-08-26  
**Estado:** **LISTO PARA REAUDITORÍA** (NO MERGE)  
**Base main:** `96ad42b`  
**Rama:** `cursor/main-cert-migrations-control-001`  
**HEAD final:** `9bce435`

---

## 1. Resumen ejecutivo

Corrección post-merge de 3 FAIL en suite Windows + gobierno de migraciones Alembic.
Sin rediseño ni cambios funcionales del producto certificado en PR #19.

| Área | Resultado |
|------|-----------|
| pytest completo | **423 passed, 2 skipped** |
| npm run build | **PASS** (sin warning CSS esbuild) |
| npm audit | **0 vulnerabilidades high** |
| git diff --check | **PASS** |
| alembic heads | **972a1b2c3d4e** (único) |
| Clean install PostgreSQL | **PASS** (manual previo + CI automatizado) |

---

## 2. FAIL originales (405 PASS / 3 FAIL)

### FAIL #1 — `test_pr_diff_isolated_from_805`

| Campo | Valor |
|-------|-------|
| Tipo | **Test** (no producto) |
| Causa | Test diseñado para contexto PR exigía diff con marcadores `810` contra `origin/main`; en **main post-merge** el diff es vacío |
| Corrección | Distinguir contexto PR (validar aislamiento diff) vs main (validar infraestructura presente en árbol). Nuevo test de regresión cuando falta infraestructura |

### FAIL #2 y #3 — process tree Windows

| Campo | Valor |
|-------|-------|
| Tests | `test_adversarial_process_tree_parent_child_grandchild_no_late_effects`, `test_adversarial_process_tree_parent_child_no_late_effects` |
| Tipo | **Harness de test** (no Scheduler) |
| Causa | Rutas `C:\Users\...` embebidas en `python -c` → `SyntaxError` por secuencia `\U` |
| Corrección | Helper portable `tests/certification/process_tree_helpers.py`: scripts temporales + variables de entorno (patrón cert_09) |
| Revalidación | 6 iteraciones adversariales PASS (3+3) en Linux; harness evita escape Windows |

**Nota:** `process_tree_alive` no modificado — sin reproducción de falso positivo en esta revisión.

---

## 3. CSS warning esbuild

| Campo | Valor |
|-------|-------|
| Archivo | `frontend/src/styles.css` líneas 147-150 |
| Causa | Reglas huérfanas (`margin: 0; font-size: 18px;`) sin selector tras merge |
| Corrección | Restaurar `.login-card h1 { margin: 0; font-size: 18px; }` |
| Build posterior | **Sin warnings CSS** |

---

## 4. MIGRATIONS-CONTROL-001

### 4.1 Preflight BD (fail-closed)

**Módulo:** `backend/scripts/migration_control.py`

Antes de bootstrap/seed:

1. Si no existe `alembic_version` → OK (instalación limpia)
2. Si revisión desconocida (ej. `dbf8439340e9`) → **ABORT**
3. Mensaje en español: *"Base de datos incompatible con esta versión..."*
4. Sin stamp automático ni migración improvisada

**Integración:**

- `backend/scripts/db_startup.py` → `run_bootstrap`, escenario B
- `backend/app/main.py` → lifespan antes de bootstrap

### 4.2 Migration ledger

**Archivo:** `backend/alembic/migration_ledger.json`

- `baseline_head`: `972a1b2c3d4e`
- 16 revisiones protegidas del baseline consolidado
- CI falla si desaparece una revisión protegida

**Validador:** `backend/scripts/validate_migrations.py`

### 4.3 HEAD_REVISION actualizado

`backend/scripts/schema_repair.py`: `HEAD_REVISION = "972a1b2c3d4e"` (antes `c950a1b2c3d4` obsoleto)

### 4.4 BD legacy `empleados_ia_cert`

| Campo | Valor |
|-------|-------|
| `alembic_version` | `dbf8439340e9` (huérfana) |
| Acción | **NO modificada** — conservada como evidencia |
| Clasificación | LEGACY / REVISIÓN HUÉRFANA / NO CERTIFICADA PARA UPGRADE |
| Preflight | Rechaza arranque con mensaje controlado |

### 4.5 BD limpia `empleados_ia_cert_main`

Ya verificada manualmente: `alembic upgrade head` → `972a1b2c3d4e` PASS. No repetida en este informe.

### 4.6 Upgrade from baseline N-1

Mecanismo documentado en ledger (`upgrade_from_baseline.enabled: false`). Baseline N-1 no inventado.

---

## 5. CI

**Workflow:** `.github/workflows/qa.yml`

Nuevos pasos:

| Job | Control |
|-----|---------|
| Backend y PostgreSQL | `validate_migrations.py` + assert un solo `(head)` antes de upgrade |
| Validación Git | `validate_migrations.py` |

Controles existentes preservados: clean install PG, downgrade/upgrade, suite completa.

---

## 6. Pruebas

### Focal

```text
pytest tests/test_automations_810b.py -q          → PASS (+ test regresión infra)
pytest tests/test_automations_810c_adversarial.py -q → PASS (process tree)
pytest tests/test_migration_control.py -q         → 7 PASS
```

### Suite completa

```text
423 passed, 2 skipped
```

Skips: tests SQLite-específicos omitidos en PostgreSQL (preexistentes).

---

## 7. Git / GitHub

| Campo | Valor |
|-------|-------|
| Rama | `cursor/main-cert-migrations-control-001` |
| Base | `main` @ `96ad42b` |
| PR | _(draft, ver enlace tras creación)_ |
| Merge | **NO** |

---

## 8. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `tests/test_automations_810b.py` | Contexto PR vs main |
| `tests/test_automations_810c_adversarial.py` | Harness process tree portable |
| `tests/certification/process_tree_helpers.py` | Nuevo helper |
| `tests/test_migration_control.py` | Tests preflight/ledger |
| `backend/scripts/migration_control.py` | Preflight + ledger |
| `backend/alembic/migration_ledger.json` | Revisiones protegidas |
| `backend/scripts/validate_migrations.py` | Validador CI |
| `backend/scripts/schema_repair.py` | HEAD 972 |
| `backend/scripts/db_startup.py` | Preflight integrado |
| `backend/app/main.py` | Preflight lifespan |
| `frontend/src/styles.css` | Fix selector huérfano |
| `.github/workflows/qa.yml` | Controles migración |

---

## 9. Veredicto

```
MAIN-CERT-001 + MIGRATIONS-CONTROL-001
LISTO PARA REAUDITORÍA

NO MERGE automático.
```

Pendiente: CI GitHub 4/4 PASS en HEAD final del PR.
