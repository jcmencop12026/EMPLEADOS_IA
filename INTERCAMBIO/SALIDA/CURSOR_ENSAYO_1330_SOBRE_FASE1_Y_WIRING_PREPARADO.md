# CURSOR — Ensayo 1330 sobre Fase 1 + wiring preparado

## Resumen ejecutivo

Ensayo real en rama aislada `cursor/ensayo-1330-sobre-fase1` (sin tocar `cursor/convergencia-final-post-v1-integracion`).

| Campo | Valor |
|-------|-------|
| **FASE1_HEAD_REAL** | `041209f4acabd595b5249c979a7e61031f598048` |
| **PORT 1330** | cherry-pick `4f802c44070d20e502f139e5313b9da5ff285452` |
| **Alembic** | `1380a1b2c3d4e` → `1330a1b2c3d4e` (1 head) |
| **WIRING implementado** | **NO** |
| **Veredicto** | **CANDIDATA TÉCNICA LISTA PARA FASE 2** (post gate Fase 1) |

---

## 1. Rama y genealogía

```
041209f (Fase 1 central — NO modificada)
    ↓
1faef42 PORT-1330-SOBRE-FASE1 (+ conflictos resueltos en mismo commit)
    ↓
commits posteriores: AJUSTES-CONFLICTOS, TESTS, DOC
```

**Rama central modificada:** NO  
**Merge:** NO

---

## 2. Conflictos reales (medición empírica)

Cherry-pick `4f802c4` sobre Fase 1 generó **9 conflictos** (coincide con receta teórica).

| Archivo | Tipo | Resolución | Riesgo funcional detectado |
|---------|------|------------|----------------------------|
| `backend/app/main.py` | CONFLICTO MANUAL | Imports + routers **1330 + 1350 + 1360 + identidad** | Ninguno tras merge |
| `backend/app/permissions.py` | CONFLICTO MANUAL | `DATOS_*` + `INTEGRATION_*` + roles | **SÍ** — faltó `PLATFORM_PERMISSIONS` en superadmin y `control_center.view` en operator/viewer → **corregido** |
| `backend/alembic/migration_ledger.json` | CONFLICTO MANUAL | `baseline_head=1330a` + todas las revisiones Fase 1 | Ninguno |
| `backend/scripts/schema_repair.py` | CONFLICTO MANUAL | `HEAD_REVISION=1330a1b2c3d4e` | Ninguno |
| `frontend/src/App.tsx` | CONFLICTO MANUAL | Rutas continuidad + integraciones | Ninguno |
| `frontend/src/AppShell.tsx` | CONFLICTO MANUAL | Menú ambos ítems | Ninguno |
| `frontend/src/api.ts` | CONFLICTO MANUAL | APIs 1360/1350 + 1330 | Ninguno |
| `frontend/src/auth/permissions.ts` | CONFLICTO MANUAL | Rutas continuidad + integraciones | Ninguno |
| `tests/conftest.py` | CONFLICTO MANUAL | Imports modelos todos los bloques | Ninguno |

**CONFLICTOS REALES:** 9  
**CONFLICTOS MANUALES:** 9  
**CONFLICTO AUTOMÁTICO RESUELTO:** 0 (todos requirieron edición explícita)

### Hub sin conflicto en este ensayo

Ninguno — los 9 hubs de la receta aparecieron.

---

## 3. Re-parent Alembic

```python
# backend/alembic/versions/1330a1b2c3d4e_integraciones_reales_conectores.py
down_revision = "1380a1b2c3d4e"
```

Cadena verificada (SQLite upgrade):

```
1250f → 1350a / 1360a → 1365a → 1300a → 1370a → 1380a → 1330a (head)
```

---

## 4. Preservación Fase 1

| Bloque | Tests focales | Estado |
|--------|---------------|--------|
| 1330 | `test_integraciones_1330` 14 | PASS |
| 1350 | `test_governance_1350` 28 | PASS |
| 1360 | `test_continuidad_1360` 22 | PASS |
| 1300 | `test_bloque_1300_seguridad_avanzada` | PASS |
| 1370 | `test_identidad_1370` | PASS |
| 1380 | `test_scim_1380` | PASS (tras actualizar head) |
| 1230 Centro Control | `test_bloque_1230_centro_control` | PASS (tras fix viewer) |
| 1240 Inteligencia Externa | en regresión | PASS |
| V1 puente | regresión acumulativa | PASS |

---

## 5. P1-01 — Cross-org catálogo gobierno

**Estado:** **RIESGO CONFIRMADO** (condición posible al implementar wiring) / **CORRECCIÓN DEFINIDA**

**Evidencia código combinado:**

- `governance_service.get_catalog_entry(db, organization_id, entry_id)` **ya filtra por org** (línea 269–273).
- `GovernanceConnectorAdapter.get_resource_policy(organization_id, catalog_entry_id)` **exige org**.
- `integration_service` **aún no enlaza** conector ↔ catálogo (`gov_catalog_entry_id` no existe en `IntegrationConnector`).

**Riesgo:** al implementar WIRING-01, si `create_connector` valida catálogo sin `get_catalog_entry(db, org_id, id)` → cross-org.

**Corrección wiring (no implementada):**

```python
# integration_service.create_connector / update_connector
entry = svc.get_catalog_entry(db, organization_id, data["gov_catalog_entry_id"])
if not entry:
    raise IntegrationValidationError("Catálogo gobierno no encontrado en esta organización")
```

**Test:** `test_connector_rejects_other_org_catalog`

---

## 6. P1-02 — `organization_id` en helpers cross-módulo

**Estado:** **CORRECCIÓN DEFINIDA** (helpers destino OK; origen 1330 pendiente)

### Tabla helpers destino (ya correctos)

| HELPER | ARCHIVO | FIRMA ACTUAL | FIRMA OBJETIVO | LLAMADORES (futuro) | TEST |
|--------|---------|--------------|----------------|---------------------|------|
| `get_catalog_entry` | `governance_service.py` | `(db, organization_id, entry_id)` | igual | WIRING-01, 02 | cross-org catalog |
| `get_connector_policy_view` | `governance_service.py` | `(db, organization_id, catalog_entry_id)` | igual | WIRING-02 | preflight policy |
| `get_resource_policy` | `governance_adapters.py` | `(organization_id, catalog_entry_id)` | igual | WIRING-02 | adapter |
| `record_access` | `governance_service.py` | `(db, organization_id, ...)` | igual | WIRING-05 | audit gov |
| `add_lineage_event` | `governance_service.py` | `(db, organization_id, user_id, data)` | igual | WIRING-05 | lineage |
| `apply_mask` | `governance_masking.py` | `(records, action)` | igual | WIRING-04 | masking |
| `update_estado_servicio` | `continuidad_service.py` | `(db, org_id, sid, estado, mensaje)` | igual | WIRING-07, 08 | health sync |
| `get_servicio` | `continuidad_service.py` | `(db, org_id, sid)` | igual | WIRING-09 | proveedor_ref |
| `create_servicio` | `continuidad_service.py` | `(db, org_id, data, user_id)` | igual | WIRING-09 | registro |

### Helpers origen a crear en 1330 (WIRING)

| HELPER (nuevo) | ARCHIVO | FIRMA OBJETIVO |
|----------------|---------|----------------|
| `_gov_preflight` | `integration_service.py` | `(db, organization_id, connector_row)` |
| `_apply_gov_masking` | `integration_service.py` | `(db, organization_id, records, minimization_action)` |
| `sync_continuidad_from_connector` | `integration_service.py` | `(db, organization_id, connector_row)` |
| `ensure_continuidad_servicio` | `integration_service.py` | `(db, organization_id, connector_id)` |

**Test transversal:** `test_cross_module_calls_require_organization_id`

---

## 7. P2-01 — `proveedor_ref`

**Estado:** **MANTENER P2** — sin fuga real en ensayo

- Formato propuesto: `connector:{connector_id}` (único por org porque `connector_id` es global UUID).
- `ContinuidadBackupEjecucion.recurso` es string libre sin prefijo org en API externa.
- Endurecimiento futuro: metadata `organization_id` en backup o prefijo `org:{org_id}:connector:{id}` en WIRING-11.

---

## 8. WIRING-01…14 — preparado contra código real

**NO IMPLEMENTADO.** Tabla resumen actualizada:

| ID | Archivo origen | Función origen | Archivo destino | Función destino | Campo/evento | Test exacto | Orden |
|----|----------------|----------------|-----------------|-----------------|--------------|-------------|-------|
| WIRING-01 | `integration_models.py` | columna nueva | `governance_models.py` | `GovCatalogEntry` | `gov_catalog_entry_id` FK nullable | `test_connector_rejects_other_org_catalog` | 1 |
| WIRING-01 | `integration_service.py` | `create_connector` | `governance_service.py` | `get_catalog_entry` | validación org | idem | 1 |
| WIRING-02 | `integration_service.py` | `execute_connector` | `governance_adapters.py` | `get_resource_policy` | preflight | `test_execute_blocked_by_gov_policy` | 2 |
| WIRING-03 | `integration_service.py` | `execute_connector` | `governance_service.py` | `get_connector_policy_view` | legal hold | `test_execute_blocked_under_legal_hold` | 2 |
| WIRING-04 | `integration_service.py` | post-mapping | `governance_masking.py` | `apply_mask` | PII | `test_execute_masks_email_fields` | 3 |
| WIRING-05 | `integration_service.py` | fin ejecución | `governance_service.py` | `record_access`, `add_lineage_event` | audit+linaje | `test_execute_creates_gov_access_log` | 4 |
| WIRING-06 | `integration_service.py` | `_gov_preflight` | `governance_service.py` | `list_authorizations` | consent | `test_execute_requires_consent_when_configured` | 7 |
| WIRING-07 | `integration_service.py` | `sync_continuidad_from_connector` | `continuidad_service.py` | `update_estado_servicio` | health | `test_health_sync_degrades_servicio` | 5 |
| WIRING-08 | `integration_service.py` | circuit open branch | `continuidad_service.py` | `_alerta` | SERVICIO_DEGRADADO | `test_circuit_opens_alerts_once` | 5 |
| WIRING-09 | `integration_service.py` | `ensure_continuidad_servicio` | `continuidad_service.py` | `create_servicio` | `proveedor_ref` | `test_continuidad_servicio_linked_by_proveedor_ref` | 5 |
| WIRING-10 | `continuidad_service.py` | purge/restore | `governance_service.py` | legal hold check | bloqueo | `test_restore_blocked_under_legal_hold` | 8 |
| WIRING-11 | `continuidad_service.py` | backup metadata | `governance_service.py` | retention policies | alineación | `test_backup_respects_retention_metadata` | 8 |
| WIRING-12 | `continuidad_service.py` | `registrar_restore` | `governance_service.py` | `evaluate_provider_export` | política | `test_restore_blocked_by_privacy_policy` | 8 |
| WIRING-13 | `IntegracionWizardPage.tsx` | selector catálogo | `api.ts` | `fetchGovCatalog` | UI | e2e wizard | 9 |
| WIRING-14 | `control_center_service.py` | agregador | — | JSON blocks | sin nuevo dashboard | `test_centro_control_integraciones_block` | 10 |

### Orden confirmado

```
01–05 (1330↔1350 core)
→ 07–09 (1330↔1360)
→ 06 (consent condicional)
→ 10–12 (1350↔1360)
→ 13 (UI)
→ 14 (Centro Control datos)
```

Sin cambio respecto a receta teórica — dependencias técnicas iguales con código real.

---

## 9. Gobierno 1330↔1350 (modelos reales)

**Confirmado:** añadir `gov_catalog_entry_id` nullable FK → `gov_catalog_entries.id` en `integration_connectors` (migración `1330b` o columna en re-parent futuro).

**NO duplicar catálogo** — solo FK a `GovCatalogEntry` existente.

Adaptador existente: `GovernanceConnectorAdapter` en `governance_adapters.py` — listo para WIRING-02.

---

## 10. Continuidad 1330↔1360 (código real)

| Elemento | Valor real |
|----------|------------|
| Endpoint salud | `POST /api/continuidad/servicios/{id}/reportar-salud` |
| Servicio | `continuidad_service.update_estado_servicio` |
| `proveedor_ref` | `connector:{connector_id}` |
| Estados | `EstadoOperacional`: DISPONIBLE, DEGRADADO, NO_DISPONIBLE |
| Eventos existentes | `SERVICIO_CAIDO`, `SERVICIO_DEGRADADO` ( `_alerta` ) |
| Evento nuevo | `INTEGRACION_SALUD_RECUPERADA` — **necesario** solo si recuperación sin duplicar degradado |

---

## 11. Gobierno 1350↔1360 — estados propuestos

| Estado propuesto | Verificación código real |
|------------------|-------------------------|
| `RETENIDO_LEGALMENTE` | **YA EXISTE** equivalente: `GovLegalHold` activo + catálogo `status` |
| `BORRADO_PENDIENTE_BACKUP` | **CAMBIO NECESARIO** — no en modelos |
| `PURGA_DIFERIDA` | **CAMBIO NECESARIO** — usar workflow retención + backup `estado_registro` |
| `RESTAURADO_PENDIENTE_VALIDACION` | **CAMBIO NECESARIO** — `ContinuidadRestorePrueba` sin este estado |

---

## 12. Eventos (código combinado)

### 8 reutilizables (confirmados)

1. `integraciones.conector.creado` / `editado` / `ejecutado` / `probado`
2. `SERVICIO_CAIDO` (`continuidad_service._alerta`)
3. `SERVICIO_DEGRADADO` (idem)
4. `gov.access` (vía `record_access`)
5. `gov.legal_hold.create` / `release`
6. Audit continuidad `RESTORE_TEST`
7. Incidente continuidad (audit interno)
8. `integraciones.conector.ejecutado` (audit global — mantener)

### 2 nuevos realmente necesarios

| Evento | ¿Duplica existente? | Veredicto |
|--------|---------------------|-----------|
| `INTEGRACION_SALUD_RECUPERADA` | No hay equivalente explícito recuperación | **NECESARIO** (WIRING-07) |
| `RESTORE_BLOQUEADO_PRIVACIDAD` | No hay evento restore bloqueado | **NECESARIO** (WIRING-10/12) |

---

## 13. Centro de Control — datos futuros (sin implementar)

Bloques JSON para agregador 1230 tras WIRING-14:

- `integraciones`: conectores degradados/caídos, circuit open, ejecuciones fallidas
- `gobierno_datos`: legal holds activos, retención vencida, solicitudes abiertas
- `continuidad`: servicios NO_DISPONIBLE/DEGRADADO vinculados a conectores
- `acciones_pendientes`: purga diferida, restore pendiente validación

---

## 14. Resultados de pruebas

| Suite | Resultado |
|-------|-----------|
| Focales 1330 | 14 passed |
| Focales 1350+1360+1300+1370+1380 | 117 passed (módulos) |
| Regresión completa | **891 passed, 4 skipped, 0 failed** (tras fixes permissions) |
| SQLite Alembic | PASS (1 head `1330a1b2c3d4e`) |
| PostgreSQL Alembic | PASS (`empleados_ia_ensayo_test`) |
| PostgreSQL focales 1330 | 14 passed |
| Frontend build | PASS |
| Multiempresa 1330 | PASS (`test_rbac_and_tenant_isolation`) |
| RBAC / SUPERADMIN | PASS (tras `PLATFORM_PERMISSIONS` + `control_center.view`) |
| Secretos | PASS (`test_audit_no_secrets`) |

---

## 15. Commits en rama ensayo

| Commit | Mensaje | Contenido |
|--------|---------|-----------|
| `1faef42` | PORT-1330-SOBRE-FASE1 | Cherry-pick funcional + resolución conflictos + re-parent |
| *(siguiente)* | fix(permissions): restaurar PLATFORM y control_center en merge | `permissions.py` |
| *(siguiente)* | test(1380): head Alembic 1330a tras portado | `test_scim_1380.py` |
| *(siguiente)* | docs: ensayo 1330 sobre Fase 1 + wiring preparado | este entregable |

---

## 16. Inicio wiring (post gate Fase 1)

Ejecutar **solo cuando** General certifique gate Fase 1:

1. Mergear rama ensayo (o cherry-pick commits selectivos) a rama de convergencia oficial.
2. Implementar WIRING-01…14 según orden §8.
3. Cerrar P1-01 y P1-02 con tests.
4. Regresión + roundtrip + build.

---

## SALIDA FINAL

```
EMPLEADOS IA — ENSAYO 1330 SOBRE FASE 1 TERMINADO

FASE1 HEAD REAL:
041209f4acabd595b5249c979a7e61031f598048

RAMA:
cursor/ensayo-1330-sobre-fase1

PORT 1330:
4f802c44070d20e502f139e5313b9da5ff285452

ALEMBIC:
1380 → 1330

ALEMBIC HEADS:
1

ALEMBIC HEAD:
1330a1b2c3d4e

CONFLICTOS REALES:
9

CONFLICTOS MANUALES:
9

1330:
PASS

1360 PRESERVADO:
PASS

1350 PRESERVADO:
PASS

1300 PRESERVADO:
PASS

1370 PRESERVADO:
PASS

1380 PRESERVADO:
PASS

MULTIEMPRESA:
PASS

RBAC:
PASS

SUPERADMIN:
PASS

P1-01:
RIESGO CONFIRMADO / CORRECCIÓN DEFINIDA

P1-02:
CORRECCIÓN DEFINIDA

P2-01:
MANTENER P2

WIRING 01–14:
PREPARADO CONTRA CÓDIGO REAL

WIRING IMPLEMENTADO:
NO

EVENTOS REUTILIZABLES:
8

EVENTOS NUEVOS REALMENTE NECESARIOS:
2

SQLITE:
PASS

POSTGRESQL:
PASS

REGRESIÓN:
891 passed / 4 skipped / 0 failed / 0 errors

FRONTEND:
PASS

P0:
0

P1:
0 (abiertos en pieza; 2 riesgos wiring documentados)

P2:
1 (P2-01 documentado)

RAMA CENTRAL MODIFICADA:
NO

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

MERGE:
NO

VEREDICTO:
CANDIDATA TÉCNICA LISTA PARA FASE 2
```

---

*Ensayo aislado — no constituye Fase 2 oficial hasta gate independiente.*
