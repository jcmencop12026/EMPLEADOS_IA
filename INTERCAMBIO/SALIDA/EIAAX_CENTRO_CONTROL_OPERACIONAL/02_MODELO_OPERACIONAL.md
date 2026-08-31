# 02 — Modelo operacional canónico

## Principio

**No hay tabla monolítica.** Capa de lectura `operational_control_service.py` orquesta dominios canónicos por referencia.

```
organización → empleado IA → ejecución (WorkPlan) → capacidad → proveedor/modelo
→ consumo (FinOps) → estado → aprobación → resultado → incidencia
```

## Fuentes de verdad

| Concepto | Fuente |
|----------|--------|
| Empleado IA | `AIEmployee` |
| Ejecución | `WorkPlan`, `EmployeeTask` |
| Consumo | `FinOpsRecord`, `LlmInferenceLog` |
| Capacidad | `consumption_planner_service` |
| Aprobación | `ApprovalRequest`, `EmployeeFactoryApproval` |
| Capacidad empresarial | `EmployeeBusinessCapability` |
| Proveedor | `LlmProviderConfig` |

## APIs

| Endpoint | Rol |
|----------|-----|
| `GET /api/centro-control/resumen-ejecutivo` | Agregado completo + bloque `operacional` |
| `GET /api/centro-control/operacional` | Vista operacional dedicada |
| `GET /api/centro-control/ejecuciones/{id}/detalle-operacional` | Drill-down ejecución |

Estados no se duplican — se leen de dominios origen.
