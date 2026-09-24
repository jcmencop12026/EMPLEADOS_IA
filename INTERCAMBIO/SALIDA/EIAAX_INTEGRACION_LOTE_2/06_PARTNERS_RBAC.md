# 06 — Partners y RBAC

## Modelo MB-03

| Entidad | Propósito |
|---------|-----------|
| `Partner` | Aliado comercial |
| `PartnerOrganizationGrant` | Acceso explícito a organización |
| `PartnerUserMembership` | Usuario asociado al partner |
| `PartnerAuditEvent` | Auditoría de operaciones |

## RBAC

| Permiso | Uso |
|---------|-----|
| `partners.view` | Listar / consultar |
| `partners.manage` | CRUD partners |
| `partners.org.grant` | Grants a organizaciones |
| `partners.user.assign` | Asignar usuarios |
| `partners.audit` | Auditoría |

Roles: admin (completo), operator (view), superadmin (plataforma).

## Aislamiento verificado (tests)

- Partner A no accede a org de Partner B
- Sin grant → acceso denegado
- Revocación efectiva en backend
- Manipulación API con partner_id incorrecto → rechazado
- RBAC sin `partners.manage` → 403

## UI

- `/partners` — listado MB-03
- `/partners/:partnerId` — detalle, grants, usuarios, auditoría
- **Distinto** de `/administracion/proveedores-ia` (Multiproveedor IA / catálogo LLM)

## API

- Prefijo `/api/partners`
- CRUD, estado, grants, revocación, alcance, usuarios, auditoría, catálogo meta

## Migración

- `1412a1b2c3d4e_partners_mb03.py`
