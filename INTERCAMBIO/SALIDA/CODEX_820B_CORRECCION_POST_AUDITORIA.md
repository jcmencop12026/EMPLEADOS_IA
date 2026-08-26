# CODEX-820B — Corrección post-auditoría PR #7

HEAD ANTERIOR: `7a3953902e1fdd0513ce40d02d1c013e957fdae8`

PR: `#7`

FAULT TOLERANCE: PASS. Cada subscriber se ejecuta dentro de un SAVEPOINT; un fallo no crítico se registra y no interrumpe los subscribers posteriores ni la operación de negocio.

TRANSACTION ISOLATION: PASS. Los subscribers de eventos, auditoría y Notifications ya no hacen commit. El caso de uso dueño de la sesión conserva el control de la transacción.

EMPLOYEE_CREATED: PASS desde Agent Factory real.

EMPLOYEE_CERTIFIED: PASS desde certificación real.

EMPLOYEE_ACTIVATED: PASS desde activación real.

EXECUTION_STARTED: PASS desde `task.started`.

EXECUTION_SUCCEEDED: PASS desde `work.completed`.

EXECUTION_FAILED: PASS desde `task.failed` / `work.failed`.

APPROVAL_REQUIRED: PASS; incluye `metadata.approval_id` real.

APPROVAL_APPROVED: PASS; se deriva únicamente de `decision=approve`.

APPROVAL_REJECTED: PASS; se deriva de `decision=reject` y nunca se normaliza como aprobado.

TOOL_DENIED: PASS desde la denegación real del grant.

FINOPS_LIMIT_REACHED: PASS desde el control real de `daily_cost_limit` existente.

TENANT_SECURITY_EVENT: PASS desde intento de login inválido para usuario conocido.

SYSTEM_ERROR: PASS desde excepción inesperada del ejecutor.

DEEP LINK: PASS. La notificación navega a `/ejecuciones/{plan_id}?approval={approval_id}` y la pantalla selecciona esa aprobación existente.

STATES: contrato único `NEW`, `READ`, `ACKNOWLEDGED`, `DISMISSED`. Se permite `NEW -> ACKNOWLEDGED`. Transiciones terminales o regresivas devuelven HTTP 409. `RESOLVED` fue eliminado de la UI.

DISMISS: PASS para el destinatario de su propia notificación con `notification.view`; no permite acceso cross-tenant ni a notificaciones invisibles.

TENANT: PASS.

PERMISSIONS: PASS.

AUDIT: PASS; los fallos de subscriber se registran como `event.subscriber_failed`, además del logging de excepción, sin publicar eventos recursivos.

TESTS PASSED: 58.

TESTS FAILED: 0.

TESTS SKIPPED: 0.

BUILD: PASS — Vite, 55 módulos transformados.

GIT: `git diff --check` PASS. Sin merge.

ALEMBIC: head de esta rama `820a1`, descendiente de `5b2eb2437398`. No se creó migración de merge; queda para integración controlada 810 + 820 sobre main.

PENDIENTES A: ninguno.

PENDIENTES B: ninguno dentro del alcance solicitado.

PENDIENTES C: warning de deprecación Starlette/httpx en la suite; no afecta ejecución.

RESULTADO: **CODEX-820B PASS**
