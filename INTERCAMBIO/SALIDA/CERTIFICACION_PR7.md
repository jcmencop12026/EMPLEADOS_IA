# CERTIFICACIÓN PR #7 — Notificaciones y Alertas (CODEX-820)

**Estado:** `LISTO PARA CERTIFICACIÓN GITHUB`  
**Rama:** `codex/notifications-alerts-820`  
**HEAD inicial:** `b7f36ba`  
**HEAD final:** `2e575d8`  
**NO MERGE**

---

## Tests agregados

| Archivo | Descripción |
|---------|-------------|
| `tests/certification/test_notifications_certification.py` | Suite permanente 11 casos obligatorios |
| `tests/certification/__init__.py` | Paquete certificación |
| `pytest.ini` | Markers `certification`, `notifications`, `tenant`, `auth`, `operations`, `concurrency`, `postgresql` |

## Defectos históricos cubiertos

| # | Vector | Test |
|---|--------|------|
| 1 | Recipient cross-tenant | `test_cert_01_recipient_cross_tenant_denied` |
| 2 | Recipient inexistente | `test_cert_02_recipient_inexistente_denied` |
| 3 | SubscriberSession commit/rollback/close | `test_cert_03_subscriber_session_sin_control_transaccion` |
| 4 | SAVEPOINT dos listeners | `test_cert_04_savepoint_dos_listeners_sin_persistencia_parcial` |
| 5 | Viewer approve → 403 | `test_cert_05_viewer_approve_403` |
| 6 | Viewer reject → 403 | `test_cert_06_viewer_reject_403` |
| 7 | Deep link no concede permisos | `test_cert_07_deep_link_no_concede_permisos` |
| 8 | Idempotencia secuencial | `test_cert_08_idempotencia_secuencial` |
| 9 | Idempotencia concurrente | `test_cert_09_idempotencia_concurrente` |
| 10 | Retry IntegrityError | `test_cert_10_retry_integrity_sin_duplicacion` |
| 11 | API `/api/notificaciones` | `test_cert_11_api_notificaciones_list` |

## Resultados

### Certificación rápida

```bash
PYTHONPATH=backend:. pytest -m "certification and notifications" -q
```

**11 passed**

### Suite notificaciones completa

```bash
PYTHONPATH=backend:. pytest tests/test_notifications_820.py tests/test_notifications_820_adversarial.py tests/certification/ -q
```

**36 passed**

### Suite completa

```bash
PYTHONPATH=backend:. pytest -q
```

**84 passed**

### Migraciones

```bash
cd backend && PYTHONPATH=. alembic upgrade head
```

**PASS** (`820a1` → `820a2` idempotency)

### Build / audit / Git

| Comando | Resultado |
|---------|-----------|
| `npm run build` | PASS |
| `npm audit` | 0 vulnerabilities |
| `git diff --check` | PASS |

## Frontend `/notificaciones`

- Vista implementada: `NotificationsPage.tsx`, ruta `/notificaciones`
- **No existe suite frontend automatizada** (sin Vitest/Jest en proyecto)
- Control: `npm run build` PASS
- Limitación documentada — no se inventó framework nuevo

## PostgreSQL

- Local: sin `DATABASE_URL` PostgreSQL — tests de persistencia usan SQLite en suite focal.
- En GitHub (QA-INFRA #12, servicio `postgres:16`):

```bash
DATABASE_URL=postgresql+psycopg2://empleados_test:empleados_test@localhost:5432/empleados_ia_test \
  PYTHONPATH=backend:. pytest -m "certification and notifications" -v
```

## Comandos GitHub (post QA-INFRA #12 en main)

```bash
# Certificación rápida por PR
PYTHONPATH=backend:. pytest -m "certification and notifications" -v

# Grupo focal notifications (workflow existente)
pytest -m notifications -v
```

No duplicar `.github/workflows/qa.yml` en esta rama — ampliar QA-INFRA cuando #12 esté en `main`.

## Corrección aplicada durante certificación

- `test_cert_09_idempotencia_concurrente`: deadlock por `future.result()` secuencial en list comprehension; corregido enviando ambos futures antes de `result()`.

## Commits

| SHA | Mensaje |
|-----|---------|
| `efd30a5` | `docs(cert): informe CERTIFICACION_PR7 completo` |
| `c4f7871` | `test(cert): suite permanente notificaciones PR #7` |

## Pendientes

- Integrar `pytest -m "certification and notifications"` en workflow QA-INFRA tras merge de #12.
- Tests PostgreSQL dedicados para idempotencia multi-conexión (opcional).
- E2E browser `/notificaciones` (opcional futuro).

---

**LISTO PARA CERTIFICACIÓN GITHUB — NO MERGE**
