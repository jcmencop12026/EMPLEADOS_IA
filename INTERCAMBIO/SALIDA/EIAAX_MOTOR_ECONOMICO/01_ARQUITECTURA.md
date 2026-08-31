# 01 — Arquitectura Motor Económico EIAAX

## Principio rector

**Un solo FinOps.** El Motor Económico es una **capa de unificación y gobierno** sobre:

- `finops_service` (consumo/valor 950/1110)
- `consumption_planner_service` (MB-07 presupuestos/capacidad)
- `valuation_service` (1210 naturalezas VERIFICADO/ESTIMADO/POTENCIAL)
- Adaptadores Centro de Control existentes

No introduce un segundo ledger de consumo ni reemplaza tablas `finops_*`.

## Componentes nuevos (Bloque 1600)

```
┌─────────────────────────────────────────────────────────┐
│  API /api/motor-economico                               │
│  router/motor_economico.py                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  economic_motor_service.py (facade)                     │
│  · register_cost / register_value                       │
│  · entity_view_summary (Vista Entidad)                  │
│  · build_indicators (ANTES/PROYECTADO/REAL)             │
│  · private economy + price recommend (borrador)         │
└─────┬──────────────┬──────────────┬─────────────────────┘
      │              │              │
      ▼              ▼              ▼
 finops_service   MB-07 planner   economic_* tables
 (finops_records) (simulate)      (capa unificada)
```

## Clasificaciones unificadas

| Dimensión | Valores |
|---|---|
| Clase costo | `DIRECTO`, `TRANSVERSAL_ATRIBUIBLE`, `PLATAFORMA` |
| Naturaleza importe | `ESTIMADO`, `REAL`, `PROYECTADO` |
| Naturaleza valor | `VERIFICADO`, `ESTIMADO`, `POTENCIAL` |
| Fuente costo | 12 tipos (IA, tokens, infra, integraciones, …) |
| Alcance | Empleado IA, agente transversal, evaluación, oportunidad, implementación, organización |

## Centro de Control

`MotorEconomicoAdapter` expone fases ANTES/PROYECTADO/REAL sin economía privada (`economia_privada_expuesta: false`).
