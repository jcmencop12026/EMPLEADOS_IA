# 06 — Plan de mejoramiento

## Cadena

`hallazgo` → `causa` → `accion` → `responsable` → `fecha_meta` → `indicador` → seguimiento → evidencia → resultado → estado

## Tabla `resultados_plan_acciones`

Estados: PENDIENTE, EN_CURSO, COMPLETADA, CANCELADA

## API

- `GET/POST /api/resultados/plan-acciones`
- `PATCH /api/resultados/plan-acciones/{id}`

## Reutilización

No sustituye tareas de orquestación/work plans; complementa el expediente de evaluación con seguimiento de impacto.
