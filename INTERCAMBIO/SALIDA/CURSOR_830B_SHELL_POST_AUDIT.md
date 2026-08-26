# CURSOR-830B — Corrección post-auditoría Codex (PR #8)

**Rama:** `cursor/shell-auth-dashboard-830`
**PR:** #8 (draft, sin merge)
**HEAD ANTERIOR:** `8498adf`
**HEAD NUEVO:** _(post-commit)_

## Correcciones

| ID | Defecto Codex | Solución |
|----|---------------|----------|
| A1 | Viewer puede aprobar/rechazar | `operations.approve` en `permissions.py`; `check_permission` en `/approvals/{id}/decide` |
| A2 | Wizard pierde configuración | Payload parcial (`exclude_unset`), merge de `model_policy`, wizard edit con carga completa |
| A3 | Regresión wizard | Preservación de capabilities/tools/model en edición parcial |
| A4 | Auth regression | Tests viewer/admin/cross-tenant/sin token |

## Tests nuevos (`test_shell_830b.py`)

- viewer approval/rejection denied
- admin approval allowed
- cross-tenant approval denied
- approval sin auth → 401
- wizard edit preserves capabilities/tools/model
- partial update does not clear untouched fields

## Evidencia

```
TESTS PASSED: 62
FAILED: 0
BUILD: PASS
NPM AUDIT: 0 HIGH/CRITICAL
GIT diff --check: PASS
```

**RESULTADO: CURSOR-830B PASS**
