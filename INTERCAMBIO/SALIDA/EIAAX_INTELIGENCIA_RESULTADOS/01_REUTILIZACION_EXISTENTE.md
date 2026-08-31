# 01 — Reutilización existente

## Auditoría previa

| Capacidad existente | Uso en 1410 |
|---------------------|-------------|
| Bloque 1200 `baseline_service` | Puente `sync_indicador_from_linea_base` — ANTES/impacto esperado sin duplicar motor |
| Bloque 1405 `evaluacion_service` | Expedientes, hallazgos; `get_impacto_resumen` consume indicadores de resultados |
| Bloque 1210 valoración | No duplicado — interfaces económicas reservadas para integración con rama B |
| Centro de oportunidades 1100 | Vinculación `opportunity_id` en indicadores |
| Aprendizaje / optimización | No reimplementados — trazabilidad vía `correlation_id` |
| Reporting documental | Informe narrativo determinístico propio, no diseñador BI |
| Compliance / auditoría | `write_audit` en evaluación; evidencias en `resultados_evidencias` |
| Experiencia transversal (`7f2e3ce`) | `EiaaxTable`, `ContextualHelp`, tokens, tema, `AppShell` |

## No construido (por diseño)

- Motor Económico (rama B)
- Gobierno operacional transversal (rama A)
- BI genérico / diseñador de reportes infinito
- Segundo gestor de tareas — plan de mejoramiento ligero sobre acciones existentes

## Integración evaluación ↔ resultados

La pestaña **Impacto e Indicadores** del expediente lee indicadores persistidos en `resultados_indicadores` cuando existen; mantiene compatibilidad con hallazgos textuales legacy.
