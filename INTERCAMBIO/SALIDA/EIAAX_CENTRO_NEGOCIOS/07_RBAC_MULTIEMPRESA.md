# 07 — RBAC y multiempresa

## Permisos nuevos

| Código | Descripción |
|--------|-------------|
| `negocio.view` | Consultar dashboard, pipeline, propuestas |
| `negocio.manage` | Crear desde expediente, enriquecer, negociar, IA |
| `negocio.economy.private` | Ver documento interno y economía privada |
| `negocio.proposal.approve` | Aprobar propuesta y decidir precio |
| `negocio.proposal.present` | Transición a `ENVIADA` |
| `negocio.contract` | Marcar `ACEPTADA` y convertir a implementación |

## Asignación por rol

- **admin / superadmin:** todos los permisos `negocio.*`
- **operator:** view, manage, approve, present (sin contract ni economy.private)
- **viewer:** sin acceso a centro de negocios

## Aislamiento

- Todas las tablas `negocio_*` incluyen `organization_id`
- Filtro por organización en cada consulta
- `resolve_organization_id` para multi-tenant

## Pruebas

- `test_centro_negocios_aislamiento_tenant` — tenant B no ve propuesta de A
- `test_centro_negocios_sin_permiso` — viewer recibe 403
