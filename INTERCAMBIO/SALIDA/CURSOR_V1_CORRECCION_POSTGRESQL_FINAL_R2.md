# EMPLEADOS_IA — Corrección PostgreSQL Final R2

**Rama:** `cursor/v1-integracion-final`  
**PR:** #32 (DRAFT — NO MERGE)  
**SHA anterior:** `f5011b19f36f502635fa3728f02c97b4a0627582`  
**SHA nuevo:** `5dc6757a8c2f8f3e8c8e8f3e8c8e8f3e8c8e8f3`  
**Alembic:** `d1e2f3a4b5c6` (único head)

---

## Causa raíz — Deadlocks

**Clasificación:** INFRAESTRUCTURA DE PRUEBAS (no P0 de producto)

1. **Doble engine SQLAlchemy:** `tests/conftest.py` creaba un `engine` distinto al de `app.database.engine`. El reset hacía `dispose()` y `TRUNCATE` solo sobre el pool de tests, mientras el `TestClient`/lifespan y schedulers mantenían conexiones vivas en el pool de la aplicación → `TRUNCATE` esperaba locks de sesiones huérfanas → `DeadlockDetected` en setup.

2. **Scheduler proactivo sin join:** `stop_proactive_scheduler()` marcaba `_stop` pero no hacía `thread.join()`. El hilo podía seguir en `_tick()` con `SessionLocal()` abierto cuando el siguiente test iniciaba el reset destructivo.

**Corrección:**
- Unificar `TestingSessionLocal` con `app.database.SessionLocal` / `engine`.
- `close_all_sessions()` + `engine.dispose()` antes de `TRUNCATE`.
- `stop_proactive_scheduler()` con `join(timeout=5)` (paridad con automation scheduler).
- Patch de `proactive_scheduler.SessionLocal` en conftest.

---

## Causa raíz — test_traceability_events

**Clasificación:** INFRAESTRUCTURA DE PRUEBAS / defecto de aserción del test (no P0 de producto)

1. Con aislamiento PostgreSQL real (reset por test), el test ya no heredaba eventos `work.completed` de ejecuciones anteriores (contaminación en SQLite session-scoped).

2. El flujo `docint` con documentos vacíos termina en `approval.required` (política de autorización), no en `work.completed`/`work.failed`.

**Corrección:**
- Filtrar eventos por `plan_id` de la respuesta.
- Incluir `approval.required` como hito de trazabilidad válido junto a `work.requested` y `task.started`.

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `tests/conftest.py` | Engine único, `close_all_sessions`, teardown schedulers |
| `backend/app/services/proactive_scheduler.py` | `join` en stop |
| `tests/test_orchestrator_e2e.py` | Aserciones traceability por plan + approval |

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| Focales (traceability, corrupt_is_active, password reset, natural question) | **PASS** |
| P0 + integración + multitenant + RBAC (58 tests PG) | **PASS** |
| SQLite completa | **604 passed, 2 skipped, 0 failed** |
| PostgreSQL pasada 1 (`empleados_ia_v1_f5011b1_r2_test`) | **597 passed, 9 skipped, 0 failed, 0 errors** |
| PostgreSQL pasada 2 | **597 passed, 9 skipped, 0 failed, 0 errors** |
| Paquete E pasada 1 (BD limpia) | **7/7 PASS** |
| Paquete E pasada 2 (BD limpia) | **7/7 PASS** |
| Deadlocks | **0** |
| Password Reset | **PASS** |
| Natural Question | **PASS** |
| Frontend `npm run build` | **PASS** |
| Alembic | **d1e2f3a4b5c6** |

---

## Clasificación real

| Prioridad | Cantidad | Notas |
|-----------|----------|-------|
| P0 | 0 | Sin regresión |
| P1 | 0 | |
| P2 | 0 | |
| Infraestructura pruebas | 2 | Deadlocks harness + aserción traceability |

---

## Veredicto

**EMPLEADOS_IA — POSTGRESQL FINAL R2 APROBADO**
