# 03 — Tipos de analítica

## Separación semántica

| Tipo | Uso |
|------|-----|
| DESCRIPTIVA | Qué pasó (valor ANTES, hechos registrados) |
| DIAGNOSTICA | Por qué (causas en plan de acción / hallazgos) |
| COMPARATIVA | Cambio vs línea base o periodo |
| PREDICTIVA | Proyección — marcada como inferencia en capa APR |
| PRESCRIPTIVA | Recomendación — no presentada como hecho |

## Capa `build_antes_proyectado_real`

Devuelve por indicador:

- `proyectado_es_inferencia` cuando `tipo_analitica` ∈ {PREDICTIVA, PRESCRIPTIVA, DIAGNOSTICA}
- `sin_medicion_posterior` cuando hay PROYECTADO sin REAL

## Drill-down

Árbol `resultados_dimension_nodos` con `parent_id` y `nivel` — no hardcodeado a salud; demo usa pagador → causal.

## Filtros API

`expediente_id`, `periodo`, `proceso`, `tipo_analitica`, `q`, `solo_con_real`
