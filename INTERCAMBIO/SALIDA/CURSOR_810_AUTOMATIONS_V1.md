# CURSOR-810 — AUTOMATIZACIONES Y PROGRAMADOR DE TRABAJOS V1

## GIT

| Campo | Valor |
|-------|-------|
| HEAD INICIAL | `02a0e0f` |
| HEAD FINAL | _(ver commit tras push)_ |
| RAMA | `cursor/automations-scheduler-810` |
| PR | _(pendiente creación)_ |

## ENTREGABLES

| Área | Estado |
|------|--------|
| MODELS | `Automation`, `AutomationRun` con `occurrence_key` único |
| MIGRATION | `a810f1c2d3e4_automations_scheduler_810.py` |
| API | CRUD + activate/pause/disable/duplicate/run-now/runs |
| SCHEDULER | Thread backend 30s, recálculo al iniciar, missed SKIP |
| TRIGGERS | SCHEDULE, MANUAL, INTERNAL_EVENT (extensible) |
| RECURRENCE | ONE_TIME, DAILY, WEEKLY, MONTHLY, INTERVAL |
| TIMEZONE | `zoneinfo` en `recurrence.py` |
| IDEMPOTENCY | `uq_automation_occurrence` + IntegrityError handling |
| RETRIES | `max_retries` / `retry_delay_seconds` en `_execute_run` |
| APPROVAL | `sync_run_from_work_plan` + hook en `decide_approval` |
| FINOPS | `_sum_run_cost` desde `FinOpsRecord` existente |
| TENANT | `organization_id` en queries + tests negativos |
| PERMISSIONS | `automation.*` en roles admin/operator/viewer |
| AUDIT | `automation.created/updated/activated/paused/run_*` |
| UI | Lista, wizard 5 pasos, monitor de ejecuciones |
| WIZARD | Identidad → Qué → Cuándo → Límites → Revisar |
| MONITOR | `/automatizaciones/:id/ejecuciones` + drill-down WorkPlan |
| ORCHESTRATOR E2E | `route_task` / `execute_plan` sin segundo orquestador |
| TESTS | 20 tests `test_automations_810.py` + regresión 45/45 |
| REGRESSION | Suite completa PASS |
| BUILD | `npm run build` PASS |

## FLUJO

```
TRIGGER → AUTOMATION → route_task/execute_plan → WORKPLAN → EMPLOYEETASK → TOOL → APPROVAL → RESULTADO
```

## PENDIENTES

- **A:** Conectores externos (WEBHOOK, EMAIL, etc.) — contrato preparado, sin implementar
- **B:** CRON expresión directa — arquitectura extensible vía `recurrence_config`
- **C:** Certificación Windows scheduler en producción multi-worker

## RESULTADO

**CURSOR-810 PASS** — No merge (PR independiente contra `main`).
