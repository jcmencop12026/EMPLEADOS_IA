# CURSOR — Segunda corrección reauditoría PR #6 (810C) y PR #9 (840B)

**Fecha:** 2026-08-24
**Estado global:** CORREGIDO Y LISTO PARA NUEVA REAUDITORÍA
**No declarado apto para merge**

---

## PR #6 — CURSOR-810C

| Campo | Valor |
|-------|-------|
| Rama | `cursor/automations-scheduler-810` |
| HEAD inicial (reauditoría) | `fa07040e8b38efebb309677d72a2c6bdd7ded082` |
| HEAD final | `5d0a9ff8652ec82bdefbc91557ef8612f2d67005` |
| Commit | `fix(810c): commit-gated execution fence for real timeout isolation` |

### Causa raíz

`RunExecutionGuard` cooperativo no impedía commits tardíos por:
- sesión SQLAlchemy compartida entre hilos;
- ausencia de fencing atómico en BD;
- race TOCTOU entre cancelación y `commit()`;
- subprocess sin terminación forzada.

### Arquitectura implementada

**Fase 1 — Ejecución:** worker en sesión aislada (`SessionLocal`) con `FenceToken(run_id, generation)`.

**Fase 2 — Commit gated:** `commit_gated()` valida token en memoria + `execution_generation` y `status=RUNNING` con `SELECT FOR UPDATE` antes de cada commit en coordinator.

**Invalidación:** `invalidate_run_execution()` incrementa generación en BD y memoria; mata subprocess registrados.

**Columna:** `automation_runs.execution_generation` (migración `b810c2f3e4d5`).

### Archivos modificados

- `backend/app/services/execution_guard.py` (reescrito)
- `backend/app/services/automation_service.py`
- `backend/app/services/coordinator.py`
- `backend/app/automation_models.py`
- `backend/alembic/versions/b810c2f3e4d5_execution_fence_810c.py`
- `tests/test_automations_810c_adversarial.py` (nuevo)

### Pruebas adversariales

| Test | Resultado |
|------|-----------|
| A Memoria tardía | PASS |
| B Archivo tardío | PASS |
| C SQLite/DB tardía | PASS |
| D Subprocess | PASS |
| E Finally funcional | PASS |
| F Race 100 iteraciones | PASS — **0/100 efectos tardíos** |
| G Thread rezagado | PASS |
| H Callback/BD tardía | PASS |
| J Estado FAILED inmutable | PASS |

### Resultados

| Control | Resultado |
|---------|-----------|
| Suite completa | **111 passed** |
| Build | PASS |
| npm audit | 0 vulnerabilities |
| git diff --check | PASS |
| Deep merge wizard | PASS (sin cambios) |

---

## PR #9 — CURSOR-840B

| Campo | Valor |
|-------|-------|
| Rama | `cursor/admin-users-roles-840` |
| HEAD inicial (reauditoría) | `0e25e3e0189b5ed9c029ee9d863d0f40782a1349` |
| HEAD final | `4d1a8a038f525df74ded80d5d40edb9d44be93f4` |
| Commit | `fix(840b): fail-closed roles deny ambiguous and remove runtime fallback` |

### Causa raíz

- `user_permissions()` aplicaba `ROLE_PERMISSIONS_FALLBACK` para roles inexistentes y sin BD;
- roles globales duplicados resolvían con `.first()` arbitrario;
- `is_active` no validado estrictamente (fail-open).

### Solución

- **DENY BY DEFAULT:** `user_permissions()` solo desde `resolve_authoritative_role()`;
- sin fallback runtime (referencia `ROLE_PERMISSIONS_FALLBACK` solo para seed);
- `is_role_strictly_active()` — solo `is_active is True`;
- ambigüedad org/global duplicada → DENY + log;
- migración `b840c3e4f5a6` deduplica globales + índice único parcial.

### Tests nuevos

- `test_nonexistent_role_denies_no_fallback`
- `test_duplicate_global_role_denies`
- `test_corrupt_is_active_denies` (parametrizado)
- `test_corrupt_is_active_in_db_denies`
- `test_empty_role_code_denies`

### Resultados

| Control | Resultado |
|---------|-----------|
| Suite completa | **87 passed** |
| Migración u/d/u | PASS |
| Build | PASS |
| npm audit | 0 vulnerabilities |
| git diff --check | PASS |

---

## Tabla de controles

| Control | PR #6 | PR #9 |
|---------|-------|-------|
| Hallazgo Codex corregido | PASS | PASS |
| Pruebas adversas | PASS | PASS |
| Race 100 ejecuciones | PASS (0/100) | N/A |
| Memoria tardía | PASS | N/A |
| Archivo tardío | PASS | N/A |
| DB tardía | PASS | N/A |
| Subprocess tardío | PASS | N/A |
| Finally tardío | PASS | N/A |
| Rol inexistente | N/A | PASS |
| Rol duplicado | N/A | PASS |
| is_active corrupto | N/A | PASS |
| Fail closed | N/A | PASS |
| Suite completa | PASS | PASS |
| Build | PASS | PASS |
| npm audit | PASS | PASS |
| Migración | PASS | PASS |
| git diff --check | PASS | PASS |

---

## Riesgos residuales

- PR #6: herramientas externas no integradas con `commit_gated`/`run_subprocess` requieren adopción explícita.
- PR #9: instalaciones con datos legacy duplicados deben aplicar migración `b840c3e4f5a6`.

**NO MERGE — pendiente nueva reauditoría Codex.**
