# EMPLEADOS_IA — LIMPIEZA QUIRÚRGICA 1250A — AISLAMIENTO DE ESTADO ENTRE PRUEBAS

**Agente:** C
**Base:** `062db08`
**Rama:** `cursor/1250a-fix-aislamiento-tests`
**Fecha:** 2026-08-29

---

## 1. Fallos de contaminación iniciales (4)

| # | Test | Archivo | Orden colección | Esperado | Encontrado (suite larga) |
|---|------|---------|-----------------|----------|--------------------------|
| 1 | `test_t_tenant_05_inactive_org_api_returns_403` | `tests/test_p0_precertificacion_v1.py` | ~562 | `POST /api/platform/organizations` → 201 | 403 |
| 2 | `test_onboarding_success_creates_org_admin_and_bootstrap` | `tests/test_prerelease_v1_corrections.py` | ~576 | onboarding → 201 | 403 |
| 3 | `test_duplicate_slug_returns_409` | `tests/test_prerelease_v1_corrections.py` | ~578 | duplicado → 409 | 403 (fallo previo en create) |
| 4 | `test_07_inactive_org_blocks_ingestion` | `tests/test_senales_reales_1120.py` | ~649 | `POST .../status` INACTIVE → 200 | 403 |

**Roundtrip Alembic (excluido de esta tarea):**
`tests/test_admin_840b_v3.py::test_migration_roundtrip_upgrade_downgrade_upgrade` — P1 pendiente agente General.

### Reproducción

- **Aislados (DB fresca):** los 4 tests → **PASS**
- **Suite completa (DB compartida, sesión pytest):** los 4 → **FAIL** con 403 en APIs de plataforma
- **Confirmado:** contaminación entre pruebas, no defecto funcional aislado

---

## 2. Causa raíz

Los tests de notificaciones (`test_notifications_820.py`, `test_notifications_820_adversarial.py`) mutan temporalmente `admin.role` a `"operator"` para probar el bus de eventos, pero en el bloque `finally` restauraban **hardcodeado** a `"admin"`.

El usuario bootstrap `admin` se crea con rol **`superadmin`** (incluye permisos `platform.organization.*`). Tras los tests de notificaciones, quedaba persistido `admin.role = "admin"` (rol global sin permisos de plataforma).

Efecto en tests posteriores que usan el fixture `token` (login como `admin`):

- El JWT sigue siendo válido
- Las llamadas a `/api/platform/organizations` devuelven **403** por falta de permisos de plataforma
- No era contaminación de `organization.status` (la org bootstrap permanecía `ACTIVE`)

**Contaminante identificado:**

- `test_subscriber_failure_isolated_logged_and_later_subscriber_runs`
- `test_listener_commit_forbidden_and_savepoint_holds`
- `test_two_listeners_second_commit_fails_no_partial_persist`

---

## 3. Corrección aplicada

**Cambio producción:** NO

**Archivos modificados:**

- `tests/test_notifications_820.py`
- `tests/test_notifications_820_adversarial.py`

**Patrón:** capturar `original_role = admin.role` antes de la mutación y restaurar `original_role` en `finally` (incluso si falla una assertion).

La prueba `test_1200_empresa_inactiva` ya tenía `try/finally` para `organization.status` desde convergencia 1250A — no requirió cambios adicionales.

---

## 4. Pruebas de orden

| Escenario | Resultado |
|-----------|-----------|
| contaminante → afectados (6 tests) | PASS |
| afectados → contaminante (2 tests) | PASS |
| repetición conjunto | PASS |

---

## 5. Regresión

| Batería | Resultado |
|---------|-----------|
| 1200 completo (`test_bloque_1200_linea_base_impacto.py`) | **14/14 PASS** |
| Focales 1250A (74) | **74/74 PASS** |
| Convergencia 1250A (8) | **8/8 PASS** |
| Suite SQLite completa | **685 passed, 2 skipped, 1 failed** |
| Frontend `npm run build` | **PASS** |

**Único fallo restante:** `test_migration_roundtrip_upgrade_downgrade_upgrade` (P1 Alembic — pendiente General).

**Fallos de contaminación restantes:** **0**

---

## 6. P0 / P1 / P2 nuevos

| Severidad | Cantidad |
|-----------|----------|
| P0 nuevos | 0 |
| P1 nuevos | 0 |
| P2 nuevos | 0 |

---

## 7. Veredicto

**LIMPIO SALVO ROUNDTRIP**

NO MERGE (rama de corrección aislada; integrar vía convergencia cuando proceda).
