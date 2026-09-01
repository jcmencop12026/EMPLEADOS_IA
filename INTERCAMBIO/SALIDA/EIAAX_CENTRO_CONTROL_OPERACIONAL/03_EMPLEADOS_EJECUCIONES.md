# 03 — Empleados IA y ejecuciones

## Fuerza laboral IA

Bloque `fuerza_laboral` distingue plantilla (`is_template`) de instancia operativa.

| Bucket | Fuente |
|--------|--------|
| Activos | `lifecycle_status=ACTIVE` |
| En prueba | `TESTING` |
| Pausados | `PAUSED` |
| Con error | `FAILED_TEST` |
| Pendientes aprobación | `EmployeeFactoryApproval` PENDING |

Por empleado: última actividad, ejecuciones activas, proveedor, capacidades declaradas, enlace a fábrica.

## Ejecuciones

Reutiliza `operations_center` con etiquetas españolas (`operations_labels`):

- Pendiente / En ejecución / Esperando aprobación / Fallido / Completado / Cancelado

No se marca "Completado" sin estado canónico en `WorkPlan`.

## Detalle ejecución

`detalle-operacional` incluye: empleado, objetivo, tiempos, correlation_id, consumo FinOps, fallo, acciones permitidas. **Sin prompts ni credenciales.**

## Integración Fábrica

Desde CC → `/empleados/{id}` → configuración, consumo, ejecuciones, incidencias. Sin duplicar wizard.
