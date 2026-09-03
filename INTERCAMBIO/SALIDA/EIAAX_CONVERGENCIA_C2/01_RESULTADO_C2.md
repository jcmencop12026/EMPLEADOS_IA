# 01 — Resultado Bloque C2

**Proyecto:** EIAAX / EMPLEADOS_IA
**Rama:** `cursor/eiaax-convergencia-v1-v2`
**Fecha UTC:** 2026-08-31
**Tipo:** Gobierno multiempresa y operación central

---

## SHA

| Referencia | SHA |
|---|---|
| **SHA inicial C2** (C1-R1 certificado) | `3226ba5ee9b998547c7026c98b69972dfacd2d3d` |
| **SHA candidato C2** (único) | `afce8c34229addb2fdd0fce5b8c99b800e4f29d7` |
| V1 certificado (intacto) | `e8cb853a2c447fd5e136a0907e44d68ce2c8cf81` |
| V2 certificado (intacto) | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| Tag Fase 2 (intacto) | `fase2-candidato-final-certificado` → `dc1e6cd` |

---

## Objetivo cumplido

Consolidación de **MULTIEMPRESA + RBAC + SUPERADMIN + Centro de Control + Mi Trabajo** como capacidad coherente y utilizable en el producto convergido.

---

## Causa de cambios

| Hallazgo | Causa | Corrección |
|---|---|---|
| Notificaciones en Mi Trabajo cross-org incorrectas | `_notification_visible_query` filtraba por `user.organization_id` en lugar del `org_id` resuelto | Filtro por `org_id` activo |
| SUPERADMIN podía consultar org inactiva vía `?organization_id=` | `resolve_organization_id` no validaba estado ACTIVE | `ensure_organization_active()` en resolución |
| Contexto organizacional invisible en UI | Frontend no enviaba `organization_id` ni mostraba org activa | `OrganizationProvider` + selector en topbar |

---

## Archivos modificados

### Backend
```
backend/app/services/control_center_service.py   — resolve_organization_id + org activa
backend/app/services/trabajo_service.py          — notificaciones scoped por org_id
```

### Frontend
```
frontend/src/hooks/useOrganizationContext.tsx    (nuevo)
frontend/src/components/OrganizationContextBar.tsx (nuevo)
frontend/src/api.ts                              — organizationId en CC y trabajo
frontend/src/auth/session.ts                     — limpia contexto org al logout
frontend/src/AppShell.tsx                        — provider + badge con org activa
frontend/src/pages/CentroControlPage.tsx         — org activa en datos
frontend/src/pages/TrabajoPage.tsx               — org activa en bandeja
frontend/src/styles.css                          — estilos selector org
```

### Pruebas
```
tests/test_convergencia_c2.py                    (nuevo — matriz A-P)
```

### Sin cambios
- Migraciones Alembic (head único `1341a1b2c3d4e`)
- Permisos RBAC existentes (sin permisos nuevos ni eliminados)
- C1-R1 home routing (`HomePage`, `resolveHomeRoute`, `NoModulesPage`)
- V1/V2 certificados, tags, respaldos

---

## Migraciones

**NO requeridas.** Estructuras V2 existentes son suficientes.

## Permisos modificados

**NO.** Se reutilizan `platform.organization.view`, `control_center.view` y permisos de Mi Trabajo existentes.

---

## P0 / P1 / P2

| Severidad | Nuevos |
|---|---|
| P0 | **NINGUNO** |
| P1 | **NINGUNO** |
| P2 | **NINGUNO** introducido por C2 |

### Riesgos pendientes (fuera alcance C2)
- Endpoints fuera de CC/trabajo/auditor/finops no exponen `organization_id` override para SUPERADMIN (diseño V1.1 documentado; no bloqueante C2).

---

## Veredicto

**C2 APTO PARA CERTIFICACIÓN**
