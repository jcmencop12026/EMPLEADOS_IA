# CIERRE GITHUB PR #6 / PR #7

**Fecha:** 2026-08-25
**Main verificado:** `1697dd2`

---

## PR #6 — `cursor/automations-scheduler-810`

| Campo | Valor |
|-------|-------|
| HEAD inicial reportado | `7b97a46` |
| HEAD tras merge main | `627c7c6` |
| HEAD final | `ba54039` |
| PR | https://github.com/jcmencop12026/EMPLEADOS_IA/pull/6 |

### Merge con main

- Merge explícito `origin/main` @ `1697dd2` → commit `627c7c6`
- Conflicto resuelto en `tests/conftest.py` (DATABASE_URL + JWT + connect_args PostgreSQL)

### Correcciones aplicadas en este cierre

1. `tzdata` en Windows (`backend/requirements.txt`) — ZoneInfo UTC
2. Escapado de rutas Windows en scripts `-c` de process tree
3. FK PostgreSQL en `test_cert_06` (crear `Automation` antes de `AutomationRun`)
4. `terminate_process_tree` / `process_tree_alive` en Windows
5. `fetch-depth: 0` en checkout backend (validación Git)
6. `invalidate_run_execution` siempre termina process tree en Windows
7. Cert Windows: criterio por ausencia de marcadores tras ventana 8s
8. **Fix PG retry/internal-event:** `_apply_run_result` solo asigna `work_plan_id` si el plan existe (evita FK abort en mocks con `plan_id` ficticio); `except Exception` en `_execute_run` hace rollback y persiste FAILED antes del retry
9. **Fix flake PG adversarial:** usernames con `uuid4().hex` completo (evita `UniqueViolation` en suite compartida)

### GitHub Actions

| Run | HEAD | Estado |
|-----|------|--------|
| 32849741410 | `fd9e60c` | FAILURE — Backend PG (4 tests retry/event) + Windows PASS |
| 32851522761 | `3d40414` | FAILURE — 1 flake UniqueViolation adversarial |
| **32852408076** | **`ba54039`** | **SUCCESS (4/4 jobs)** |

URL run PASS: https://github.com/jcmencop12026/EMPLEADOS_IA/actions/runs/32852408076

### Validaciones locales (rama `ba54039`)

| Prueba | Resultado |
|--------|-----------|
| 4 tests PG retry/event | 4 passed |
| Suite automations 810b/810c/adversarial (PostgreSQL) | 57 passed |
| Certificación rápida | 15 passed, 2 skipped |
| Certificación intensiva (race 100) | 1 passed — 0/100 efectos tardíos |

### Componentes CI — PASS

- Backend y PostgreSQL (incl. cert rápida + cert PostgreSQL + adversarial 100 iter)
- Frontend
- Validación Git
- Pruebas Windows (cert process tree)
- Certificación intensiva: solo `workflow_dispatch` (403 con token agente); ejecutada localmente PASS

### Resultado

## **PR #6 — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

**NO MERGE** (instrucción explícita)

---

## PR #7 — `codex/notifications-alerts-820`

| Campo | Valor |
|-------|-------|
| HEAD inicial reportado | `f31052c` |
| HEAD tras merge main | `7710403` |
| HEAD final | `38212fa` |
| PR | https://github.com/jcmencop12026/EMPLEADOS_IA/pull/7 |

### Merge con main

- Merge explícito `origin/main` @ `1697dd2` → commit `7710403`
- Conflictos: `pytest.ini`, `tests/conftest.py`

### Correcciones aplicadas

1. `decide_approval`: publicar `approval.completed` **antes** de `db.commit()` (`0bb7e6c`)
2. Trailing whitespace en informes INTERCAMBIO (`38212fa`)

### GitHub Actions — PASS

| Run | HEAD | Estado |
|-----|------|--------|
| 32844580516 | `7710403` | FAILURE (orchestrator e2e + git check) |
| **32845455625** | **`38212fa`** | **SUCCESS (4/4 jobs)** |

URL run PASS: https://github.com/jcmencop12026/EMPLEADOS_IA/actions/runs/32845455625

### Validaciones en CI PASS

- PostgreSQL real (migraciones upgrade/downgrade/upgrade)
- Suite backend (84+ tests)
- Certificación notificaciones
- Frontend build + npm audit
- Validación Git

### Certificación

- 11/11 casos (turno previo documentado en `CERTIFICACION_PR7.md`)

### Resultado

## **PR #7 — APTO PARA MERGE — PENDIENTE DE INTEGRACIÓN**

**NO MERGE** (instrucción explícita)
