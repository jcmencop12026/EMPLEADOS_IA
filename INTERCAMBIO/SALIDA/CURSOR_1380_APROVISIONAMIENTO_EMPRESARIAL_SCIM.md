# EMPLEADOS_IA — BLOQUE 1380
## Aprovisionamiento empresarial SCIM 2.0

**Rama:** `cursor/1380-aprovisionamiento-scim`  
**Base:** `cursor/1370-identidad-empresarial-sso` @ `3c545f64fe06569ecadbfa8523d65af798d472e3`  
**Justificación base:** Extiende 1370 (SSO, identidad, mapeos, sesiones) sin reemplazarlo ni crear mecanismos paralelos incompatibles.

---

## Objetivo cumplido

Implementación SCIM 2.0 (RFC 7643/7644) para aprovisionamiento y desaprovisionamiento automatizado de usuarios y grupos por organización, con tokens Bearer, ciclo de vida, mapeo grupos→roles por allowlist, protección SUPERADMIN, auditoría, métricas y UI administrativa en español.

---

## Arquitectura

```
IdP externo (push SCIM estándar)
        │ Bearer token por organización
        ▼
/scim/v2/*  (router scim.py)
        │ authenticate_scim_token + rate limit
        ▼
scim_user_service / scim_group_service
        │ integra User + ScimUserResource
        ▼
1370: sesiones, MFA, auth_method, políticas org
```

### Modelos (`scim_models.py`)
- `ScimToken` — hash SHA-256, prefijo enmascarado, expiración/revocación
- `ScimUserResource` — vínculo SCIM ↔ `User` interno
- `ScimGroup`, `ScimGroupMember`
- `ScimGroupRoleMapping` — allowlist grupo externo → rol interno
- `ScimAuditLog`, `ScimConflict`, `ScimIdempotencyRecord`, `ScimMetrics`

### Servicios
- `scim_auth_service` — tokens, autenticación, rate limit (memoria, P2)
- `scim_user_service` — CRUD/PATCH, desaprovisionamiento, idempotencia
- `scim_group_service` — grupos, membresías, mapeo roles
- `scim_filter` — filtros `eq` (userName, externalId, active, displayName)
- `scim_patch` — add/replace/remove con campos protegidos
- `scim_audit` — auditoría y métricas por organización

---

## Endpoints SCIM (`/scim/v2`)

| Recurso | Métodos |
|---------|---------|
| `/Users` | GET (list+filter), POST, GET/{id}, PUT/{id}, PATCH/{id}, DELETE/{id} |
| `/Groups` | GET, POST, GET/{id}, PUT/{id}, PATCH/{id}, DELETE/{id} |
| `/ServiceProviderConfig` | GET |
| `/ResourceTypes` | GET |
| `/Schemas` | GET |

### API administración (`/api/identidad/scim`)
- `GET /estado` — URL base, métricas, tokens, conflictos, eventos
- `PUT /configuracion` — activar/desactivar SCIM
- `POST /tokens`, `POST /tokens/{id}/rotar`, `POST /tokens/{id}/revocar`
- `GET|POST /mapeos-roles`
- `GET /conflictos`

---

## Seguridad

- **Tenant isolation:** todas las consultas filtran por `organization_id` del token
- **Tokens:** nunca en texto plano en BD; solo hash SHA-256; token completo solo al crear/rotar
- **Roles:** allowlist `ScimGroupRoleMapping`; prohibidos `superadmin`, `platform_admin`, `admin`
- **SUPERADMIN:** cuentas protegidas no modificables vía SCIM (403)
- **Desaprovisionamiento:** `active=false` → sesiones revocadas (`revoke_all_user_sessions`), sin borrado destructivo
- **Idempotencia:** cabecera `X-Idempotency-Key`
- **Rate limiting:** 120 req/min por org+token (memoria compartida en proceso — P2 persistente)
- **Errores SCIM:** formato RFC, sin filtrar tokens ni trazas internas

---

## Ciclo de vida

| Estado | Descripción |
|--------|-------------|
| PROVISIONADO | Alta inicial |
| ACTIVO | Usuario operativo |
| SUSPENDIDO | Reservado |
| DESACTIVADO | Desaprovisionado (`active=false`) |

---

## Multiempresa

Cada organización tiene configuración SCIM, tokens, usuarios SCIM, grupos y mapeos independientes. Pruebas explícitas de aislamiento cross-tenant (404 al acceder recurso de otra org).

---

## Migración

- **Revisión:** `1380a1b2c3d4e`
- **Down:** `1370a1b2c3d4e`
- Tablas SCIM + columna `scim_enabled` en `organization_identity_settings`
- Cabeza Alembic única verificada

---

## Pruebas

```
tests/test_scim_1380.py — 22 passed
tests/test_identidad_1370.py — 15 passed
tests/test_bloque_1300_seguridad_avanzada.py — 20 passed
tests/test_migration_control.py — 7 passed
Total focal — 64 passed
npm run build — PASS
```

Cobertura: discovery, usuarios, PATCH, filtros, paginación, grupos/membresías, tokens (válido/inválido/revocado/expirado), rotación, multiempresa, idempotencia, allowlist roles, SUPERADMIN, auditoría, rate limit 429, migración.

---

## Observabilidad

Métricas por org en `ScimMetrics`: usuarios provisionados/activos/desactivados, solicitudes, 429, conflictos, tokens activos/expirados, última sincronización. Expuestas en `/api/identidad/scim/estado` para integración futura al Centro de Control.

---

## UI (español)

**Administración → Identidad empresarial → Aprovisionamiento SCIM**

- Activar/desactivar SCIM
- URL base, generar/rotar/revocar token
- Métricas y última actividad
- Mapeo grupos → roles
- Conflictos y eventos recientes
- Ayuda contextual breve

---

## Riesgos y clasificación

| ID | Nivel | Descripción |
|----|-------|-------------|
| P0 | 0 | Sin hallazgos bloqueantes en pruebas focales |
| P1 | 0 | — |
| P2 | 1 | Rate limit en memoria (no compartido entre réplicas); documentado para Redis futuro |

---

## Preparado para futuro

- Reconciliación pull (no implementada; arquitectura compatible)
- Conectores propietarios Entra/Okta/Google (no requeridos; compatibilidad vía SCIM estándar)
- Rate limit persistente/compartido
- Sincronización bidireccional avanzada

---

## Veredicto

**APTO** — SCIM 2.0 empresarial integrado con 1370, sin modificar V1. NO MERGE (borrador).
