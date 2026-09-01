# 07 — Modelos, costo y capacidad

## Integración FinOps (reutilizada)

Endpoint: `GET /api/agent-factory/employees/{id}/estimate-capacity`

Delega en `consumption_planner_service.employee_cost_detail` cuando hay base suficiente.

Respuesta incluye:

- Frecuencia estimada
- Modelo preferido (de `EmployeeModelPolicy`)
- Límites de costo (`EmployeeLimits`)
- Bloque `finops` con estimación o advertencia
- `confianza`: MEDIA / BAJA según datos disponibles

## Dimensionamiento

Sin afirmar "sustituye X personas" sin datos.

Métricas preparadas vía:

- `EmployeeLimits` (concurrencia, timeout, costo)
- `EmployeeMetric` / `/metrics`
- FinOps records históricos

Distinción conceptual documentada:

- **CAPACIDAD** — volumen/frecuencia procesable
- **PRODUCTIVIDAD LIBERABLE** — tiempo humano evitable
- **REDISTRIBUCIÓN POSIBLE** — reasignación de tareas

## Consumo proyectado vs real

| Tipo | Fuente |
|------|--------|
| PROYECTADO | `estimate-capacity`, Consumption Planner |
| REAL | FinOps records, LLM inference logs |
| ANTES | Baseline manual (frontera D — Inteligencia de Resultados) |

**No** se reconstruyó Motor Económico.
