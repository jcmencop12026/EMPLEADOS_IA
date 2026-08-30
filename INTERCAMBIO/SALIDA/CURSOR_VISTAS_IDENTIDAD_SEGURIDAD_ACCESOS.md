# EMPLEADOS IA — Vistas identidad, seguridad y accesos

**BASE:** `33793ae` (cadena 1300/1370/1380 + vistas integraciones)  
**RAMA:** `cursor/vistas-identidad-seguridad-accesos`

---

## Objetivo

Hacer visible y revisable lo ya construido en identidad (1370), MFA/seguridad (1300) y SCIM (1380), sin nuevo motor de identidad ni duplicar RBAC.

---

## Rutas y menú

| Vista | Ruta | Menú |
|-------|------|------|
| Usuarios (grilla operativa) | `/administracion/usuarios` | Administración → Usuarios |
| Detalle identidad | `/administracion/usuarios/:userId` | Desde grilla o acciones |
| Roles y permisos | `/administracion/roles` | Administración → Roles |
| Identidad / SCIM | `/administracion/identidad` | Administración → Identidad |
| Seguridad | `/administracion/seguridad` | Administración → Seguridad |
| Mi MFA / sesiones | `/mi-seguridad` | Usuario |
| Auditoría general | `/auditoria` | Auditoría |

---

## APIs reutilizadas / ampliadas

| Endpoint | Uso |
|----------|-----|
| `GET /api/admin/users?vista=operativa` | Grilla usuarios con MFA, origen, SCIM, org |
| `GET /api/admin/users/{id}/identidad` | Detalle: permisos efectivos, MFA, sesiones, SCIM, auditoría |
| `GET /api/admin/security` | Resumen ampliado: MFA count, métricas SCIM, nota P2 |
| `GET /api/security/admin/sessions` | Sesiones con `username` y `auth_method` |
| `GET /api/identidad/scim/estado` | SCIM admin (existente) |
| `GET /api/security/*` | MFA self-service, eventos (existente) |

---

## Recorrido visual (8 pasos)

| Paso | Ruta | Qué se ve | Capacidad |
|------|------|-----------|-----------|
| 1 Login | `/login` | Acceso tenant | Autenticación local/SSO, RBAC |
| 2 Usuarios | `/administracion/usuarios` | Grilla configurable: MFA, origen, aprovisionamiento | 1300/1370/1380 en lista |
| 3 Detalle identidad | `/administracion/usuarios/:id` | Tabs datos, roles, MFA, sesiones, SCIM, auditoría | Permisos efectivos por org |
| 4 Roles/permisos | `/administracion/roles` | Matriz roles ↔ permisos | RBAC existente |
| 5 MFA | Detalle → MFA o `/mi-seguridad` | Estado, método TOTP, política; sin secretos | 1300 MFA |
| 6 Aprovisionamiento | Detalle → Aprovisionamiento o `/administracion/identidad` | Estado SCIM, eventos, métricas | 1380 SCIM |
| 7 Auditoría seguridad | Detalle → Auditoría, `/administracion/seguridad` | Login, eventos, admin | Trazabilidad multi-flujo |
| 8 Estado seguridad | `/administracion/seguridad` | Activos/inactivos, MFA, SCIM, sesiones | Resumen por organización |

---

## P2 SCIM rate limit

- **Mantenido** (no resuelto con infra paralela).
- Documentado en UI (`AdminIdentidadPage`, `AdminSecurityPage`) y en `GET /api/admin/security` (`scim_rate_limit_note`).
- Backend: límite en memoria 120 req/min por token (`scim_auth_service`).

---

## Seguridad UI

- No se muestran: contraseñas, hashes, TOTP secret, tokens SCIM completos en detalle usuario.
- Contraseña temporal solo al restablecer (flujo admin existente).
- Permisos efectivos limitados a la organización del tenant.
- Acciones (crear, desactivar, restablecer) según permisos `admin.user.*` existentes.

---

## Multiempresa

- `get_user_in_org` y vistas operativas filtran por `organization_id` del actor.
- ORG-A no lista ni detalla usuarios de ORG-B (tests `test_admin_840` multiempresa).

---

## Archivos principales

- `backend/app/services/admin_service.py` — overview, detalle identidad, security_summary
- `backend/app/routers/admin.py` — rutas nuevas
- `frontend/src/pages/admin/AdminUsersPage.tsx`
- `frontend/src/pages/admin/AdminUserDetailPage.tsx`
- `frontend/src/pages/admin/identityLabels.ts`
- `frontend/src/pages/admin/AdminSecurityPage.tsx`
- `frontend/src/pages/admin/AdminIdentidadPage.tsx`

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `npm run build` | PASS |
| `test_scim_1380.py` | 36 passed (en ejecución focal) |
| `test_bloque_1300_*` | Requiere DB de test aislada (errores de fixture preexistentes en snapshot) |

---

## Alembic

- **Sin nueva migración** (solo UI/agregación API).
- HEAD esperado en cadena: `1330b1b2c3d4f` (tras `1380a1b2c3d4e`).
