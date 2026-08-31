# 05 — Motor económico y FinOps

## Capa canónica

`economic_motor_service` es la implementación real; BP2 consume vía `evaluacion_integracion_finops.py`.

## Reutilización

- `finops_service` — costos y consumo
- `consumption_planner_service` — planificación MB-07
- Valoración económica 1210 — indicadores de valor

## Clasificaciones preservadas

### Ámbito
- DIRECTO
- TRANSVERSAL_ATRIBUIBLE
- PLATAFORMA

### Naturaleza temporal
- ESTIMADO
- REAL

### Estado de valor (vista entidad)
- VERIFICADO
- ESTIMADO
- POTENCIAL — **nunca promovido silenciosamente a realizado**

## Integración BP2

```python
# evaluacion_integracion_finops.py
obtener_indicadores_economicos() → economic_motor_service.sum_values_by_nature / sum_costs_by_class_and_kind
enriquecer_impacto_desde_finops() → entity_view_summary (sin economía privada)
```

## Economía privada

- Permiso: `finops.economy.private.view`
- No expuesta en Vista Entidad, BP2 integración, Partners ni APIs públicas no autorizadas
- Tests de motor económico verifican separación

## Centro de control

- `MotorEconomicoAdapter` registrado en `control_center_adapters.py`

## API

- Prefijo `/api/motor-economico`
- Endpoints de resumen, valores por naturaleza, costos, vista entidad segura

## Migración

- `1600a1b2c3d4e_motor_economico_eiaax.py` — tablas y enums del motor
