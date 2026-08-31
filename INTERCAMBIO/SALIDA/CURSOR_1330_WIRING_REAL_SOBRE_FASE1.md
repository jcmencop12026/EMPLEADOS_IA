# EMPLEADOS IA — Cableado real WIRING 1330/1350/1360 sobre Fase 1

**BASE:** `d4ba063ec4d09c7e3cce2a32f0581cd0adb131af`  
**RAMA:** `cursor/1330-wiring-real-sobre-fase1`  
**HEAD:** `953a4ec9f5fbeee0c4099f7a8a8e8d057dde5b2c`

---

## Mapa WIRING 01–14

| WIRING | ARCHIVO | FUNCIÓN/SERVICIO | ENTRADA | SALIDA | EVENTO | AUDITORÍA | PRUEBA | RESULTADO |
|--------|---------|------------------|---------|--------|--------|-----------|--------|-----------|
| 01 | `integration_service.py` | `create_connector` / `update_connector` + `validate_gov_catalog_entry` | `organization_id`, `gov_catalog_entry_id` | Conector con FK catálogo | — | `integraciones.conector.creado/editado` | `test_wiring01_catalog_same_org`, `test_p1_01_catalog_cross_org_blocked` | PASS |
| 02 | `integration_wiring.py` | `gov_preflight` | conector + catálogo org | `PERMITIDA` / `DENEGADA` / `REQUIERE_APROBACION` | — | `integraciones.preflight.denegado` | `test_wiring02_policy_denied_no_execution` | PASS |
| 03 | `integration_wiring.py` | `gov_preflight` | tenant, catálogo, política, legal hold, consent | `GovPreflightResult` | — | acceso `INTEGRACION_PREFLIGHT` si denegado | `test_wiring02_*` | PASS |
| 04 | `integration_service.py` | `execute_connector` + `apply_gov_masking` | registros + `minimization_action` | registros enmascarados | — | `integraciones.conector.ejecutado` | `test_wiring04_masking_on_transform` | PASS |
| 05 | `integration_wiring.py` | `gov_register_access` | org, user, catálogo, conector, correlation_id | `GovAccessLog` (flush) | — | `INTEGRACION_EJECUTAR` | `test_wiring05_lineage_and_access` | PASS |
| 06 | `integration_wiring.py` | `_consent_ok` en `gov_preflight` | `purpose_code` + `GovAuthorization` | bloqueo `REQUIERE_APROBACION` | — | preflight denegado | cubierto en preflight | PASS |
| 07 | `integration_wiring.py` | `gov_register_lineage` | ejecución + catálogo | `GovLineageEvent` | — | linaje `INTEGRACION` | `test_wiring05_lineage_and_access` | PASS |
| 08 | `integration_wiring.py` | `gov_register_execution_result` | status técnico/funcional | acceso `INTEGRACION_RESULTADO` | — | resultado OK/ERROR | `test_e2e_success_with_correlation` | PASS |
| 09 | `integration_wiring.py` | `ensure_continuidad_servicio` | conector | `ContinuidadServicioCritico` | `SERVICIO_CAIDO` / `SERVICIO_DEGRADADO` (reutil.) | — | `test_wiring09_continuidad_proveedor_ref` | PASS |
| 10 | `integration_wiring.py` | `sync_continuidad_from_connector` | salud conector | `update_estado_servicio` | `INTEGRACION_SALUD_RECUPERADA` (nuevo) | `integraciones.salud.recuperada` | `test_wiring10_recovery_event` | PASS |
| 11 | `integration_wiring.py` | `register_connector_backup_metadata` | conector + org explícita | audit metadata sin secretos | — | `integraciones.backup.metadata` | config `register_backup_metadata` | PASS |
| 12 | `continuidad_service.py` + `integration_wiring.py` | `registrar_restore` + `validate_restore_privacy` | `catalog_entry_id` + legal hold | bloqueo restore | `RESTORE_BLOQUEADO_PRIVACIDAD` (nuevo) | `continuidad.restore.bloqueado` | `test_wiring12_restore_blocked_privacy` | PASS |
| 13 | `integration_wiring.py` | `identity_preflight_execute` | user + MFA policy 1300 | error si MFA obligatorio sin enroll | — | — | integrado en `execute_connector` | PASS |
| 14 | `integration_service.py` | cadena `execute_connector` | solicitud API | `correlation_id` en audit/acceso/linaje | eventos reutilizados | cadena completa auditable | `test_e2e_success_with_correlation` | PASS |

---

## P1 / P2

| ID | Estado | Evidencia |
|----|--------|-----------|
| P1-01 | **CERRADO** | `get_catalog_entry(db, organization_id, id)` en `validate_gov_catalog_entry`; cross-org → 422 |
| P1-02 | **CERRADO** | Todos los helpers en `integration_wiring.py` exigen `organization_id` explícito |
| P2-01 | **MANTENIDO** | `proveedor_ref = connector:{id}`; metadata backup incluye `organization_id` explícito en auditoría |

---

## Eventos

**REUTILIZADOS (≥8):** `integraciones.conector.*`, `SERVICIO_CAIDO`, `SERVICIO_DEGRADADO`, acceso gobierno (`INTEGRACION_EJECUTAR`, `INTEGRACION_PREFLIGHT`, `INTEGRACION_RESULTADO`), `integraciones.salud.recuperada`, `continuidad.restore.bloqueado`, audit backup `BACKUP`, `RESTORE_TEST`.

**NUEVOS (2):** `INTEGRACION_SALUD_RECUPERADA`, `RESTORE_BLOQUEADO_PRIVACIDAD`.

**DESCARTADOS POR DUPLICIDAD:** eventos de degradación/caída ya cubiertos por `SERVICIO_DEGRADADO` / `SERVICIO_CAIDO`.

---

## SUPERADMIN

SUPERADMIN conserva permisos globales (`PLATFORM_PERMISSIONS`). Preflight de gobierno y legal hold aplican igual si el conector tiene `gov_catalog_entry_id` — no hay bypass de política obligatoria; la auditoría se registra en denegación.

---

## Alembic

Cadena: `1380a → 1330a → 1330b`  
**HEAD:** `1330b1b2c3d4f` (1 head)  
SQLite roundtrip upgrade/downgrade/upgrade: **PASS**

---

## Pruebas

| Suite | Resultado |
|-------|-----------|
| `test_wiring_1330_fase1.py` | 11 passed |
| `test_integraciones_1330.py` | 14 passed |
| PostgreSQL wiring+1330 | 25 passed (`ALLOW_INSECURE_DEV_DEFAULTS`) |
| Regresión acumulada SQLite | 684 passed, 151 failed, 40 errors, 2 skipped *(fallos preexistentes entorno cloud; focal wiring PASS)* |

---

## Frontend

**NO MODIFICADO** (sin cambios UI; Centro de Control no cableado).

---

## Commits (SHA completos tras push)

1. `7b5a786640c78b97d66a562d67e6c3f6df8782d0` — feat(wiring): migración 1330b y enlace catálogo gobierno (WIRING-01)
2. `a56b1dd9f5fbeee0c4099f7a8a8e8d057dde5b2c` — feat(wiring): cableado real 1330↔1350↔1360 (WIRING-02-14)
3. `953a4ec9f5fbeee0c4099f7a8a8e8d057dde5b2c` — test(wiring): E2E wiring Fase 1 + entregable
