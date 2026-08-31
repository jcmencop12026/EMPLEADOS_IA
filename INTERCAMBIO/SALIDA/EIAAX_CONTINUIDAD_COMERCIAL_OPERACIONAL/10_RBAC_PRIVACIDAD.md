# 10 — RBAC, multiempresa y economía privada

## Permisos nuevos

| Permiso | Descripción |
|---------|-------------|
| `continuidad_comercial.view` | Ver vista continuidad |
| `continuidad_comercial.manage` | Gestionar cambios de alcance |
| `continuidad_comercial.close` | Cerrar contratos |

Asignados a roles admin/comercial vía `permissions.py` seed.

## Multiempresa

Tests `test_multiempresa_aislamiento`:

- Tenant B no accede contrato, implementación, entregables, cambios, economía de Tenant A
- Manipulación directa API con tokens cruzados → 403/404

## Economía privada

`vista_continuidad` filtra datos privados salvo permisos:

- `negocio.economy.private`
- `finops.economy.private`

Test `test_privacidad_economia_no_en_vista_cliente` verifica ausencia de costos internos/margen en vista estándar.

## Aprobaciones

`ApprovalPort` preservado; `LocalNegocioApprovalAdapter` sin profundizar (convergencia GENERAL → Gobierno Operacional).
