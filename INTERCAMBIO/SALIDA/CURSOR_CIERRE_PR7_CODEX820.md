# CURSOR — Cierre técnico PR #7 / CODEX-820

**Fecha:** 2026-08-25
**Estado:** CORREGIDO Y LISTO PARA QA FINAL
**No declarado apto para merge — NO MERGE**

---

## IDENTIFICACIÓN

| Campo | Valor |
|-------|-------|
| PR | #7 |
| Título | CODEX-820: Centro de notificaciones y alertas V1 |
| Rama | `codex/notifications-alerts-820` |
| Base | `main` |
| HEAD inicial (remoto verificado) | `56d469863970415ae1372f11da31586d922b1e61` |
| HEAD final | *(ver commit de cierre en rama)* |

---

## COMMITS EN RAMA (respecto a `main`)

| SHA | Mensaje |
|-----|---------|
| `7a39539` | feat: add notifications and alerts center |
| `fca7893` | fix: close notifications audit findings |
| `04ae68a` | fix(820): validate alert rule recipient on update |
| `c3331cc` | docs: informe revisión técnica PR #7 (CODEX-820) |
| `16762dd` | fix(820): close Codex reaudit blockers for PR #7 |
| `56d4698` | docs(820): add CURSOR correction report for PR #7 Codex reaudit |
| *(cierre)* | fix(820): etiquetas UI en español en centro de notificaciones |

---

## CINCO DEFECTOS — REVISIÓN Y RESULTADO

| # | Defecto | Resultado | Evidencia |
|---|---------|-----------|-----------|
| 1 | Destinatario cross-tenant | **PASS** | `validate_notification_recipient()` en `notification_recipients.py`; tests adversariales `test_event_bus_cross_tenant_recipient_denied`, `test_emit_event_manipulated_recipient_cross_tenant_denied`, `test_update_rule_rejects_cross_tenant_recipient` |
| 2 | Listener `commit()` escapa SAVEPOINT | **PASS** | `SubscriberSession` prohíbe `commit()`, `rollback()`, `close()`; tests `test_listener_commit_forbidden_and_savepoint_holds`, `test_two_listeners_second_commit_fails_no_partial_persist` |
| 3 | Viewer decide aprobaciones vía deep link | **PASS** | `operations.approve` en backend; `approval_decide` exige permiso; frontend oculta acciones; tests `test_viewer_cannot_approve_or_reject`, `test_operator_can_decide_approval` |
| 4 | `/notificaciones` en blanco (`useEffect`) | **PASS** | Patrón `cancelled` + `void load()`; estados loading/error/empty; página siempre renderiza estructura |
| 5 | Eventos repetidos duplican notificaciones | **PASS** | `idempotency_key` + índice único migración `820a2`; tests secuencial, concurrente y multi-destinatario |

---

## VALIDACIÓN EJECUTADA

### Tests (`pytest`)

```
PYTHONPATH=backend python3 -m pytest -q
→ 73 passed
```

Incluye `tests/test_notifications_820.py` (13) y `tests/test_notifications_820_adversarial.py` (12).

### Migraciones SQLite (`820a1`, `820a2`)

```
alembic upgrade head
alembic downgrade 820a1
alembic upgrade head
→ PASS
```

### Frontend

```
npm run build → PASS
npm audit     → 0 vulnerabilities
```

### Git

```
git diff --check → PASS (sin conflictos de espacios en blanco)
```

---

## TEXTOS CORREGIDOS (español UI)

| Antes | Después |
|-------|---------|
| Tooltip `Acknowledge` | `Marcar como atendida` |
| Tooltip `Marcar leído` | `Marcar como leída` |
| Estados crudos `NEW/READ/...` en filtros y tabla | Etiquetas: Nueva, Leída, Atendida, Descartada |
| Severidades crudas `LOW/MEDIUM/...` | Etiquetas: Baja, Media, Alta, Crítica |

Archivo: `frontend/src/pages/NotificationsPage.tsx`

---

## POSTGRESQL REAL

**POSTGRESQL REAL NO CERTIFICADO** — solo validación SQLite en este entorno.

---

## ARQUITECTURA APLICADA (sin rehacer módulo)

```
Evento → bus.publish()
           └─ SAVEPOINT por subscriber
                └─ SubscriberSession(db)  ← sin commit/rollback/close
                     └─ handler

emit_event() / API / reglas
  └─ validate_notification_recipient()
  └─ _persist_notification() + idempotency_key

approval_decide
  └─ check_permission("operations.approve")
```

---

## ARCHIVOS CLAVE

| Área | Archivos |
|------|----------|
| Validación destinatario | `backend/app/notification_recipients.py` |
| Idempotencia | `backend/app/notifications.py`, `820a2_notification_idempotency.py` |
| Event bus | `backend/app/events/bus.py`, `subscriber_session.py` |
| Permisos aprobación | `backend/app/permissions.py`, `routers/operations.py` |
| Frontend | `frontend/src/pages/NotificationsPage.tsx`, `ExecutionDetailPage.tsx` |
| Migraciones | `820a1_notifications_alerts_v1.py`, `820a2_notification_idempotency.py` |

---

## ESTADO FINAL

**CORREGIDO Y LISTO PARA QA FINAL**

No se realizó merge. PRs #6, #8, #9 y #10 no fueron tocados.
