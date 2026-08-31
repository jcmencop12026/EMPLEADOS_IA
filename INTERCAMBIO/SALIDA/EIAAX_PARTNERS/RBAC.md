# RBAC — Partners MB-03

## Permisos plataforma

| Código | Descripción |
|--------|-------------|
| `partners.view` | Consultar partners |
| `partners.manage` | Crear, editar, activar/desactivar |
| `partners.org.grant` | Asociar organizaciones |
| `partners.user.assign` | Asignar usuarios al partner |
| `partners.audit` | Consultar auditoría (reservado extensión) |

Asignados a roles `admin` y `superadmin` vía `ROLE_PERMISSIONS_FALLBACK` y bootstrap.

## Roles usuario partner

Definidos en `PARTNER_USER_ROLES`:

- **ADMIN** — puede conceder orgs y asignar usuarios del partner (sin permisos plataforma)
- **OPERADOR** — opera sobre organizaciones con grant activo
- **LECTOR** — lectura según alcance concedido

## Matriz de decisión API

| Acción | partners.manage | partners.org.grant | Membresía ADMIN | Membresía OPERADOR |
|--------|-----------------|--------------------|-----------------|--------------------|
| Crear partner | ✓ | — | — | — |
| Ver detalle | ✓ | — | ✓ | ✓ |
| Conceder org | ✓ | ✓ | ✓ | — |
| Contexto org | ✓ (sin membresía) | — | ✓ + grant | ✓ + grant |

## Frontend

Rutas protegidas con `partners.view`. Acciones de gestión condicionadas a `partners.manage`, `partners.org.grant`, `partners.user.assign`.
