# CURSOR-840B — Corrección post-auditoría Codex (PR #9)

**Rama:** `cursor/admin-users-roles-840`
**PR:** #9 (draft, sin merge)
**HEAD ANTERIOR:** `5c1e4b3`
**HEAD NUEVO:** `4f7ba18`

## Correcciones

| ID | Defecto Codex | Solución |
|----|---------------|----------|
| B1 | Migración SQLite rota (`create_foreign_key` inválido) | FK en `batch_alter_table` con firma correcta; ciclo upgrade/downgrade/upgrade validado |
| B2 | Autorización híbrida DB/fallback | `user_permissions()` usa BD como fuente única si el rol existe; fallback solo sin fila de rol; documentado en `permissions.py` |
| B3 | Escalación de privilegios | `assert_role_assignable`, `assert_permission_subset`, bloqueo self-elevation, roles protegidos |
| B4 | Matriz permisos solo lectura | `AdminRolesPage` con edición de roles personalizados, guardar/cancelar, API `updateRolePermissions` |
| B5 | Tenant / role assignment | Validación cross-tenant en servicio y tests negativos |
| B6 | Regresión | Suite completa + build + npm audit |

## Archivos clave

- `backend/alembic/versions/a840c4d5e6f7_administration_840.py`
- `backend/app/permissions.py`
- `backend/app/services/admin_service.py`
- `backend/app/routers/admin.py`
- `backend/app/routers/agent_factory.py` (pasa `db` a `check_permission`)
- `frontend/src/pages/admin/AdminRolesPage.tsx`
- `frontend/src/api.ts`
- `tests/test_admin_840b.py`

## Tests nuevos (`test_admin_840b.py`)

- `test_migration_a840_sqlite_upgrade_downgrade_upgrade`
- `test_authorization_single_source_db_not_fallback`
- `test_privilege_escalation_superadmin_denied`
- `test_privilege_escalation_platform_role_denied`
- `test_privilege_escalation_extra_permissions_denied`
- `test_protected_system_role_permissions_denied`
- `test_cross_tenant_role_permissions_denied`
- `test_cross_tenant_role_assignment_denied`
- `test_matrix_edit_add_permission`
- `test_matrix_edit_remove_permission`
- `test_self_role_elevation_denied`

## Evidencia

```
TESTS PASSED: 73
FAILED: 0
SKIPPED: 0
NPM AUDIT: 0 HIGH/CRITICAL
BUILD: PASS
GIT diff --check: PASS
```

## Resultado

**CURSOR-840B PASS** — sin merge.
