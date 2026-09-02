# 08 — Multiempresa y RBAC

## Aislamiento probado

Tests con tenant A y tenant B:

- Clasificaciones: org B no ve objetos de org A
- Visibilidad: filtrada por `organization_id`
- Auditoría: consulta scoped a organización del token
- Centro de Confianza: datos por organización

## Permisos nuevos

| Permiso | Rol admin | Rol operator | Rol viewer |
|---------|-----------|--------------|------------|
| `gobierno.clasificacion.view` | ✓ | ✓ | ✓ |
| `gobierno.clasificacion.assign` | ✓ | ✓ | ✗ |
| `gobierno.trazabilidad.view` | ✓ | ✓ | ✓ |
| `gobierno.evidencia.view` | ✓ | ✓ | ✓ |
| `gobierno.evidencia.link` | ✓ | ✓ | ✗ |
| `gobierno.auditoria.consulta` | ✓ | ✓ | ✓ |

## Backend autoridad

Todas las APIs validan `user.organization_id` — manipulación directa cross-tenant retorna vacío o 404.
