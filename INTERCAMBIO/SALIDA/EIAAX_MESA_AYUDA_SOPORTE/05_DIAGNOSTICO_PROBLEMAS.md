# 05 — Diagnóstico y problemas recurrentes

## Diagnóstico (campos separados en caso)
- `sintoma` — observación reportada
- `hipotesis` — no se presenta como causa confirmada
- `causa_probable` — análisis en curso
- `causa_validada` — causa confirmada

API: `PATCH /api/soporte/casos/{id}/diagnostico`

Historial acción `DIAGNOSTICO`.

Análisis IA: usar gateway LLM existente (P2 — sin acoplar OpenAI directo en soporte).

## Problemas recurrentes
`SupportProblem` agrupa incidentes relacionados.

- `POST /api/soporte/problemas` — crear desde lista de `case_ids`
- `GET /api/soporte/problemas` — listar
- `PATCH /api/soporte/problemas/{id}` — causa raíz, soluciones, acciones preventivas

Campos: `causa_raiz`, `solucion_temporal`, `solucion_definitiva`, `acciones_preventivas`.

## Revisión posterior
`PUT /api/soporte/casos/{id}/revision-posterior` — qué ocurrió, impacto, causa, acciones, lecciones (sin buscar culpables).
