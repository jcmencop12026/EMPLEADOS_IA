# CURSOR — Corrección PR #7 / CODEX-820 (reauditoría Codex)

**Fecha:** 2026-08-24  
**Estado final:** CORREGIDO Y LISTO PARA NUEVA REAUDITORÍA  
**No declarado apto para merge**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #7 |
| Título | CODEX-820: Centro de notificaciones y alertas V1 |
| Rama | `codex/notifications-alerts-820` |
| Base | `main` |
| HEAD inicial (Codex) | `c3331ccbc2c285cf5a0ce95beaa9c57c1b882962` |
| HEAD final | `16762dd` |
| Commit corrección | `16762dd` — `fix(820): close Codex reaudit blockers for PR #7` |

---

## CINCO DEFECTOS BLOQUEANTES — CAUSA RAÍZ Y CORRECCIÓN

### 1. Event bus cross-tenant recipient

| | |
|---|---|
| **Causa raíz** | La materialización de notificaciones no validaba `recipient.tenant_id == notification.tenant_id` en la frontera de persistencia; además, al fallar una regla con destinatario inválido, el fallback `DEFAULTS` podía crear notificación sin destinatario. |
| **Corrección** | `validate_notification_recipient()` central en `notification_recipients.py`, aplicada en `_persist_notification()`, `emit_event()` (reglas) y routers. Se bloquea fallback `DEFAULTS` cuando hubo reglas coincidentes con destinatario denegado (`denied_recipient`). |
| **Archivos** | `notification_recipients.py`, `notifications.py`, `routers/notifications.py` |

### 2. Listener escapa del SAVEPOINT (`session.commit()`)

| | |
|---|---|
| **Causa raíz** | Los listeners recibían `Session` completa y podían invocar `commit()`/`rollback()`, confirmando cambios fuera del SAVEPOINT del dispatcher. |
| **Corrección** | `SubscriberSession` (proxy) en `subscriber_session.py` que prohíbe `commit()`, `rollback()` y `close()`. `bus.publish()` envuelve la sesión entregada a cada handler. El dispatcher conserva propiedad de SAVEPOINT/commit/rollback. |
| **Archivos** | `events/subscriber_session.py`, `events/bus.py` (+ import faltante de `write_audit`) |

### 3. Viewer puede decidir aprobaciones vía deep link

| | |
|---|---|
| **Causa raíz** | La ruta de decisión de aprobación no exigía `operations.approve`; el frontend mostraba acciones sin consultar permisos. |
| **Corrección** | Permiso `operations.approve` en `permissions.py` (operator/admin sí; viewer no). `approval_decide` exige `check_permission(user, "operations.approve")`. `/api/auth/me` expone `permissions`. `ExecutionDetailPage` oculta aprobar/rechazar sin permiso. |
| **Archivos** | `permissions.py`, `routers/operations.py`, `routers/auth.py`, `schemas.py`, `ExecutionDetailPage.tsx`, `api.ts` |

### 4. `/notificaciones` en blanco (Promise desde `useEffect`)

| | |
|---|---|
| **Causa raíz** | `useEffect` retornaba la Promise de una función `async` (`load`), violando el contrato de React y rompiendo el render. |
| **Corrección** | Patrón `let cancelled = false; void load(); return () => { cancelled = true }` con estados `loading`, `error` y empty state. |
| **Archivos** | `NotificationsPage.tsx` |

### 5. Eventos duplicados generan notificaciones duplicadas

| | |
|---|---|
| **Causa raíz** | Sin identificador estable ni constraint de unicidad; reintentos/concurrencia podían insertar filas duplicadas. |
| **Corrección** | `resolve_event_id()`, `build_idempotency_key()`, columnas `event_id`, `rule_id`, `idempotency_key`, índice único `(organization_id, idempotency_key)` en modelo y migración `820a2`. `_persist_notification()` consulta primero, inserta en nested savepoint, captura `IntegrityError`; `emit_event()` re-resuelve en `commit` ante carrera. |
| **Archivos** | `notifications.py`, `models.py`, `820a2_notification_idempotency.py` |

---

## ARQUITECTURA APLICADA

```
Evento → bus.publish()
           └─ SAVEPOINT por subscriber
                └─ SubscriberSession(db)  ← sin commit/rollback
                     └─ handler (notifications, audit, …)

emit_event() / API / reglas
  └─ validate_notification_recipient()  ← frontera autoritativa
  └─ _persist_notification()
        ├─ idempotency_key lookup
        ├─ nested savepoint + CHANNEL deliver
        └─ IntegrityError → fila existente

approval_decide
  └─ check_permission("operations.approve")  ← backend autoridad
```

---

## ARCHIVOS MODIFICADOS / NUEVOS

| Archivo | Cambio |
|---------|--------|
| `backend/app/notification_recipients.py` | **Nuevo** — validación central destinatario |
| `backend/app/events/subscriber_session.py` | **Nuevo** — sesión limitada para listeners |
| `backend/app/notifications.py` | Idempotencia, validación, DEFAULTS seguro |
| `backend/app/events/bus.py` | SubscriberSession + import `write_audit` |
| `backend/app/models.py` | Campos idempotencia + `UniqueConstraint` |
| `backend/app/permissions.py` | `operations.approve` |
| `backend/app/routers/operations.py` | Guard en `approval_decide` |
| `backend/app/routers/auth.py` | `permissions` en `/me` |
| `backend/app/routers/notifications.py` | Validador central en reglas |
| `backend/app/schemas.py` | `UserMe.permissions` |
| `backend/alembic/versions/820a2_notification_idempotency.py` | **Nuevo** — migración idempotencia |
| `tests/test_notifications_820_adversarial.py` | **Nuevo** — 12 pruebas adversariales |
| `frontend/src/pages/NotificationsPage.tsx` | Fix lifecycle async |
| `frontend/src/pages/ExecutionDetailPage.tsx` | Ocultar acciones sin permiso |
| `frontend/src/api.ts` | Tipo `UserMe.permissions` |

---

## TESTS NUEVOS (adversariales)

`tests/test_notifications_820_adversarial.py` — 12 tests:

| Test | Defecto cubierto |
|------|------------------|
| `test_event_bus_cross_tenant_recipient_denied` | Cross-tenant regla → DENY |
| `test_emit_event_manipulated_recipient_cross_tenant_denied` | Payload manipulado → DENY |
| `test_emit_event_nonexistent_recipient_denied` | Recipient inexistente → DENY |
| `test_emit_event_same_tenant_recipient_allowed` | Mismo tenant → OK |
| `test_listener_commit_forbidden_and_savepoint_holds` | commit() malicioso → sin persistencia |
| `test_two_listeners_second_commit_fails_no_partial_persist` | Dos listeners → sin commit parcial |
| `test_viewer_cannot_approve_or_reject` | Viewer deep link/API → 403 |
| `test_operator_can_decide_approval` | Operador autorizado → 200 |
| `test_event_idempotency_sequential_duplicate` | Mismo evento 2× secuencial → 1 fila |
| `test_event_idempotency_concurrent_duplicate` | Mismo evento concurrente → 1 fila |
| `test_event_idempotency_two_recipients_same_event` | Mismo event_id, 2 recipients → 2 filas |
| `test_resolve_event_id_is_stable` | event_id estable |

Suite `test_notifications_820.py` (13 tests) preservada sin regresiones.

---

## RESULTADOS EXACTOS

| Comando | Resultado |
|---------|-----------|
| `pytest` (73 tests) | **73 passed** |
| `alembic upgrade head` (SQLite limpio) | **PASS** |
| `alembic downgrade 820a1` | **PASS** |
| `alembic upgrade head` (re-upgrade) | **PASS** |
| `npm run build` | **PASS** |
| `npm audit` | **0 vulnerabilities** |
| `git diff --check` | **PASS** |
| Tests frontend automatizados | **No disponibles** (sin vitest/jest en `package.json`; verificación por build + patrón corregido) |
| PostgreSQL real | **NO CERTIFICADO** (servidor no disponible en entorno de ejecución) |

---

## MIGRACIONES

| Revisión | Estado |
|----------|--------|
| `820a1` | Preservada, sin edición destructiva |
| `820a2` | Nueva — `event_id`, `rule_id`, `idempotency_key`, FK `fk_notifications_rule_id`, índice único `uq_notifications_idempotency` |

Roundtrip SQLite: upgrade → downgrade 820a1 → upgrade **PASS**.

---

## TABLA DE CONTROLES

| Control | Resultado |
|---------|-----------|
| Event bus recipient tenant | **PASS** |
| Listener transaction isolation | **PASS** |
| SAVEPOINT escape | **PASS** |
| Viewer approval | **PASS** |
| Viewer rejection | **PASS** |
| Deep-link authorization | **PASS** |
| /notificaciones render | **PASS** |
| Event idempotency | **PASS** |
| Concurrent duplicate | **PASS** |
| Cross-tenant | **PASS** |
| Migration | **PASS** |
| PostgreSQL real | **NO CERTIFICADO** |
| Backend tests | **PASS** (73/73) |
| Frontend | **PASS** (build) |
| npm audit | **PASS** |
| git diff --check | **PASS** |

---

## NO REGRESIONES PRESERVADAS

- Validación destinatario en `create_rule` y `update_rule`
- Viewer acknowledge → 403
- Alert rule cross-tenant → 404
- Migración 820a1 intacta
- Listado notificaciones, badge, deep links autorizados
- Integración orquestador, agent factory, auth
- Sin cambios en ramas PR #6, #8, #9, #10

---

## RIESGOS RESIDUALES

1. **PostgreSQL real no certificado** — migración 820a2 y constraint único deben validarse en instancia PostgreSQL antes de merge.
2. **Tests frontend automatizados ausentes** — estados loading/error/unmount verificados por corrección de código y build; no hay suite E2E en CI frontend.
3. **Idempotencia cross-process** — protegida por constraint DB; workers en procesos distintos dependen del motor (PostgreSQL recomendado para producción).

---

## BLOQUEOS RESTANTES PARA MERGE

- Reauditoría Codex pendiente
- Certificación PostgreSQL real pendiente
- No se realizó merge (instrucción explícita)

**Estado entregado:** CORREGIDO Y LISTO PARA NUEVA REAUDITORÍA
