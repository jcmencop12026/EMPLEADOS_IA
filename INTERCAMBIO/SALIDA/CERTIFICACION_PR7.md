# CERTIFICACIÓN PR #7 — Notificaciones y Alertas (CODEX-820)

**Estado:** `LISTO PARA CERTIFICACIÓN GITHUB`  
**Rama:** `codex/notifications-alerts-820`  
**HEAD inicial:** `b7f36ba`  
**NO MERGE**

---

## Tests agregados

| Archivo | Descripción |
|---------|-------------|
| `tests/certification/test_notifications_certification.py` | Suite permanente 11 casos obligatorios |
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
pytest -m "certification and notifications"
```

**11 passed**

### Suite notificaciones completa

```bash
pytest tests/test_notifications_820.py tests/test_notifications_820_adversarial.py tests/certification/ -q
```

**36 passed**

### Suite completa

```bash
pytest -q
```

**84 passed**

### Migraciones

```bash
cd backend && PYTHONPATH=. alembic upgrade head
```

**PASS** (`820a1` → `820a2` idempotency)

### Build / audit

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

Tests `@pytest.mark.postgresql` pendientes de fixture dedicada. En GitHub (QA-INFRA #12):

```bash
DATABASE_URL=postgresql+psycopg2://... pytest -m "certification and notifications and postgresql"
```

## Comandos GitHub (post QA-INFRA #12 en main)

```bash
pytest -m "certification and notifications" -v
pytest -m notifications -v
```

## Commits

- (actualizar tras push)

## Pendientes

- Restaurar `.github/workflows/qa.yml` cuando #12 esté en main (no duplicado en esta rama)
- Tests PostgreSQL dedicados para idempotencia multi-conexión
- E2E browser `/notificaciones` (opcional futuro)

---

**LISTO PARA CERTIFICACIÓN GITHUB — NO MERGE**
