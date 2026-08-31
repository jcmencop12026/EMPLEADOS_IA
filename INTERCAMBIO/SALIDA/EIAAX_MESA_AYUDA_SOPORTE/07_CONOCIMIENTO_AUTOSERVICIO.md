# 07 — Conocimiento y autoservicio

## Autoservicio
`POST /api/soporte/autoservicio` — flujo «¿Qué necesitas?»

Antes de crear caso:
1. Busca en Knowledge (`search_documents`)
2. Sugiere casos abiertos similares (misma org, RBAC)
3. Calcula prioridad sugerida por impacto/urgencia

UI: botón «¿Qué necesitas?» en Mesa de Ayuda → crear caso reutilizando texto ya ingresado.

## Propuesta de conocimiento
`POST /api/soporte/conocimiento/proponer`

- Estado `PENDIENTE` — **no publica** automáticamente
- Requiere revisión/aprobación vía Knowledge existente (P1)
- Tipos: `ARTICULO`, `PROCEDIMIENTO`, `SOLUCION`, `FAQ`

Vinculable a `case_id` o `problem_id`.
