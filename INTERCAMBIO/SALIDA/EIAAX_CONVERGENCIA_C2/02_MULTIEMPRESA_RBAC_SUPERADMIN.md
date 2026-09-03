# 02 — Multiempresa, RBAC y SUPERADMIN (C2)

**Proyecto:** EIAAX / EMPLEADOS_IA
**Fecha UTC:** 2026-08-31

---

## Multiempresa

### Autoridad backend
- Consultas, filtros, endpoints y conteos de CC y Mi Trabajo usan `resolve_organization_id()`.
- Organización A no accede a datos de B sin `platform.organization.view`.
- Usuarios tenant reciben **403** al pasar `?organization_id=` ajeno (verificado).

### Corrección material
- Notificaciones en `collect_items()` ahora filtran por `org_id` resuelto, no por org home del usuario.

### Organizaciones inactivas
- `resolve_organization_id()` invoca `ensure_organization_active()` para org home y cross-org.

---

## RBAC

| Capacidad | Permiso | Backend | Frontend |
|---|---|---|---|
| Centro de Control | `control_center.view` | 403 sin permiso | `HomePage` / menú |
| Mi Trabajo | OR-lista existente (`operations.view`, `notification.view`, …) | `can_access_trabajo()` | menú + ruta |
| Cross-org SUPERADMIN | `platform.organization.view` | `check_permission` en resolver | selector visible solo con permiso |
| Plataforma empresas | `platform.organization.*` | `/api/platform/organizations` | AdminCompaniesPage |

No se crearon permisos redundantes.

---

## SUPERADMIN cross-org

### Mecanismo
- Query param `organization_id` en:
  - `/api/centro-control/resumen-ejecutivo`
  - `/api/trabajo/items`
  - `/api/trabajo/resumen`
- Requiere `platform.organization.view`; valida existencia y estado ACTIVE.

### Frontend (C2)
- `OrganizationProvider` — contexto en `sessionStorage` (tab-scoped).
- `OrganizationContextBar` — selector en topbar para usuarios plataforma.
- Al cambiar org: evento `organization-context-changed` refresca badge Mi Trabajo, CC y bandeja.
- Indicador visible: **"Viendo: {organización}"** cuando difiere de org home.

### Trazabilidad
- Respuestas API incluyen `organization_id` en resumen CC y filtros aplicados en trabajo.
- UI muestra nombre de organización activa en CC y Mi Trabajo.

---

## Seguridad preservada

Login hotfix, MFA, SSO, sid/sesiones, RBAC deny-by-default, Knowledge auth, DATABASE_URL, Docker — **sin debilitación**.
