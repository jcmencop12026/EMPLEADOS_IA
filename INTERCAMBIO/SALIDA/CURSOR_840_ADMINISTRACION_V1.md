# CURSOR-840 — Administración Empresarial V1

## Identificación

| Campo | Valor |
|-------|-------|
| **HEAD INICIAL** | `b887a2e` |
| **HEAD FINAL** | _(post-push)_ |
| **RAMA** | `cursor/admin-users-roles-840` |
| **PR** | _(draft)_ |
| **RESULTADO** | **CURSOR-840 PASS** |
| **NO MERGE** | Sí |

---

## SCOPE

Módulo de administración empresarial multi-tenant V1:

- Usuarios (CRUD, estados, reset contraseña)
- Roles y matriz de permisos (DB-backed, roles de sistema)
- Organización (lectura/edición con estados terminales)
- Configuración empresarial (idioma, timezone, formatos)
- Seguridad (resumen real + eventos admin recientes)
- Auditoría administrativa reutilizando `write_audit`

**No integra:** PR #6/#7/#8, SSO, MFA, email, LDAP.

---

## Auditoría previa (main)

| Componente | Estado previo | Acción 840 |
|------------|---------------|------------|
| `User.role` string | Hardcoded | Extendido + DB roles |
| `Role`/`Permission` models | No existían | Creados |
| Admin API | No existía | `/api/admin/*` |
| Permisos admin | No existían | Catálogo + seed |
| Organización | GET only, loading infinito UI | Admin GET/PUT + UI con estados |
| `require_permission` | NotImplementedError | Implementado |

---

## MODELS / MIGRATION

- `Organization`: +status, timezone, config_json, updated_at
- `User`: +email, full_name, status, last_login_at, created_by_id, updated_by_id, updated_at
- `Permission`, `Role`, `RolePermission` (nuevos)
- Migración: `a840c4d5e6f7` ← `5b2eb2437398`

---

## Rutas

| Ruta frontend | API |
|---------------|-----|
| `/administracion/usuarios` | `/api/admin/users` |
| `/administracion/roles` | `/api/admin/roles`, `/permission-matrix` |
| `/administracion/organizacion` | `/api/admin/organization` |
| `/administracion/configuracion` | `/api/admin/config` |
| `/administracion/seguridad` | `/api/admin/security` |
| `/organizacion` | redirect → admin organización |

---

## Permisos admin (mínimo)

`admin.user.*`, `admin.role.*`, `admin.organization.*`, `admin.config.*`, `admin.security.view`

Roles de sistema: `admin`, `operator`, `viewer` (protegidos).

---

## Pruebas

| Métrica | Resultado |
|---------|-----------|
| TESTS PASSED | 62 |
| TESTS FAILED | 0 |
| BUILD | PASS |
| NPM AUDIT | 0 vulnerabilities |
| GIT DIFF CHECK | PASS |

Nuevo: `tests/test_admin_840.py` (16 casos)

Cross-tenant: list/get/update/deactivate bloqueados (404).

---

## Pendientes

| ID | Descripción |
|----|-------------|
| A | Integración menú jerárquico shell 830 cuando esté en main |
| B | Edición UI de permisos en roles personalizados |
| C | SSO / MFA / recuperación por email |

---

**NO MERGE**
