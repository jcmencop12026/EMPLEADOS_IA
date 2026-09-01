# 08 — RBAC y multiempresa

## Permiso principal

`control_center.view` — acceso al Centro de Control.

## Permisos por bloque

| Bloque | Permiso |
|--------|---------|
| FinOps / costo | `finops.view` |
| LLM proveedores | `llm.view` |
| Empleados | `employee.view` |
| Operaciones | `operations.view` |
| Conocimiento | `knowledge.view` |
| Vista plataforma cross-org | `platform.organization.view` |

## Multiempresa

`resolve_organization_id` valida tenant. Prueba `test_caso6_multitenant_operacional`: tenant B no ve empleados de A.

Backend autoridad — manipulación API incluida en tests.
