# 09 — Operación y medición

## Vista operacional (reutilizada)

`EmployeeDetailPage.tsx` + endpoints existentes:

| Necesidad | Endpoint / vista |
|-----------|------------------|
| Estado activo | `lifecycle_status`, `/health` |
| Última ejecución | métricas, test runs |
| Errores | `ERROR` status, health checks |
| Consumo | `/metrics`, FinOps |
| Aprobaciones pendientes | `/approvals` |
| Acciones | pause, retire, rollback |

**No** se construyó segundo Centro de Control.

## Indicadores preparados

Relación con `EmployeeMetric` y FinOps:

- Volumen procesado
- Tiempo / latencia
- Calidad (certificación score)
- Errores (test runs FAILED)
- Costo (FinOps)
- Cumplimiento (auditoría)

## Frontera Inteligencia de Resultados (agente D)

| Concepto | Estado |
|----------|--------|
| ANTES | Manual / baseline en dossier |
| PROYECTADO | estimate-capacity |
| REAL | FinOps + inference logs |

Integración futura: exponer `employee_id` + métricas vía contrato REST existente.

## Asignación

Campos preparados: `organization_id`, specialty, proceso vía metadata.

No organigrama RRHH completo.
