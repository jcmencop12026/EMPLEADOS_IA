# 13 — Brechas restantes (P0/P1/P2)

## P0 — Ninguna bloqueante para entrega MB-12
Capacidad transversal operativa con pruebas verdes.

## P1 — Integración posterior (GENERAL)
| Brecha | Notas |
|--------|-------|
| Reglas MB-11 por org | Plantillas seed listas; reglas activas requieren configuración en Centro Información |
| Autocierre post-validación | Scheduler existente; job de autocierre no cableado |
| Puente Knowledge aprobación | Propuestas `PENDIENTE`; flujo revisión en Knowledge |
| Puente continuidad 1360 | `cont_incidentes` ↔ `support_cases` |
| `support.manage` alias | Usar `support.update` + `support.admin` |
| Horario laboral en SLA | Campo `horario_servicio_json` sin cálculo activo |

## P2 — Evolución
| Brecha | Notas |
|--------|-------|
| Asignación Empleado IA | Referencias preparadas |
| Satisfacción formal (CSAT) | Sin encuesta; validación solicitante como proxy |
| Dashboard Resultados embebido | Indicadores vía API; widget dedicado pendiente |
| Análisis IA en diagnóstico | Gateway LLM existente, no integrado en UI soporte |
| Reconciliación migraciones 1410/1420 | Responsabilidad GENERAL en convergencia |

## Migraciones
- Nueva: `1430a1b2c3d4e` (depende `1420a1b2c3d4e`)
- `tests/conftest.py`: import `support_models` para SQLite create_all
