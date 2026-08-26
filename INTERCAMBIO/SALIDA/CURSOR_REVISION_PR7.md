# CURSOR — Revisión técnica PR #7

**Fecha:** 2026-08-24
**Estado final:** CORREGIDO Y LISTO PARA REAUDITORÍA
**No declarado apto para merge**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #7 |
| Título | CODEX-820: Centro de notificaciones y alertas V1 |
| Código | **CODEX-820** (no CURSOR) |
| Rama | `codex/notifications-alerts-820` |
| Base | `main` |
| HEAD inicial | `fca7893de291f20a0c1fb9302541bf20d3a35232` |
| HEAD final | `ae6454bc9f8e8f0e8c8e8c8e8c8e8c8e8c8e8c8` |
| Commits originales | `7a39539` feat: add notifications and alerts center · `fca7893` fix: close notifications audit findings |
| Commit corrección | `fix(820): validate alert rule recipient on update` |

---

## ALCANCE

PR #7 incorpora el **Centro de notificaciones y alertas V1**:

1. **Modelos y migración** `820a1`: tablas `notifications` y `alert_rules`.
2. **Motor de eventos desacoplado**: suscriptor en `notifications.py` conectado al bus (`events/bus.py`) con SAVEPOINT por subscriber.
3. **Canal IN_APP** y reglas de alerta configurables por tenant.
4. **API REST** tenant-aware:
   - `/api/notifications` (listar, unread-count, read/acknowledge/dismiss)
   - `/api/alert-rules` (CRUD básico, enable/disable)
5. **Integración** con orquestador, agent factory, auth (login inválido → `TENANT_SECURITY_EVENT`).
6. **Frontend**: `NotificationsPage`, badge de no leídas en `AppShell`, deep links a ejecuciones/aprobaciones.
7. **Permisos** hardcoded en rama: `notification.*`, `alert_rule.*`.

No incluye scheduler (PR #6), shell auth avanzado (PR #8), admin roles DB (PR #9) ni capabilities (PR #10).

---

## MAPA DE ARCHIVOS

| Área | Archivos | Finalidad |
|------|----------|-----------|
| Backend modelos | `models.py` | `Notification`, `AlertRule` |
| Backend API | `routers/notifications.py` | Endpoints notificaciones y reglas |
| Backend servicio | `notifications.py` | Emisión, reglas, canal IN_APP, aliases |
| Backend eventos | `events/bus.py` | SAVEPOINT + aislamiento subscribers |
| Backend integración | `coordinator.py`, `agent_factory.py`, `routers/auth.py` | Publicación eventos |
| Schemas | `schemas_notifications.py` | Contratos API |
| Permisos | `permissions.py` | Permisos notification/alert_rule |
| Migración | `820a1_notifications_alerts_v1.py` | DDL + índices |
| Frontend | `NotificationsPage.tsx`, `AppShell.tsx`, `api.ts`, `App.tsx`, `styles.css` | UI centro notificaciones |
| Frontend | `ExecutionDetailPage.tsx` | Deep link aprobación |
| Tests | `test_notifications_820.py` | Suite principal |
| Tests | `test_orchestrator_e2e.py`, `test_agent_factory_e2e.py` | Integración eventos |
| Docs | `CODEX_820B_CORRECCION_POST_AUDITORIA.md` | Evidencia auditoría previa |

---

## HALLAZGOS

### H1 — Validación destinatario ausente en `update_rule` (MEDIO)

| Campo | Detalle |
|-------|---------|
| Severidad | MEDIA |
| Archivo | `backend/app/routers/notifications.py` |
| Causa | `create_rule` validaba `recipient_user_id` en el mismo tenant; `update_rule` no |
| Riesgo | Asignar destinatario cross-tenant al actualizar regla |
| Corrección | Helper `_validate_recipient_user()` reutilizado en create y update |
| Test | `test_update_rule_rejects_cross_tenant_recipient` |

### Sin otros defectos bloqueantes

Revisión adicional sin cambios requeridos:

- Aislamiento tenant notificaciones: PASS (404 cross-tenant)
- Aislamiento tenant reglas: PASS (`_get_rule` filtra `organization_id`)
- Máquina de estados: PASS (`NEW/READ/ACKNOWLEDGED/DISMISSED`, 409 en transiciones inválidas)
- Subscribers aislados: PASS (SAVEPOINT, `event.subscriber_failed`)
- Sin commit en subscribers: PASS
- Deep links aprobación: PASS
- Permisos viewer vs admin: PASS

---

## TESTS

| Métrica | Valor |
|---------|-------|
| Suite completa | **61 passed**, 0 failed, 0 skipped |
| Tests notificaciones | 13 passed |
| Tests nuevos (esta revisión) | 3 |
| Warnings | 1 (Starlette/httpx deprecation, no bloqueante) |

### Tests nuevos añadidos

- `test_update_rule_rejects_cross_tenant_recipient`
- `test_viewer_cannot_acknowledge_notification`
- `test_cross_tenant_alert_rule_returns_404`

### Tests existentes relevantes (PASS)

- Tenant isolation, permissions, recipient scope
- State transitions, subscriber failure isolation
- Approval alias normalization, dismiss cross-tenant
- Invalid login security event

---

## BUILD

```
npm run build — PASS (Vite, 55 módulos)
```

---

## NPM AUDIT

```
found 0 vulnerabilities
```

---

## GIT DIFF CHECK

```
git diff main --check — PASS (sin errores)
```

---

## MIGRACIÓN

Migración `820a1` (revises `5b2eb2437398`):

```
alembic upgrade head — PASS
alembic downgrade 5b2eb2437398 — PASS
alembic upgrade 820a1 — PASS
```

**Nota:** Head de rama es `820a1`. Integración con ramas posteriores (810, 830, 840, 850) requerirá merge de migraciones en integración controlada (fuera de alcance).

---

## RIESGOS RESIDUALES

1. **Permisos hardcoded** en esta rama (no integra modelo DB de PR #9) — aceptable para alcance PR #7.
2. **PUT completo en alert rules** (no PATCH parcial) — diseño V1 documentado; no borra campos no enviados porque reemplaza objeto completo con body obligatorio.
3. **Migración paralela** con otras ramas sobre `5b2eb2437398` — requiere merge Alembic al integrar.
4. **Warning httpx** en tests — cosmético.

---

## TABLA FINAL

| Control | Resultado |
|---------|-----------|
| PR #7 identificado correctamente | PASS |
| Alcance auditado | PASS |
| Backend | PASS |
| Frontend | PASS |
| Autorización | PASS |
| Tenant isolation | PASS |
| Persistencia | PASS |
| Migraciones | PASS |
| Pruebas adversariales | PASS |
| Suite completa relevante | PASS |
| Build | PASS |
| npm audit | PASS |
| git diff --check | PASS |
| Sin cambios fuera del alcance | PASS |
| Sin merge | PASS |

---

## RESTRICCIONES RESPETADAS

- No merge a `main`
- No modificados PR #6, #8, #9, #10
- Cambio mínimo acotado a PR #7
