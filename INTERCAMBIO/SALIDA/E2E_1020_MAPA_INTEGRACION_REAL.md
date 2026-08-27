# E2E-1020 — Mapa de integración real

**Fecha:** 2026-08-27
**Rama:** `cursor/e2e-integral-1020-12b6`
**Base:** `main` @ `cc77d83` (incluye PR #22 ORQUESTADOR-EXPERIENCIA-1010)

## Leyenda de estados

| Estado | Significado |
|--------|-------------|
| CONECTADO | Datos fluyen entre etapas con persistencia verificable |
| PARCIALMENTE CONECTADO | Existe enlace pero con gaps documentados |
| AISLADO | Módulo existe sin enlace al flujo principal |
| SIMULADO | Respuesta fixture/mock, no pipeline real |
| FALTANTE | No implementado |

## Matriz de integración

| ETAPA | COMPONENTE | ENDPOINT/SERVICIO | ENTRADA | SALIDA | PERSISTENCIA | SIGUIENTE ETAPA | ESTADO |
|-------|-----------|-------------------|---------|--------|--------------|-----------------|--------|
| Solicitud | SALUD engine | `POST /api/salud/analisis` | `request_text`, datasets | `IpsAnalysis.id` | `ips_analyses` | Orquestador + Motor | CONECTADO |
| Orquestación | ORQUESTADOR-1010 | `select_team` vía `select_specialists` | solicitud, datos | equipo, factores, log | `experience_selection_logs` | Motor + hallazgos | CONECTADO |
| Conocimiento | Centro Conocimiento | `collect_analysis_knowledge` | grants, dominio | fuentes, fragmentos | audit + summary | Hallazgos | PARCIALMENTE CONECTADO |
| Análisis | MOTOR-1000 | `run_motor_analitico` | indicadores, solicitud | hipótesis, priorización | `summary_json.motor` | Recomendación | CONECTADO |
| Recomendación | Motor + propuestas | `get_diagnostico` | analysis_id | `recomendacion_consolidada` | `ips_propuestas` | Plan acción | CONECTADO |
| Aprobación humana | Coordinator | `POST /api/assistant/ask` | RIPS/docint | `WAITING_APPROVAL` | `approval_requests` | Ejecución | CONECTADO (coordinator) |
| Aprobación SALUD | — | plan-accion | propuestas | WorkPlan READY | `work_plans` | Operaciones | PARCIALMENTE CONECTADO |
| WorkPlan | SALUD bridge | `POST .../plan-accion` | propuesta_ids | work_plan_id | `work_plans`, `ips_action_plans` | Operaciones | CONECTADO |
| Operaciones | Operations Center | `/api/operations/center/*` | work_plan_id | tareas, estados | `employee_tasks` | Ejecución | CONECTADO |
| Automatizaciones | Scheduler | `automation_scheduler._tick` | cron/trigger | runs | `automation_runs` | Notificaciones | PARCIALMENTE CONECTADO |
| Notificaciones | Event bus | `notifications._event_subscriber` | eventos | IN_APP | `notifications` | Humano | CONECTADO |
| FINOPS | finops_bridge | `register_finops_values` | motor finops | valores | `finops_values` | Dashboard | PARCIALMENTE CONECTADO |
| Resultado real | SALUD resultado | `POST .../propuestas/{id}/resultado` | KPI, outcome | IpsActionResult | `ips_action_results` | Experiencia core | CONECTADO (1020) |
| Experiencia IPS | salud_experience | `save_experience_case` | análisis | IpsExperienceCase | `ips_experience_cases` | Casos similares IPS | PARCIALMENTE CONECTADO |
| Experiencia core | experience_core | `EmployeeExperienceRecord` | resultado real | peso, similitud | `employee_experience_records` | Orquestador | CONECTADO (1020) |
| Aprendizaje | Orquestador | `select_team` 2ª vez | experiencia actualizada | ranking/score | logs + records | Nueva decisión | CONECTADO |

## Gaps identificados

| ID | Gap | Severidad | Acción 1020 |
|----|-----|-----------|-------------|
| G-01 | Coordinator no invoca `run_ips_analysis` para ips-analitica | Media | Documentado; flujo E2E usa SALUD directo |
| G-02 | FINOPS valor sin `work_plan_id` | Baja | Documentado; trazabilidad vía `source=motor_analitico:{id}` |
| G-03 | Doble store experiencia (IPS vs core) | Media | **Corregido:** puente `sync_action_result_to_core_experience` |
| G-04 | Conocimiento requiere solicitud con keywords de dominio | Baja | Documentado en E2E |
| G-05 | E2E GUI no ejecutado en Cloud Agent | Info | PENDIENTE VALIDACIÓN LOCAL |

## Cadena de IDs (trazabilidad)

```
IpsAnalysis.id
  → ExperienceSelectionLog.id (selection_log_id)
  → IpsHallazgo.id / IpsPropuesta.id
  → IpsActionPlan.id
  → WorkPlan.id + correlation_id
  → EmployeeTask.inputs_json.analysis_id
  → FinOpsValueRecord.source = motor_analitico:{analysis_id}
  → EmployeeExperienceRecord.caso_origen_id = analysis.id
```

## Clasificación E2E

| Tipo | Cobertura 1020 |
|------|----------------|
| E2E BACKEND REAL | 13 tests `test_e2e_integral_1020.py` — PASS |
| E2E API REAL | Flujo completo vía HTTP TestClient |
| E2E GUI REAL | NO PROBADO — pendiente validación local |
| SIMULADO | Ninguno en suite 1020 |
