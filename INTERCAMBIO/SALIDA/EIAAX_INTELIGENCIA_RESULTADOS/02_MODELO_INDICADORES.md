# 02 — Modelo de indicadores

## Tabla `resultados_indicadores`

| Campo | Descripción |
|-------|-------------|
| `nombre`, `definicion`, `unidad`, `fuente` | Identidad y definición |
| `dimension_json` | Dimensiones sector-agnósticas (JSON) |
| `periodo`, `proceso` | Contexto temporal y de proceso |
| `valor_antes`, `valor_proyectado`, `valor_real`, `meta` | Capa ANTES / PROYECTADO / REAL |
| `fecha_medicion`, `evidencia_ref`, `confianza`, `calidad` | Medición y calidad |
| `tipo_analitica` | DESCRIPTIVA, DIAGNOSTICA, COMPARATIVA, PREDICTIVA, PRESCRIPTIVA |
| `responsable_id`, `correlation_id` | Responsable y trazabilidad |
| `expediente_id`, `hallazgo_id`, `opportunity_id`, `linea_base_id` | Vínculos |
| `visible_entidad` | Visibilidad BP1 |

## Tablas relacionadas

- `resultados_dimension_nodos` — drill-down genérico (pagador → causal → …)
- `resultados_evidencias` — evidencia vinculada a indicador o informe
- `resultados_informes` — informes versionables
- `resultados_plan_acciones` — plan de mejoramiento

## API principal

- `GET/POST /api/resultados/indicadores`
- `POST /api/resultados/indicadores/sync-linea-base/{id}`
- `POST /api/resultados/indicadores/{id}/medicion-real`
- `GET /api/resultados/indicadores/{id}/drill-down`
