# 04 — Capacidad y consumo

## Capacidad (MB-07 reutilizado)

Bloque `capacidad`:

- CAPACIDAD UTILIZADA = ejecuciones RUNNING/PLANNING/PARTIAL
- COLA = planes CREATED/READY/PLANNING
- CONCURRENCIA = ejecuciones activas
- SATURACIÓN = NORMAL / ELEVADA / SATURADA (según riesgo planificador + carga)
- PROYECCIÓN = `centro_control_contract`

**No** deriva capacidad solo del número de empleados.

## Costo operacional (FinOps reutilizado)

Bloque `costo`:

| Tipo | Fuente |
|------|--------|
| REAL | `finops_service.dashboard_summary` |
| ESTIMADO | `consumption_planner_service.centro_control_contract` |

Clasificación: DIRECTO, TRANSVERSAL_ATRIBUIBLE, PLATAFORMA.

Economía privada restringida por `finops.view` — sin segundo motor.

## Dimensionamiento

Bloque `dimensionamiento`: volumen 30d, duración, concurrencia. Distingue productividad liberable vs reducción personal verificada (null sin evidencia).
