# CURSOR-810B — Corrección integral post-auditoría Automatizaciones

## Identificación

| Campo | Valor |
|-------|-------|
| **HEAD ANTERIOR** | `c53adfd` (auditado NO APTO) |
| **HEAD NUEVO** | _(commit tras push)_ |
| **PR #6** | https://github.com/jcmencop12026/EMPLEADOS_IA/pull/6 |
| **RAMA** | `cursor/automations-scheduler-810` |
| **BASE CORRECTA** | `b887a2e` (main post-805) |
| **RESULTADO** | **CURSOR-810B PASS** |
| **NO MERGE** | Sí |

---

## A1 — Aislamiento del PR

Rama **rebaseada** sobre `main` (`b887a2e`). El diff `git diff main...cursor/automations-scheduler-810` contiene **solo** archivos 810:

- No elimina infraestructura 805
- No modifica startup/SQLite legacy
- No toca Notifications 820

**DIFF FILE COUNT:** 21 archivos (20 código + evidencia)

**805 PRESERVED:** Sí — tests 805, scripts startup, .gitignore intactos en main

---

## Correcciones implementadas

| ID | Corrección |
|----|------------|
| **A2** | Validación cross-tenant `employee_id` en create/update + rechazo en ejecución |
| **A3** | `start_at` futuro respetado en DAILY/WEEKLY/MONTHLY/INTERVAL; `end_at` aplicado |
| **A4** | `requires_approval` crea `ApprovalRequest` antes de ejecutar; approve → `execute_plan`; reject → FAILED |
| **A5** | FinOps pre-ejecución con `workflow.estimated_cost`; sin estimación no se finge enforcement; eliminado skip post-ejecución inconsistente |
| **A6** | `max_retries` = reintentos tras intento inicial (0–10); `retry_delay_seconds` aplicado |
| **A7** | `timeout_seconds` aplicado vía `ThreadPoolExecutor` |
| **A8** | Suscriptor real en `events/bus.py` via `automation_events.py`; protección anti-bucle por `work_plan_id` |
| **A9** | E2E run-now, scheduler tick, internal event vía bus |
| **A10** | Wizard 7 pasos: validación, cancelar, editar, empleado, límites, aprobación |
| **A11** | CRUD: crear, editar, duplicar, activar, pausar, desactivar, run-now, historial, eliminar (solo DRAFT) |
| **A12** | Audit: created, updated, activated, paused, disabled, run_now, scheduler_run, retry, waiting_approval, succeeded, failed |
| **A13** | Idempotency `occurrence_key`; daily limit; riesgo multi-worker documentado |
| **A14** | `test_alembic_chain_present` portable (heredado de main post-rebase) |
| **A15** | `npm audit`: 0 vulnerabilities |

---

## Archivos del PR (lista final)

```
INTERCAMBIO/SALIDA/CURSOR_810B_AUTOMATIONS_POST_AUDIT.md
INTERCAMBIO/SALIDA/CURSOR_810_AUTOMATIONS_V1.md
backend/alembic/versions/a810f1c2d3e4_automations_scheduler_810.py
backend/app/automation_models.py
backend/app/enums.py
backend/app/main.py
backend/app/permissions.py
backend/app/routers/automations.py
backend/app/schemas_automation.py
backend/app/services/automation_events.py
backend/app/services/automation_scheduler.py
backend/app/services/automation_service.py
backend/app/services/coordinator.py
backend/app/services/recurrence.py
frontend/src/App.tsx
frontend/src/AppShell.tsx
frontend/src/api.ts
frontend/src/pages/AutomationRunsPage.tsx
frontend/src/pages/AutomationWizardPage.tsx
frontend/src/pages/AutomationsPage.tsx
tests/conftest.py
tests/test_automations_810.py
tests/test_automations_810b.py
```

---

## Pruebas

| Métrica | Resultado |
|---------|-----------|
| **TESTS PASSED** | 87 |
| **TESTS FAILED** | 0 |
| **TESTS SKIPPED** | 0 |
| **BUILD** | PASS |
| **GIT DIFF CHECK** | PASS |
| **NPM AUDIT** | 0 vulnerabilities |

Nuevos: `tests/test_automations_810b.py` (21 casos post-auditoría)

---

## Pendientes

| ID | Descripción |
|----|-------------|
| **A** | Integración con shell 830 (menú jerárquico) cuando ambos PR estén en main |
| **B** | Claim atómico multi-worker distribuido (riesgo residual documentado) |
| **C** | WEBHOOK / EMAIL / FILE_RECEIVED (fuera V1) |

---

**NO MERGE** — entrega en PR #6 para revisión.
