# CURSOR — V1 PAQUETE C — MULTI-TENANT / ALTA DE EMPRESAS

**Fecha/hora UTC:** 2026-08-28
**Proyecto:** EMPLEADOS_IA
**Paquete:** V1 Paquete C — Multi-tenant / Alta de empresas / Aislamiento

---

## 1. RAMA, BASE, HEAD, PR

| Campo | Valor |
|-------|-------|
| **Rama** | `cursor/v1-multitenant` |
| **Base V1** | `dc51d5ce4852d37e5eef8b5112d1260a002ee3bf` |
| **HEAD final** | Ver commit actual en rama |
| **PR** | [#29](https://github.com/jcmencop12026/EMPLEADOS_IA/pull/29) (draft, sin merge) |

---

## 2. PRECHECK OBLIGATORIO

```
git fetch origin --prune          → OK
git rev-parse --show-toplevel     → /workspace (D:\EMPLEADOS_IA en entorno Windows)
git branch --show-current         → cursor/v1-multitenant ✓
git rev-parse HEAD                → f424ca0984b70fd97c181a1bdfc9b5cf8a344c0a
git rev-parse origin/main         → dc51d5ce4852d37e5eef8b5112d1260a002ee3bf (base V1) ✓
git status --short                → limpio (sin archivos no versionados tocados)
```

Rama verificada: **EXACTAMENTE** `cursor/v1-multitenant`. Base V1: `dc51d5c`. Rama contiene commits de Paquete C sobre la base.

---

## 3. MODELO TENANT

Se reutiliza la entidad existente **`Organization`** como tenant/empresa.

| Campo | Descripción |
|-------|-------------|
| `id` | UUID |
| `name` | Nombre de la empresa |
| `slug` | Identificador único (nuevo) |
| `status` | `ACTIVE` / `INACTIVE` |
| `timezone` | Zona horaria |
| `config_json` | Metadatos mínimos |
| `created_at` / `updated_at` | Timestamps |

No se introdujeron entidades `Company` ni `Tenant` paralelas.

---

## 4. MAPA DE MODELOS (RESUMEN)

| Modelo | `organization_id` | Alcance actual | Riesgo cross-tenant | Acción |
|--------|-------------------|----------------|---------------------|--------|
| Organization | — (es el tenant) | Global | Bajo | API plataforma |
| User | Sí | Por tenant | Bajo | Sin cambio |
| AIEmployee, WorkPlan, Automation, Knowledge*, FinOps*, etc. | Sí | Filtrado por tenant | Bajo | Verificado en tests |
| Roles globales | `NULL` | Sistema | Bajo | Sin cambio |

\* Todos los dominios certificados mantienen filtro `organization_id == user.organization_id`.

---

## 5. ALTA DE EMPRESA

Flujo implementado:

```
CREAR EMPRESA (POST /api/platform/organizations)
  → validar nombre/slug/duplicados
  → crear Organization ACTIVE
  → bootstrap_orchestration + bootstrap_salud
  → crear administrador inicial (rol admin del tenant)
  → auditoría platform.organization.created
```

Solo usuarios con permiso **`platform.organization.create`** (rol `superadmin`) pueden crear empresas.

---

## 5. USUARIOS Y EMPRESA

- Todo usuario queda asociado a `organization_id`.
- El scope se deriva del usuario autenticado en BD (no del JWT `org`).
- No se acepta `organization_id` arbitrario en schemas de entrada sensibles.
- Administradores de tenant (`admin`) **no** tienen permisos de plataforma.

---

## 6. AISLAMIENTO BACKEND

- Patrón existente preservado: filtros por `user.organization_id`.
- Nuevo módulo `tenant_scope.py` con validación de empresa activa.
- `get_current_user` y login bloquean acceso si empresa `INACTIVE`.

---

## 7. SUPERADMIN

| Aspecto | Comportamiento |
|---------|----------------|
| Rol | `superadmin` (global, sistema) |
| Permisos plataforma | `platform.organization.view/create/manage` |
| Permisos negocio | Solo en **su** organización (mismos que admin) |
| Asignación | Bloqueada vía `PROTECTED_ASSIGNMENT_ROLE_CODES` |
| Bootstrap | Usuario `admin` promovido a `superadmin` en instalaciones existentes |

---

## 8. EMPRESA INACTIVA

| Acción | Comportamiento |
|--------|----------------|
| Login usuarios del tenant | **Bloqueado** — 401 «empresa inactiva» |
| API autenticada | **Bloqueado** — 403 en `get_current_user` |
| Datos históricos | **Conservados** — sin borrado |
| Reactivación | `POST /api/platform/organizations/{id}/status` → `ACTIVE` |
| Automatizaciones nuevas | Scheduler ya filtra orgs `ACTIVE` |

---

## 9. FRONTEND

| Pantalla | Ruta | Permiso |
|----------|------|---------|
| Empresas (listado/crear/activar) | `/administracion/empresas` | `platform.organization.view` |
| Organización (tenant actual) | `/administracion/organizacion` | `admin.organization.view` |

Textos en español. Diseño compacto existente respetado.

---

## 10. MIGRACIONES

| Migración | Descripción |
|-----------|-------------|
| `c1a2b3c4d5e6_multitenant_organization_slug_v1.py` | Añade `slug` único a `organizations` con backfill legacy |

- Head único: `c1a2b3c4d5e6` (revises `1030a1b2c3d4e`)
- Upgrade probado en SQLite
- Downgrade: elimina columna `slug`
- **Compatibilidad legacy:** org bootstrap recibe slug automático; datos preservados

### Conflictos potenciales de integración

| Paquete | Riesgo |
|---------|--------|
| **D** (seguridad) | Sin conflicto directo; D endurece RBAC general |
| **E** (PG tests) | Sin dependencia |
| **B** (LLM) | `organization_id` ya presente en modelos para futuro scoping LLM |

---

## 11. COMPATIBILIDAD LEGACY

- Instalación mono-organización sigue funcionando.
- Organización bootstrap conserva datos y recibe `slug` automático.
- Admin bootstrap promovido a `superadmin` para habilitar alta de empresas.
- Tests existentes compatibles vía `before_insert` auto-slug en `Organization`.

---

## 12. ARCHIVOS MODIFICADOS

### Backend
- `backend/app/models.py` — campo `slug` + auto-slug legacy
- `backend/app/permissions.py` — permisos plataforma + rol superadmin
- `backend/app/seed_permissions.py` — label superadmin
- `backend/app/seed.py` — bootstrap superadmin + slug
- `backend/app/deps.py` — bloqueo empresa inactiva
- `backend/app/routers/auth.py` — bloqueo login empresa inactiva
- `backend/app/routers/platform.py` *(nuevo)*
- `backend/app/schemas_platform.py` *(nuevo)*
- `backend/app/schemas_admin.py` — slug en OrganizationAdminOut
- `backend/app/services/tenant_service.py` *(nuevo)*
- `backend/app/tenant_scope.py` *(nuevo)*
- `backend/app/main.py` — router platform
- `backend/alembic/versions/c1a2b3c4d5e6_multitenant_organization_slug_v1.py` *(nuevo)*

### Frontend
- `frontend/src/api.ts` — API plataforma
- `frontend/src/pages/admin/AdminCompaniesPage.tsx` *(nuevo)*
- `frontend/src/pages/admin/AdminOrganizationPage.tsx` — muestra slug
- `frontend/src/App.tsx` — ruta empresas
- `frontend/src/AppShell.tsx` — menú empresas

### Tests
- `tests/test_multitenant_v1.py` *(nuevo — 14 tests)*

---

## 13. PRUEBAS Y RESULTADOS

| Caso | Test |
|------|------|
| A. Alta de empresa | `test_superadmin_can_list_and_create_company` |
| B. Duplicados | `test_duplicate_slug_rejected` |
| C. Admin inicial | incluido en alta |
| D. Tenant A / B | `_create_tenant_user` + cross-tenant |
| E. Cross-tenant list | `test_cross_tenant_employee_list_denied` |
| F. Cross-tenant detail | knowledge, automation, operations, opportunities |
| G. Cross-tenant edit | `test_cross_tenant_employee_detail_edit_execute_denied` |
| H. Cross-tenant delete | N/A (endpoints devuelven 404) |
| I. Cross-tenant execute | `test_cross_tenant_employee_detail_edit_execute_denied` |
| J. Empresa inactiva | `test_inactive_company_blocks_login` |
| K. Agent Factory | `test_cross_tenant_employee_list_denied` |
| L. Knowledge | `test_cross_tenant_knowledge_denied` |
| M. Automations | `test_cross_tenant_automation_denied` |
| N. FinOps | `test_cross_tenant_finops_denied` |
| O. Opportunities | `test_cross_tenant_opportunities_denied` |
| P. Superadmin | `test_superadmin_*`, `test_bootstrap_org_has_slug` |
| Q. Legacy | `test_bootstrap_org_has_slug` |

```
tests/test_multitenant_v1.py                    14 passed
tests/test_admin_840.py + 840b                  PASS
tests/test_automations_810b.py                  PASS
tests/test_knowledge_930.py                     PASS
tests/test_finops_950_adversarial.py            PASS
tests/test_oportunidades_proactivas_1030.py     PASS
────────────────────────────────────────────────────────
Suite Paquete C + regresión relevante:         144 passed
Frontend build:                                 PASS
git diff --check (archivos paquete):            PASS
```

Entorno: SQLite temporal (`DATABASE_URL` no definido).

---

## 14. RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| Bootstrap admin pasa a superadmin | Necesario para alta empresas V1; tenant admins siguen sin permisos plataforma |
| Username global único | Comportamiento existente; documentado |
| Integración con Paquete D | RBAC general en PR #28; sin duplicar aquí |

---

## 15. DEPENDENCIAS

| Paquete | Relación |
|---------|----------|
| **B** (LLM) | `organization_id` listo para scoping futuro; sin adaptadores IA |
| **D** (seguridad) | Hardening RBAC en PR #28; este paquete solo scope multi-tenant |
| **E** (PG tests) | Sin dependencia |

---

## 16. PENDIENTES V1.1

- UI de cambio de tenant para usuarios multi-org (fuera alcance V1)
- Username por tenant (requiere migración)
- Rate limiting login (Paquete D / V1.1)

---

## 17. VEREDICTO

### **APTO PARA INTEGRACIÓN**

- Múltiples empresas creables: **SÍ**
- Admin inicial funciona: **SÍ**
- Datos aislados cross-tenant: **SÍ** (tests adversariales PASS)
- Legacy sin pérdida de datos: **SÍ**
- Empresa inactiva bloqueada: **SÍ**
- Frontend mínimo: **SÍ**
- Migración segura: **SÍ**
- PR creado, **no mergeado**

---

*Ciclo 810C–1030 no reabierto. Sin LLM, Docker, Paquete D/E ni nuevas verticales.*
