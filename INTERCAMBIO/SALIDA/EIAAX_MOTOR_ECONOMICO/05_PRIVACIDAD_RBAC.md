# 05 — Privacidad y RBAC multiempresa

## Vista Entidad (por defecto)

`entity_view_summary()` expone:

- Costos por clase/naturaleza agregados
- Valores con separación POTENCIAL
- ROI FinOps consolidado
- `economia_privada_incluida: false`

Margen, precio sugerido operador, ROI privado y notas internas **no** aparecen.

## Economía privada

Requiere `finops.economy.private` (asignado a `superadmin` vía `FINOPS_PERMISSIONS`; `viewer` no tiene acceso).

Campos: costo estimado/real, tiempo, recursos, IA, infra, servicios, soporte, valor cliente, precio sugerido, margen, ROI, payback, riesgo comercial.

## Multiempresa

- `resolve_organization_id()` heredado de Centro de Control (mismo patrón C2)
- Todas las tablas `economic_*` con `organization_id` + FK
- Query param `organization_id` solo cross-org con permisos plataforma

## Protección márgenes

Costos/márgenes privados en tabla separada; endpoint dedicado con permiso dedicado; adapter CC con `economia_privada_expuesta: false`.
