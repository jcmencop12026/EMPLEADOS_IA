# 06 — RBAC y multiempresa

## Permisos nuevos

| Código | Rol típico |
|--------|------------|
| `strategic_control.view` | admin, superadmin |
| `strategic_control.economia_privada` | admin, superadmin |

## Ruta frontend

- `/centro-estrategico` → `RequirePermission strategic_control.view`
- Menú: "Centro estratégico" (junto a Centro de Control operacional)

## Multiempresa

- `resolve_organization_id` delegado a `control_center_service`
- SuperAdmin puede pasar `organization_id` query param
- `test_multitenant_aislamiento` verifica org distinta por tenant

## Denegación

- Sin `strategic_control.view` → 403
- Lecturas respetan permisos de dominio (oportunidades, finops, continuidad, etc.)
