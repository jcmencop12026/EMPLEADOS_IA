# 04 — RBAC, multiempresa y Partners

---

## Autoridad RBAC

| Capa | Fuente | Regla |
|------|--------|-------|
| Permisos | `backend/app/permissions.py` | Deny-by-default |
| Enforcement | `check_permission(user, code, organization_id=...)` | Obligatorio en routers |
| Frontend | `frontend/src/auth/permissions.ts` | Espejo; no sustituye backend |
| Roles | `Role` + `RolePermission` + SCIM 1380 | Por organización |

---

## Aislamiento tenant

**Regla absoluta:** toda query de datos de negocio filtra `organization_id` del contexto autenticado.

Excepciones controladas:
- Usuario plataforma con permiso explícito cross-tenant (auditoría, admin)
- Partner con **grant activo** + membresía partner + RBAC partner — nunca solo grant

---

## Partners (`2afd673` / `fe646d4`)

### Modelo

| Entidad | Tabla | Rol |
|---------|-------|-----|
| `Partner` | `partners` | Aliado comercial (plataforma) |
| `PartnerOrganizationGrant` | `partner_organization_grants` | Acceso explícito Partner→Org |
| `PartnerUserMembership` | `partner_user_memberships` | Usuario↔Partner con rol |
| `PartnerAuditEvent` | `partner_audit_events` | Trazabilidad partner |

### Scopes grant (`PARTNER_SCOPE_CODES`)

- `organizacion.read`
- `cc.view`
- `trabajo.view`
- `evaluacion.view`
- `oportunidades.view`

---

## Interacción correcta: membresía + grant + RBAC + visibilidad

```
Usuario autenticado
    │
    ├─ ¿Membresía PartnerUserMembership activa?
    │       NO → flujo tenant normal (User.organization_id)
    │       SÍ → continuar
    │
    ├─ ¿PartnerOrganizationGrant ACTIVO para org objetivo?
    │       NO → 403 (asociación sola NO basta)
    │       SÍ → continuar
    │
    ├─ ¿Scope grant cubre recurso?
    │       NO → 403
    │       SÍ → continuar
    │
    ├─ ¿RBAC partner rol (ADMIN/OPERADOR/LECTOR)?
    │       NO → 403
    │       SÍ → continuar
    │
    └─ ¿Clasificación + visibilidad del objeto?
            RESTRINGIDO / INTERNO → 403 salvo permiso explícito
            VISIBLE_ENTIDAD / COMPARTIDO → permitir según scope
```

---

## Conflictos

### P-01 — Grant sustituye RBAC

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Diseño tentativo en integraciones partner |
| **COMPONENTES** | `partner_service`, routers partners, evaluación |
| **AUTORIDAD** | RBAC + grant como AND, no OR |
| **CONSERVAR** | `PartnerOrganizationGrant` |
| **ADAPTAR** | Middleware partner valida triple: membership + grant + permission |
| **RETIRAR** | Rutas `evaluacion.view` que omitan `check_permission` |
| **RIESGO** | Bypass multiempresa por grant expirado o scope amplio |

### P-02 — Grant sustituye tenant isolation

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Queries partner sin `organization_id` |
| **COMPONENTES** | `partner_service`, CC, trabajo |
| **AUTORIDAD** | `organization_id` del grant, no del partner |
| **CONSERVAR** | Grant con `organization_id` FK |
| **ADAPTAR** | Contexto `effective_organization_id` desde grant |
| **RETIRAR** | Listados globales cross-tenant |
| **RIESGO** | Datos de tenant B visibles a partner de tenant A |

### P-03 — Partner ve economía privada

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Scopes amplios en propuestas CN |
| **COMPONENTES** | CN, motor económico, partners |
| **AUTORIDAD** | Permisos `negocio.economy.private` — no en PARTNER_SCOPE_CODES |
| **CONSERVAR** | Scopes actuales (sin economía) |
| **ADAPTAR** | PDF partner = vista sin costos/margen |
| **RETIRAR** | Scope `negocio.economy` para partners |
| **RIESGO** | Exposición margen a consultor externo |

### P-04 — RBAC duplicado frontend/backend

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Convergencia múltiple en `permissions.ts` / `permissions.py` |
| **COMPONENTES** | `main.py`, menú, App.tsx — hotspot merge |
| **AUTORIDAD** | `permissions.py` |
| **CONSERVAR** | Ambos con sincronización |
| **ADAPTAR** | GENERAL merge con lista única permisos nuevos |
| **RETIRAR** | Permisos solo en frontend |
| **RIESGO** | UI muestra acción que API rechaza (o peor: inverso) |

---

## Permisos transversales nuevos (Seguridad `c433bac`)

Integrar en merge sin duplicar:

- `empresa.seguridad.read` / `empresa.seguridad.admin`
- `gobierno.operacional.read` / `gobierno.operacional.admin`
- Mantener `governance.*` (1350) como catálogo datos personales

---

## Verificación GENERAL

1. Test adversarial: usuario partner sin grant → 403
2. Test: grant revocado → 403 inmediato
3. Test: grant activo pero objeto INTERNO_EIAAX → 403
4. Test: tenant A token en org B → 403
5. Auditoría: `PartnerAuditEvent` + `write_audit` en accesos sensibles
