# CURSOR — Corrección reauditoría PR #6 (810C) y PR #9 (840B)

**Fecha:** 2026-08-24  
**Estado global:** CORREGIDO Y LISTO PARA REAUDITORÍA  
**No declarado apto para merge**

---

## PR #6 — CURSOR-810C

| Campo | Valor |
|-------|-------|
| Rama | `cursor/automations-scheduler-810` |
| HEAD anterior | `03c58dfc3378ea19e6a01880963afe5b1ab180fc` |
| HEAD nuevo | `02e746f613d9fe3a6982fec0ff4016a6f66e9b91` |
| Commit | `fix(810c): cancel timed-out work and preserve wizard config` |

### Archivos modificados

- `backend/app/services/execution_guard.py` (nuevo)
- `backend/app/services/automation_service.py`
- `backend/app/services/coordinator.py`
- `frontend/src/pages/AutomationWizardPage.tsx`
- `tests/test_automations_810c.py`

### Defecto 1 — Efectos después del timeout

**Causa raíz:** `ThreadPoolExecutor` + `future.result(timeout=...)` declaraba timeout pero el hilo seguía ejecutándose; `contextvars` del guard no se propagaban al worker.

**Solución:**
- `RunExecutionGuard` cooperativo con `cancel()` / `require_execution_allowed()`
- Binding del guard en el hilo worker dentro de `_run_with_timeout()`
- Checkpoints en `_invoke_orchestration`, `_run_tool`, `_execute_task`
- `_apply_run_result` ignora resultados si el guard está cancelado
- `ExecutionCancelledError` en coordinator hace rollback sin persistir

### Defecto 2 — Wizard elimina configuración compleja

**Causa raíz:** Actualizaciones parciales reemplazaban `workflow`/`recurrence` completos; el frontend enviaba payload completo en edición.

**Solución:**
- `_deep_merge()` en `update_automation()` para estructuras anidadas
- `buildPartialPayload()` en wizard: solo campos modificados en modo edición

### Pruebas nuevas (810C)

| Test | Descripción |
|------|-------------|
| `test_timeout_no_post_timeout_side_effects` | TEST A/D — sin efectos tras timeout + espera |
| `test_timeout_blocks_post_timeout_persist` | TEST B — 0 persistencias posteriores |
| `test_timeout_stops_multi_step_execution` | TEST C — pasos posteriores no ejecutan |
| `test_wizard_partial_name_preserves_nested_workflow` | TEST A — solo name |
| `test_wizard_partial_nested_workflow_merge` | TEST B — merge anidado |
| `test_wizard_omitted_workflow_fields_preserved` | TEST C — arrays conservados |
| `test_wizard_explicit_null_clears_workflow` | TEST D — null vs omitido |

### Resultados de verificación PR #6

| Control | Resultado |
|---------|-----------|
| Suite completa (`pytest`) | **102 passed** |
| Build (`npm run build`) | **PASS** |
| NPM audit | **0 vulnerabilities** |
| Migraciones | N/A |
| `git diff --check` | **PASS** |

### Riesgos / puntos pendientes

- Cancelación cooperativa: herramientas de terceros sin checkpoints pueden seguir en CPU hasta terminar, pero no deberían persistir efectos si respetan el guard.
- No se modificaron PR #7, #8, #10.

---

## PR #9 — CURSOR-840B

| Campo | Valor |
|-------|-------|
| Rama | `cursor/admin-users-roles-840` |
| HEAD anterior | `fa1b1acb1c7a564eecc48e3c3715cf30f99d7a3e` |
| HEAD nuevo | `35058d51a8f57e27128e25130439a8b83d915f1e` |
| Commit | `fix(840b): deny inactive db roles and remove permissive fallback` |

### Archivos modificados

- `backend/app/permissions.py`
- `tests/test_admin_840b.py`
- `INTERCAMBIO/SALIDA/CURSOR_840B_ADMIN_POST_AUDIT.md` (whitespace)

### Defecto 1 — Rol DB inactivo activa fallback hardcoded

**Causa raíz:** `resolve_role_for_user()` filtraba `is_active=True`; rol inactivo devolvía `None` y `user_permissions()` aplicaba `ROLE_PERMISSIONS_FALLBACK` con permisos elevados.

**Solución:**
- `find_role_record_for_user()` busca rol sin filtrar activo
- Si existe en BD e `is_active=False` → `set()` (DENY)
- Si existe y activo → permisos de `role_permissions`
- Si no existe → fallback bootstrap (comportamiento explícito previo)
- Error de BD → `set()` (fail closed)

### Defecto 2 — git diff --check

**Causa raíz:** Trailing whitespace en documento de entrega previo.

**Solución:** Eliminado trailing whitespace en líneas afectadas.

### Pruebas nuevas (840B)

| Test | Matriz |
|------|--------|
| `test_inactive_db_role_denies_not_fallback` | TEST A — rol inactivo → DENY |
| `test_db_role_limits_permissions_no_escalation` | TEST B — solo permisos BD |
| `test_active_db_role_without_permissions_denies` | TEST C — sin permisos → DENY |
| `test_revoked_inactive_role_denies` | TEST D — revocado → DENY |
| `test_cross_tenant_role_permissions_denied` | TEST E — (existente) |
| `test_db_error_on_role_lookup_denies` | TEST G — error BD → DENY |

### Resultados de verificación PR #9

| Control | Resultado |
|---------|-----------|
| Suite completa (`pytest`) | **78 passed** |
| Migración SQLite u/d/u | **PASS** |
| Build (`npm run build`) | **PASS** |
| NPM audit | **0 vulnerabilities** |
| `git diff --check` | **PASS** |

### Riesgos / puntos pendientes

- TEST F (`operations.approve`) no aplica en esta rama; validado en PR #8/#10 según alcance.
- Fallback hardcoded sigue activo solo para roles inexistentes en BD (bootstrap).

---

## Tabla final de controles

| Control | PR #6 | PR #9 |
|---------|-------|-------|
| Defecto principal corregido | PASS | PASS |
| Tests regresión | PASS | PASS |
| Suite completa | PASS | PASS |
| Build | PASS | PASS |
| NPM audit | PASS | PASS |
| Migraciones | N/A | PASS |
| git diff --check | PASS | PASS |
| Sin cambios fuera de alcance | PASS | PASS |
| Sin merge | PASS | PASS |

---

## Restricciones respetadas

- No merge a `main`
- No modificación de PR #7, #8, #10
- Commits separados por rama
- No declarado apto para merge — pendiente reauditoría independiente
