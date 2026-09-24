# 07 — Impacto e indicadores

## Modelo

Tabla `evaluaciones_indicadores`:

- `valor_antes`, `valor_proyectado`, `valor_real`
- `unidad`, `fuente` (`MANUAL` | preparado para `PIIAX`)
- Vinculación opcional a `hallazgo_id`
- `visible_entidad` para vista filtrada

## API

- `GET /api/evaluaciones/{id}/indicadores`
- `POST /api/evaluaciones/{id}/indicadores` — permiso `evaluacion.indicadores.manage`

## Visualización

`get_impacto_resumen()` en `evaluacion_service.py`:

- Separa inequívocamente **proyección** vs **realizado**
- Genera `grafico_puntos` cuando hay ≥2 valores numéricos comparables
- Frontend: `ImpactoGrafico.tsx` — barras ANTES / PROYECTADO / REAL

## Preparación PIIAX

Campo `fuente` permite ingestión futura de métricas reales desde PIIAX sin cambiar el modelo de presentación.
