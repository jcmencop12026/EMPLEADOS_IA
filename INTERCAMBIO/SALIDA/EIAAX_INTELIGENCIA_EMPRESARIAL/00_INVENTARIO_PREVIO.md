# 00 — Inventario previo (auditoría)

## COMPLETO (reutilizar)

| Dominio | Servicio/Router | Estado |
|---------|-----------------|--------|
| Evaluación adaptativa BP1 | `evaluacion_service`, `/api/evaluaciones` | Catálogo por nivel PRELIMINAR/DIAGNOSTICA/PROFUNDA |
| Suficiencia base | `transformacion_service.evaluar_suficiencia` | Completitud + faltantes |
| Arquitecto transformación | `transformacion_service`, `/api/transformacion` | Dossier, mapa, causas, alternativas, iniciativas |
| Diagnóstico 1220 | `diagnostic_service`, `/api/diagnosticos` | Cadena trace completa |
| Motor oportunidades 1030 | `proactive_service`, `/api/oportunidades` | Pertinencia, priorización, pipeline |
| Inteligencia externa 1240 | `external_intelligence_service` | Fuentes autorizadas, trazabilidad |
| Conocimiento 930 | `knowledge_retrieval` | Recuperación documental |

## PARCIAL (extendido en este macrobloque)

| Brecha | Acción |
|--------|--------|
| Suficiencia fragmentada (4 implementaciones) | `inteligencia_empresarial/suficiencia.py` unificado |
| Sin cadena analítica unificada evaluación | `cadena_analitica.py` |
| Evaluador único preliminar | `evaluacion_adaptativa.py` por nivel |
| Escenarios solo ACTUAL/MEJORADO/TRANSFORMADO | 5 escenarios: ACTUAL, OPTIMIZADO, AUTOMATIZADO, ASISTIDO_IA, ALTAMENTE_AUTOMATIZADO |
| Sin taxonomía HACER/ESTUDIAR | `priorizacion.py` sobre motor 1030 |
| Sin API orquestación | `/api/inteligencia-empresarial/*` |

## NO DUPLICADO

- Sin nuevo expediente/dossier/opportunity models
- Sin motor económico (contrato Agente B)
- Sin scraping externo
- Sin decisiones automáticas empresariales
