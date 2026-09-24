# CODEX — Reauditoría conjunta final PR #6 / 810C y PR #9 / 840B

Fecha: 2026-08-24

Alcance limitado a las correcciones posteriores a los heads auditados y sus regresiones solicitadas. No se realizó merge, corrección, push, rebase ni cherry-pick.

## PR #6 — CURSOR-810C

- HEAD anterior: `b1a5c7fb103c90f6ab6cb98496601ef9b93a2177`
- HEAD PR: `03c58dfc3378ea19e6a01880963afe5b1ab180fc`
- Delta post-auditoría: 5 archivos, 480 inserciones, 38 eliminaciones.
- Archivos inspeccionados: `automation_service.py`, `recurrence.py`, `api.ts`, `AutomationWizardPage.tsx`, `test_automations_810c.py`.

### TIMEOUT: FAIL — defecto A persiste

Reproducción real controlada:

- `timeout_seconds=1`
- trabajo lento: 1,8 s
- `max_retries=3`
- retorno del servicio: 1,137 s
- estado al retorno: `FAILED`
- `attempt=1`
- `finished_at` presente
- AuditLog timeout: 1
- AuditLog failed: 1
- AuditLog retry: 0
- efecto tardío al retorno: 0
- efecto tardío 1,1 s después: 1

El estado no fue sobrescrito y no quedó `RUNNING`, pero el trabajo real continuó y produjo un efecto después del timeout. `future.cancel()` y `shutdown(wait=False)` no detienen un future ya iniciado (`backend/app/services/automation_service.py:421-432`). El trabajo entra en `route_task(auto_execute=True)` (`:514-523`) y comparte una `Session` SQLAlchemy con el thread (`:673-678`). Esto viola el requisito de que la herramienta no continúe silenciosamente.

### RETRY DELAY: PASS con pendiente B

Reproducción con `max_retries=2`, `retry_delay_seconds=1`:

- intentos totales: 3, conforme a inicial + N retries
- gaps: 1,024 s y 1,037 s
- elapsed total: 2,137 s
- estado final: `FAILED`

Para valores hasta 300 s se respeta el delay. Valores superiores se recortan silenciosamente mediante `MAX_RETRY_DELAY_SECONDS=300` (`automation_service.py:31-32,721-723`) aunque el schema no declara ese máximo. Debe validarse/rechazarse o documentarse; pendiente B.

### EVENT IDEMPOTENCY: PASS

- mismo INTERNAL_EVENT emitido dos veces: 1 AutomationRun / 1 ejecución efectiva
- evento con identidad distinta: nueva ejecución permitida
- evento cross-tenant: 0 ejecuciones
- anti-loop: PASS

La clave estable usa `event_id`, `idempotency_key` o hash determinístico (`backend/app/services/recurrence.py:34-42`), apoyada por unique `(automation_id, occurrence_key)`. El handler filtra organización y conserva protección anti-loop.

### WIZARD EDIT: FAIL — defecto A persiste

La edición preserva start/end parcialmente, employee, timezone, límites, approval, retries y timeout, pero no preserva toda la configuración:

- al cargar sólo recupera `workflow.tool` y `workflow.estimated_cost` (`frontend/src/pages/AutomationWizardPage.tsx:69-96`);
- al guardar reconstruye `workflow` únicamente con esos campos (`:157-177`), eliminando capabilities, model y claves adicionales;
- `buildRecurrence` sólo conserva interval o hour/minute (`:147-155`), eliminando `weekdays` para WEEKLY y `day_of_month` para MONTHLY.

Editar un campo simple sigue siendo destructivo para configuración compleja.

### Regresión

- APPROVAL: PASS
- FINOPS: PASS respecto de las correcciones 810C; no se reabrió el pendiente histórico de estimación fiable.
- TENANT: PASS
- AUDIT: PASS para timeout/failed y flujos regresados.
- RUN NOW: PASS
- SCHEDULER: PASS
- INTERNAL EVENT: PASS

### Pruebas

- Tests 810/810B/810C: 49 passed, 0 failed, 0 skipped — 39,65 s
- Suite completa: 95 passed, 0 failed, 0 skipped — 106,28 s
- Advertencias: 3 deprecaciones
- NPM AUDIT: 0 vulnerabilidades
- BUILD: PASS, Vite, 57 módulos, 2,17 s
- GIT: `git diff --check` PASS

### Pendientes PR #6

- A: cancelación/aislamiento real del trabajo tras timeout; preservación completa de workflow y recurrencia en edición.
- B: validar o respetar `retry_delay_seconds > 300`.
- C: pruebas con side effects externos reales, UI E2E de workflow/model/capabilities/WEEKLY/MONTHLY y estrés concurrente.

### Veredicto PR #6

**NO APTO PARA MERGE**

## PR #9 — CURSOR-840B

- HEAD anterior: `5c1e4b34ab3d49b5dae7a95376549050a39d1795`
- HEAD PR: `fa1b1acb1c7a564eecc48e3c3715cf30f99d7a3e`
- Delta post-auditoría: 10 archivos, 665 inserciones, 54 eliminaciones.
- Commits del delta: `a2384c2`, `83337a4`, `4f7ba18`, `fa1b1ac`.

### MIGRATION: PASS

BD SQLite temporal:

1. upgrade a revisión base;
2. inserción de organización y usuario de control;
3. upgrade 840B;
4. downgrade;
5. upgrade nuevamente.

Resultado:

- datos preservados en todas las etapas;
- tablas `roles`, `permissions`, `role_permissions` presentes;
- FKs de organización y self-FKs de usuario presentes tras upgrade;
- `PRAGMA foreign_key_check=[]`;
- sin fallo `batch_alter_table`;
- downgrade/upgrade repetible.

### AUTHORIZATION MODEL / FALLBACK: FAIL — defecto A

La fuente DB todavía no es determinística para toda fila Role existente. `backend/app/permissions.py:111-122` busca únicamente roles con `is_active=True`. Si la fila existe pero está inactiva, el resolver devuelve `None`; `user_permissions` (`:135-144`) ejecuta el fallback hardcoded.

Reproducción:

- fila DB `Role(code='admin', is_active=False)` existente: 1 fila;
- permisos efectivos: 26 permisos hardcoded;
- incluye `admin.user.create=True`;
- mismo rol activo y sin RolePermission: conjunto vacío correcto;
- rol inexistente: fallback `employee.view`.

Por tanto, una fila DB inactiva puede conceder más permisos que la DB y contradice la afirmación “fallback sólo cuando no existe fila Role”. Es un fail-open de autorización.

### PRIVILEGE ESCALATION: PASS para ataques anteriores

- asignarse `superadmin` / `SUPERADMIN`: 403
- concederse permisos fuera del subconjunto propio: 403
- modificar rol global protegido: 403
- modificar permisos de rol de otro tenant: 404
- asignar rol cross-tenant: 403/422
- auto-cambiar rol: 403
- manipulación UUID cross-tenant: bloqueada

Las comprobaciones de subconjunto, rol protegido y tenant están presentes en `permissions.py:147-175`, `admin_service.py:88-91,127-134,256-285` y rutas administrativas `admin.py:163-182`.

### ROLE MATRIX EDIT: PASS con cobertura visual parcial

- rol personalizado: agregar permiso, guardar y verificar — PASS
- retirar permiso, guardar y verificar — PASS
- cancelar: implementado en UI por estado local
- rol protegido: sólo lectura
- backend enforce: PASS

Evidencia UI/API: `frontend/src/pages/admin/AdminRolesPage.tsx:12-14,48-83,117-125,176-205` y `frontend/src/api.ts:349-353`. No se realizó recorrido visual autenticado real; la comprobación UI fue por código/build.

### TENANT: PASS

ORG A no puede asignar, modificar ni cambiar permisos de roles ORG B. Los intentos UUID directos se rechazaron.

### USERS / PASSWORDS / REGRESIÓN: PASS

- crear usuario: 201
- login activo: 200
- reset password: 200
- contraseña anterior: 401
- contraseña nueva: 200
- usuario BLOCKED: 401
- users/organization/config/security/audit: 200

### AUDIT: PASS para las regresiones 840B solicitadas

No se reabrieron los pendientes históricos de estructura de AuditLog fuera del delta corregido.

### Pruebas

- Suite enfocada administración: 27 passed, 0 failed, 0 skipped
- Suite completa: 73 passed, 0 failed, 0 skipped — 94,01 s
- Advertencias: 3
- NPM AUDIT: 0 vulnerabilidades
- BUILD: PASS, Vite 6.4.3, 59 módulos; JS 275,37 kB / 84,17 kB gzip
- GIT: FAIL. Whitespace final en `INTERCAMBIO/SALIDA/CURSOR_840B_ADMIN_POST_AUDIT.md:3-5`.

### Pendientes PR #9

- A: fallback fail-open cuando existe una fila Role inactiva.
- B: corregir whitespace del informe; no se reauditaron defectos históricos fuera del delta.
- C: recorrido visual autenticado de guardar/cancelar y pruebas de concurrencia/invalidation de sesión.

### Veredicto PR #9

**NO APTO PARA MERGE**

## Resumen consolidado

### PR #6 CURSOR-810C: NO APTO

Bloqueantes:

- el trabajo real continúa y produce efectos después del timeout;
- editar sigue eliminando workflow complejo y parámetros WEEKLY/MONTHLY.

### PR #9 CURSOR-840B: NO APTO

Bloqueantes:

- una fila DB Role inactiva activa el fallback hardcoded y concede permisos superiores a la DB.

**NO MERGE REALIZADO.**
