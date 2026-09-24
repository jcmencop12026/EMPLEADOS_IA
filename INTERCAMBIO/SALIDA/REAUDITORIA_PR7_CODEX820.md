# Reauditoría independiente — PR #7 / CODEX-820

Fecha: 2026-08-24

- Proyecto/Git root: `D:\EMPLEADOS_IA`
- PR: #7 — Centro de notificaciones y alertas V1
- Rama: `codex/notifications-alerts-820`
- HEAD auditado: `c3331ccbc2c285cf5a0ce95beaa9c57c1b882962`
- Base/merge-base: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- Diff: 24 archivos, +1.331/-16.
- Ejecución en checkout detached. No se realizó merge, push, rebase, cherry-pick ni corrección del PR; no se modificaron PR #6/#8/#9/#10.

## Veredicto

**NO APTO PARA MERGE**

## Hallazgos

### 1. Alta — Event bus permite recipient cross-tenant

`backend/app/notifications.py:99-108` copia `payload.recipient_user_id` directamente a la notificación generada por evento, sin comprobar que el usuario pertenezca a `event.organization_id`.

Reproducción independiente:

- evento con organización A;
- payload con `recipient_user_id` de usuario organización B;
- resultado: notificación persistida con `organization_id=A` y destinatario B.

Las FKs (`backend/app/models.py:57,64` y migración 820a1) sólo garantizan que el usuario exista; no pueden expresar que usuario y notificación pertenezcan al mismo tenant.

Las rutas HTTP create/update de reglas sí reutilizan `_validate_recipient_user()` y rechazan recipient cross-tenant/inexistente con 400, pero el camino interno de eventos evita esa validación. Se incumple el aislamiento tenant del sistema completo.

### 2. Alta — Un listener puede escapar del SAVEPOINT mediante commit

`backend/app/events/bus.py:58-88` crea nested transactions/SAVEPOINT, pero entrega al listener la `Session` SQLAlchemy cruda. El contrato indica que sólo el owner debe hacer commit, pero no existe enforcement técnico.

Prueba:

1. listener persiste un registro;
2. listener ejecuta `db.commit()`;
3. listener lanza excepción;
4. caller intenta rollback.

Resultado: el registro `committed_partial` permaneció (`count=1`). El SAVEPOINT no puede revertir un commit efectuado por el listener. Por tanto, un listener defectuoso puede romper la atomicidad de la transacción principal.

Caso positivo: si el listener falla sin commit explícito, su SAVEPOINT revierte el efecto y los listeners posteriores continúan.

### 3. Alta — Deep link expone decisión de aprobación sin permiso

`frontend/src/pages/NotificationsPage.tsx:5-8` convierte `APPROVAL_REQUIRED` en enlace a ejecución. `ExecutionDetailPage.tsx:78-86` muestra Aprobar/Rechazar cuando el estado es PENDING, sin consultar permisos. Sus handlers `:42-46` llaman pending/decide.

Los endpoints `backend/app/routers/operations.py:83-111` sólo exigen autenticación y tenant; no exigen `operations.approve` ni permiso equivalente. Un `viewer` autenticado del mismo tenant puede seguir el nuevo deep link y decidir una aprobación. El filtrado de organización evita la variante cross-tenant, pero no la escalación horizontal dentro del tenant.

### 4. Bloqueante funcional — `/notificaciones` queda en blanco

Reproducido en navegador real con sesión admin:

- `NotificationsPage.tsx:24` define `load()` devolviendo Promise;
- `NotificationsPage.tsx:25` ejecuta `useEffect(load, [])`;
- React StrictMode (`frontend/src/main.tsx:1,8`) interpreta el valor devuelto como cleanup;
- la pantalla queda en blanco;
- consola: `TypeError: destroy is not a function` y advertencia de que `useEffect` sólo puede retornar cleanup.

El centro de notificaciones no es utilizable en el target local/dev auditado.

### 5. Media — Eventos duplicados generan notificaciones duplicadas

`EventMessage`/`publish()` y `notifications.py:76-113` no incluyen identidad/idempotency key ni una restricción única de ocurrencia. Publicar dos veces el mismo evento creó dos notificaciones. Reintentos de productores o listeners duplican avisos y badge.

### 6. Media — Paginación incompleta

`backend/app/routers/notifications.py:55-75` sólo acepta `limit`; no implementa offset/cursor. `?limit=1&offset=1` devolvió la misma primera página. Esto no satisface paginación real ni escalabilidad para usuarios con muchas notificaciones.

### 7. Media — CRUD de alert rules incompleto

El router sólo expone list/create/PUT/enable/disable (`notifications.py:151-197`). No existen GET individual ni DELETE, pese al CRUD solicitado.

### 8. Media — Acciones UI sin autorización/resiliencia suficiente

- NotificationsPage muestra Acknowledge a viewer aunque backend devuelve 403.
- La Promise de acción no tiene manejo visible de error; el rechazo no muestra mensaje ni refresca badge.
- No hay estados diferenciados loading/empty.
- El badge (`AppShell.tsx:19-23`) silencia errores y puede mostrar 0/stale como si fuera valor real.

### 9. Baja/contrato — PUT no es actualización parcial

`AlertRuleIn` contiene defaults (`backend/app/schemas.py:30-38`) y PUT usa el modelo completo. Omitir recipient/severity/condition/enabled reinicia o borra valores. No existe PATCH/exclude_unset.

- recipient omitido: se elimina;
- null explícito: se elimina;
- condition vacía: termina como NULL;
- name vacío: 422.

Si el contrato esperado era partial update, falla. Si PUT se documenta como reemplazo total, debe quedar explícito y la UI debe enviar el recurso completo.

`recipient_role` además acepta cualquier texto de hasta 40 caracteres, permitiendo reglas sin destinatario efectivo.

## Tenant isolation y autorización

| Escenario | Resultado |
|---|---|
| Create rule con recipient tenant B | 400 — PASS |
| Update rule con recipient tenant B | 400 — PASS |
| Recipient inexistente | 400 — PASS |
| PUT/enable/disable regla tenant B | 404 — PASS |
| GET/DELETE individual de regla | Endpoint inexistente — FAIL CRUD |
| Leer/mark-read/dismiss/ack notification tenant B | Org-scoped/denegado — PASS |
| Viewer acknowledge | 403 — PASS endpoint notifications |
| Endpoint alternativo notification acknowledge | No encontrado — PASS |
| Decidir Approval desde deep link como viewer | Permitido por operations sin permiso — FAIL |
| Evento interno con recipient tenant B | Notificación cross-tenant persistida — FAIL |

## Alert rules y actualización

- Create/update recipient HTTP: validación tenant correcta.
- Enable/disable: tenant-scoped.
- Delete: no implementado.
- GET individual: no implementado.
- Filtros/list: disponibles de forma básica.
- PUT: reemplazo completo; no partial update seguro.
- Diferencia crítica create/update vs internal event: las APIs validan recipient; `emit_event()` no.

## Event bus / SAVEPOINT

| Prueba | Resultado |
|---|---|
| Listener falla sin commit | SAVEPOINT revierte y siguiente listener continúa — PASS |
| Dos listeners, uno PASS/otro FAIL | Aislamiento básico por nested transaction — PASS condicionado |
| Listener hace commit y luego falla | Efecto persiste fuera del rollback — FAIL |
| Evento idéntico dos veces | Dos notificaciones — FAIL idempotencia |
| Persistencia parcial y excepción sin commit | Rollback del SAVEPOINT — PASS |

Conclusión: el SAVEPOINT sirve sólo mientras los listeners cumplen voluntariamente el contrato de no hacer commit. La API entrega capacidad suficiente para romperlo.

## Notificaciones

- Listado/filtros/unread/read/dismiss/ack: presentes.
- Tenant scoping: correcto en queries HTTP.
- Sin notificaciones: backend devuelve lista vacía; UI no diferencia loading/empty.
- Muchas notificaciones: limit existe, paginación real no.
- ID inexistente/otro tenant: no filtra existencia.
- Duplicados: no controlados.
- Badge: actualización periódica/event-driven diseñada, pero error se silencia y el centro crashea.

## Deep links

- Sin autenticación: redirige a `/login` — PASS.
- Ejecución/empleado cross-tenant: backend devuelve 404 por org filter — PASS.
- Recurso inexistente: error/404; no bypass.
- Approval same-tenant sin permiso: FAIL.
- Parámetros manipulados: approval arbitrario puede dejar controles engañosos; source_id se inserta en path sin encoding.

## Migración 820a1

SQLite temporal:

- upgrade: PASS;
- datos preexistentes preservados: PASS;
- tablas notifications/alert_rules: presentes;
- índices: 8 y 4 respectivamente;
- FKs/defaults/nullable: verificados;
- `PRAGMA foreign_key_check=[]`;
- downgrade: PASS, elimina las tablas y por diseño pierde datos del módulo;
- upgrade posterior: PASS.

PostgreSQL: generación offline de DDL PASS. No había servidor PostgreSQL disponible, por lo que no se ejecutó roundtrip real sobre PostgreSQL.

## Integraciones

Orchestrator/Agent Factory/Auth derivan normalmente `organization_id` de plan/user/employee. No se encontró emisión productiva explícita con org equivocado. Sin embargo, la función interna acepta recipient arbitrario cross-tenant y confía por completo en el productor. No hay event ID ni deduplicación, por lo que reintentos pueden duplicar notificaciones.

## Pruebas y herramientas

- Suite completa backend: `69 passed`, 0 failed, 0 skipped, 1 warning.
- Suite focal/adversarial: `42 passed`; las pruebas propias documentan/reproducen tanto controles como defectos.
- Frontend `npm ci`: PASS, 73 paquetes.
- `npm audit`: PASS, 0 vulnerabilidades.
- `npm run build`: PASS, Vite 6.4.3, 55 módulos; JS 263,54 kB / 82,00 kB gzip; CSS 6,47 kB / 1,83 kB gzip.
- `git diff --check`: PASS.
- Secretos/artefactos/binarios accidentales: no encontrados.
- Control visual real: login/guard PASS; `/notificaciones` autenticado FAIL con pantalla en blanco y error React.

## Modelo de amenaza resumido

Actores: viewer/editor/admin del tenant, productor interno defectuoso/comprometido y listener defectuoso. Activos: confidencialidad de destinatarios, integridad de transacción, decisiones de aprobación, badge y trazabilidad. Fronteras críticas: HTTP→queries tenant-scoped, producer→EventMessage, listener→Session compartida y notification deep link→operations approval. Los controles HTTP son razonables, pero la frontera interna confía en recipient/org y commit discipline; el deep link alcanza un endpoint de aprobación sin RBAC.

## Tabla final

| Control | Resultado |
|---|---|
| Tenant isolation | FAIL |
| Create recipient validation | PASS |
| Update recipient validation | PASS |
| Acknowledge authorization | PASS notifications / FAIL approval deep link |
| Alert rules | FAIL |
| Notifications | FAIL |
| Event bus | FAIL |
| SAVEPOINT | FAIL |
| Deep links | FAIL |
| Migration 820a1 | PASS SQLite / PostgreSQL limitado |
| Suite | PASS |
| Build | PASS |
| npm audit | PASS |
| git diff --check | PASS |
| RESULTADO FINAL | NO APTO |

## Conclusión

PR #7 / CODEX-820 en `c3331ccbc2c285cf5a0ce95beaa9c57c1b882962`: **NO APTO PARA MERGE**.

Bloqueantes principales:

1. recipient cross-tenant por event bus;
2. listener puede escapar SAVEPOINT mediante commit;
3. viewer puede decidir aprobaciones desde el nuevo deep link;
4. centro `/notificaciones` queda en blanco por error de lifecycle React.

**NO MERGE REALIZADO. NO SE MODIFICÓ EL PR.**
