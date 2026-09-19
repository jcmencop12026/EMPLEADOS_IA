# Reauditoría independiente final — PR #6 / 810C y PR #9 / 840B

Fecha: 2026-08-24

Git root confirmado: `D:\EMPLEADOS_IA`.

Rama activa del repositorio principal durante la auditoría: `codex/notifications-alerts-820`; no se trabajó sobre `main`. Los PR se auditaron en worktrees detached. No se modificaron PR #7, #8 ni #10. No se realizó merge, push, rebase, cherry-pick ni corrección de código.

Estado inicial observado: existían informes de auditorías anteriores sin seguimiento y un directorio temporal previo; se preservaron como cambios ajenos.

## PR #6 — CURSOR-810C

- Rama: `cursor/automations-scheduler-810`
- HEAD auditado: `fa07040e8b38efebb309677d72a2c6bdd7ded082`
- Head previo: `03c58dfc3378ea19e6a01880963afe5b1ab180fc`
- Base/merge-base: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- Delta desde head previo: 6 archivos, +584/-83.
- Diff completo contra base: 26 archivos.
- Archivos del delta revisados: implementación del guard/timeout, coordinator, wizard/API, tests 810C e informe compartido.
- No contiene cambios de código de PR #7/#8/#10; sí modifica `coordinator.py`, superficie que deberá resolverse al integrar con PR #10.

### Hallazgo PR6-1 — Timeout cooperativo permite efectos tardíos

- Severidad: ALTA
- Confianza: ALTA
- Resultado: defecto original reproducible.

`backend/app/services/automation_service.py:437-448` ejecuta el trabajo en `ThreadPoolExecutor`. Al vencer el timeout, `future.cancel()` no detiene un thread que ya comenzó. `RunExecutionGuard` es un `Event`/context binding y sólo detiene código que voluntariamente llama un checkpoint.

En `backend/app/services/coordinator.py:283-285` hay checkpoints alrededor de `_run_tool`, pero no dentro de una herramienta arbitraria. Una herramienta lenta/no cooperativa puede ejecutar side effects durante la llamada. También existen espacios posteriores al último checkpoint: aprobación/event publishing `:317-362`, FinOps add `:364` y commit `:374`. Persistencia/publish previa en `:259-273` tampoco está neutralizada por el guard.

### Pruebas adversas RunExecutionGuard

| Caso | Resultado observado | Veredicto |
|---|---|---|
| A — efecto tardío simple | Memoria terminó como `['late']` después del timeout | FAIL |
| B — varios pasos | Se observaron `[1,2,3,4]`; se esperaba sólo `[1]` | FAIL |
| C — worker thread real | Binding visible, pero worker no cooperativo sobrevivió | FAIL |
| D — subprocess/equivalente | Subproceso detached sobrevivió y creó archivo | FAIL |
| E — DB side effect | SQLite persistió una fila tardía (`count=1`) | FAIL |
| F — side effect externo simulado | Archivo tardío creado | FAIL |
| G — race condition | 100/100 carreras cercanas al timeout produjeron efecto | FAIL |
| H — cancelación + error | `finally` produjo `['finally-side-effect']` | FAIL |

Timeouts usados: 0,03–0,05 s en pruebas aisladas del head exacto.

Los tests aportados en `tests/test_automations_810c.py:286-383` llaman `require_execution_allowed()` antes de cada efecto simulado y absorben `ExecutionCancelledError`; demuestran herramientas cooperativas, no neutralización de side effects no cooperativos.

No se puede cumplir el requisito “0 efectos posteriores” con threads Python y checkpoints voluntarios para herramientas arbitrarias, subprocesos detached o llamadas externas ya iniciadas.

### Deep merge / wizard

La corrección `_deep_merge()` (`automation_service.py:31-42`) pasó la matriz backend/API:

- campo ausente: preservado;
- objeto anidado: actualiza sólo la hoja y preserva siblings;
- array no enviado: preservado;
- array explícito `[]`: vaciado respetado;
- `null` explícito: reemplaza;
- nested null: reemplaza sólo la hoja;
- objeto → string/null/array: reemplazo determinístico;
- scalar → objeto: reemplazo determinístico;
- arrays tratados como valores atómicos.

El wizard (`frontend/src/pages/AutomationWizardPage.tsx:185-226`) envía en edición sólo campos expuestos que cambiaron. No envía defaults ni arrays vacíos involuntarios; workflow oculto/model/tools ausentes del patch se preservan mediante deep merge.

Resultado wizard/deep merge: PASS.

### Compatibilidad transversal

- Principios PR #8: partial update/exclude-unset y preservación de campos no enviados: PASS para el flujo 810C.
- Tenant employee checks: PASS.
- Compatibilidad PR #10: FAIL/no demostrable en este head standalone. No existe `authorization.py/evaluate_tool_execution`; `coordinator._execute_task()` llama `_run_tool` directamente tras un check local. Falta garantizar en integración `evaluate_tool_execution()` antes de tool y precedencia `DENY > REQUIRES_APPROVAL > ALLOW`.
- No se introdujo una segunda función alternativa nueva, pero PR #6 y PR #10 modifican la misma ruta de coordinator y requieren resolución explícita.

### Comandos y resultados PR #6

- Tests dirigidos (810/810B/810C + auth/tenant + Agent Factory + orchestrator): `81 passed`, 3 warnings, 119,92 s.
- Suite completa `pytest`: `102 passed`, 0 failed, 0 skipped, 3 warnings, 150,60 s.
- `npm run build`: PASS, 57 módulos, 5,79 s.
- `npm audit --audit-level=low`: 0 vulnerabilidades.
- Migración: N/A para este delta.
- Secretos/binarios/artefactos accidentales: no encontrados.
- `git diff --check b887a2e..fa07040`: FAIL.
- `git diff --check 03c58df..fa07040`: FAIL.
- Causa: whitespace final en `INTERCAMBIO/SALIDA/CURSOR_CORRECCION_810C_840B.md:3-4`.

### Conclusión PR #6

**NO APTO PARA MERGE**

Bloqueantes:

1. side effects tardíos sobreviven al timeout en memoria, DB, archivo, subprocess y `finally`;
2. carrera reproducida 100/100 veces;
3. compatibilidad del camino de autorización con PR #10 no está presente en este head;
4. `git diff --check` falla.

## PR #9 — CURSOR-840B

- Rama: `cursor/admin-users-roles-840`
- HEAD auditado: `0e25e3e0189b5ed9c029ee9d863d0f40782a1349`
- Head previo: `fa1b1acb1c7a564eecc48e3c3715cf30f99d7a3e`
- Base/merge-base: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- Delta desde head previo: 4 archivos, +339/-9.
- Diff completo contra base: 29 archivos, +3114/-54.
- Delta revisado: `permissions.py`, tests de autorización y documentos de entrega.
- No se modifican PR #7/#8/#10.

### Hallazgo PR9-1 — Rol inexistente obtiene permiso por fallback

- Severidad: ALTA
- Confianza: ALTA
- Resultado: fail-closed/DENY BY DEFAULT incumplido.

`backend/app/permissions.py:142-157` distingue correctamente varios casos de rol persistido, pero termina con:

```python
ROLE_PERMISSIONS_FALLBACK.get(user.role, {"employee.view"})
```

Un usuario activo con rol inexistente, obsoleto o mal escrito obtiene `employee.view`. Reproducción: `nonexistent_unknown -> ['employee.view']`. Un rol hardcoded conocido que no existe en DB recibe además todo su conjunto legacy.

Esto aumenta permisos desde cero a lectura de empleados y contradice el criterio obligatorio de deny-by-default.

### Hallazgo PR9-2 — Roles globales duplicados tienen resolución ambigua

- Severidad: MEDIA
- Confianza: ALTA

El unique SQLite `(organization_id, code)` no impide duplicados cuando `organization_id IS NULL`. Se insertaron dos roles globales con el mismo code. El resolver (`permissions.py:111-121`) usa `.first()` sin orden o control de duplicidad, por lo que una definición global activa/inactiva o A/A+B+C puede seleccionarse de forma no determinística en lugar de fallar cerrado.

### Hallazgo PR9-3 — Estado booleano corrupto se interpreta activo

- Severidad: MEDIA
- Confianza: ALTA

SQLite no tiene CHECK para el booleano. Un valor raw `roles.is_active='garbage'` fue deserializado truthy y conservó permisos: `deserialize_bad_bool -> ['A'], True`. Excepciones reales de consulta/deserialización sí son capturadas y niegan, pero este estado semánticamente corrupto no genera excepción y falla abierto.

### Matriz de autorización PR #9

| Caso | Observado | Resultado |
|---|---|---|
| Rol activo + permiso A | Sólo A | PASS |
| Rol activo sin permiso | Vacío/DENY | PASS |
| Rol inactivo | DENY | PASS |
| Rol revocado/inactivado | DENY | PASS |
| DB A vs hardcoded A+B+C | Sólo A | PASS |
| Rol inexistente desconocido | `employee.view` | FAIL |
| Rol inexistente hardcoded conocido | Fallback completo | FAIL |
| Error DB | DENY | PASS |
| Excepción de deserialización | DENY | PASS |
| Permisos vacíos | DENY | PASS |
| Nombre hardcoded coincidente pero DB inactivo | DENY | PASS |
| Duplicados globales | Aceptados; selección ambigua | FAIL |
| Booleano corrupto | Considerado activo | FAIL |
| Cache tras inactivar | Permisos retirados | PASS; no existe cache de permisos |

### Tenant y compatibilidad transversal

- Cross-tenant user read/update/status: rechazado.
- Modificación cross-tenant de permisos/roles: 404 o rechazo equivalente sin enumeración adicional observada.
- Listados excluyen el otro tenant.
- Un rol tenant A no concede acceso tenant B.
- Tenant isolation: PASS en escenarios observados.
- PR #9 no toca `operations.py`, `coordinator.py` ni `authorization.py`; no introduce una ruta alternativa de ejecución.
- La compatibilidad combinada real con PR #8/#10 no puede certificarse desde ramas paralelas standalone. Los defectos preexistentes de esas ramas no se atribuyen a PR #9.

### Migración PR #9

Upgrade/downgrade/upgrade sobre SQLite temporal con datos y self-FKs:

- usuario legacy preservado;
- status por defecto correcto;
- `created_by`/`updated_by` preservados;
- `PRAGMA foreign_key_check=[]` tras upgrade y re-upgrade;
- downgrade/upgrade repetible;
- PASS.

### Comandos y resultados PR #9

- Tests focalizados `test_admin_840.py` + `test_admin_840b.py`: `32 passed`, 3 warnings, 49,48 s.
- Suite completa `pytest`: `78 passed`, 0 failed, 0 skipped, 3 warnings, 158,43 s.
- `npm run build`: PASS, 59 módulos; JS 275,37 kB, CSS 6,32 kB.
- `npm audit --audit-level=low`: 0 vulnerabilidades.
- Migración con datos/FKs: PASS.
- Secretos/binarios accidentales: no encontrados.
- `git diff --check b887a2e..0e25e3e`: FAIL.
- Causa: whitespace final en `INTERCAMBIO/SALIDA/CURSOR_CORRECCION_810C_840B.md:3-4`.

### Conclusión PR #9

**NO APTO PARA MERGE**

Bloqueantes:

1. rol inexistente recibe permisos por fallback;
2. duplicidad global permite resolución no determinística;
3. estado `is_active` corrupto puede fallar abierto;
4. `git diff --check` falla.

## Tabla final

| Control | PR #6 | PR #9 |
|---|---|---|
| Defecto original reproducible | SÍ | SÍ |
| Corrección efectiva | FAIL | FAIL |
| Pruebas adversas | FAIL | FAIL |
| No regresiones | PASS en suite; FAIL en invariantes | PASS en suite; FAIL en invariantes |
| Tenant isolation | PASS | PASS |
| Authorization compatibility | FAIL | FAIL |
| Suite completa | PASS | PASS |
| Build | PASS | PASS |
| NPM audit | PASS | PASS |
| Migraciones | N/A | PASS |
| git diff --check | FAIL | FAIL |
| Resultado final | NO APTO | NO APTO |

## Resultado final

- PR #6 / `fa07040`: **NO APTO PARA MERGE**.
- PR #9 / `0e25e3e`: **NO APTO PARA MERGE**.
- **NO MERGE REALIZADO.**
