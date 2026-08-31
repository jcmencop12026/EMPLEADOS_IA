# Modelo de datos — Partners

## Partner

Tabla `partners` — ámbito plataforma (no tenant-scoped).

| Campo | Descripción |
|-------|-------------|
| codigo | Identificador único (PTR-NNNN) |
| nombre, razon_social | Identificación comercial |
| estado | BORRADOR, ACTIVO, INACTIVO, SUSPENDIDO |
| tipo_relacion | CONSULTOR, INTEGRADOR, etc. |
| contacto_* | Nombre, email, teléfono |
| valid_from / valid_until | Vigencia del partner |
| created_by, created_at | Trazabilidad |

## PartnerOrganizationGrant

Tabla `partner_organization_grants` — acceso explícito y revocable.

| Campo | Descripción |
|-------|-------------|
| partner_id + organization_id | Único (uq_partner_org_grant) |
| estado | ACTIVO, REVOCADO, SUSPENDIDO |
| alcance_json | Lista JSON de códigos de alcance |
| granted_by, revoked_by, revoked_at | Trazabilidad de concesión |

### Códigos de alcance

- `organizacion.read` — lectura básica de organización
- `cc.view` — resumen centro de control
- `trabajo.view` — mi trabajo
- `evaluacion.view` — evaluaciones EIAAX
- `oportunidades.view` — oportunidades

## PartnerUserMembership

Tabla `partner_user_memberships` — usuario ↔ partner.

| Rol | Capacidad |
|-----|-----------|
| ADMIN | Administrar partner (orgs, usuarios) si no tiene permisos plataforma |
| OPERADOR | Operar sobre orgs concedidas |
| LECTOR | Solo lectura |

## PartnerAuditEvent

Tabla `partner_audit_events` — acciones: `partner.create`, `partner.org.grant`, `partner.org.revoke`, `partner.user.assign`, etc.
