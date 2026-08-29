# CURSOR — Receta quirúrgica de cableado 1330 / 1350 / 1360

## Resumen

Documento de **diseño ejecutable** derivado del mapa cerrado (`CURSOR_MAPA_INTEGRACION_1330_1350_1360.md`). Convierte los **14 puntos de wiring** en instrucciones implementables sin decisión arquitectónica ad hoc.

**Base oficial:** `cursor/base-puente-v1-post-v1` — HEAD remoto `4b67183`, funcional `d57b831` (Alembic head `1250f1a2b3c4d`).

**NO se ha modificado código. NO convergencia.**

---

## 1. Inventario WIRING-01 … WIRING-14

### Resumen por pareja

| Pareja | IDs | n |
|--------|-----|---|
| 1330 ↔ 1350 | WIRING-01 … 06, 13 | **7** |
| 1330 ↔ 1360 | WIRING-07 … 09 | **3** |
| 1350 ↔ 1360 | WIRING-10 … 12 | **3** |
| Centro Control | WIRING-14 | **1** |

---

### WIRING-01 — Enlace conector ↔ catálogo gobierno

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 `IntegrationConnector` |
| **Destino** | 1350 `GovCatalogEntry` |
| **Archivo origen** | `backend/app/integration_models.py`, `schemas_integration.py` |
| **Archivo destino** | `backend/app/governance_models.py` (`gov_catalog_entries`) |
| **Servicio** | `integration_service.create_connector` / `update_connector` |
| **Modelo** | Nueva columna nullable `gov_catalog_entry_id` FK → `gov_catalog_entries.id` (migración al insertar 1330 post-Fase 1) |
| **Endpoint** | `POST/PUT /api/integraciones/conectores` acepta `gov_catalog_entry_id` |
| **Evento** | `integraciones.conector.creado` / `editado` (ya existe) |
| **Permiso** | `integraciones.create` + validación entry con `datos.view` implícita al enlazar |
| **Tenant** | `get_catalog_entry(db, organization_id, entry_id)` — **obligatorio** |
| **Comportamiento** | Si se envía `gov_catalog_entry_id`, validar que pertenece a `organization_id` del conector; si no existe → 422. Si no se envía, conector opera sin gobierno (modo degradado documentado). |
| **Prueba** | `test_connector_links_gov_catalog_same_org`; `test_connector_rejects_other_org_catalog` (**P1-01**) |
| **Severidad si falta** | **P1** (cruce tenant) |

**P1 asociado:** **P1-01**

---

### WIRING-02 — Preflight gobierno antes de ejecutar

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 `integration_service.execute_connector` |
| **Destino** | 1350 `GovernanceConnectorAdapter.get_resource_policy` |
| **Archivo origen** | `backend/app/services/integration_service.py` |
| **Archivo destino** | `backend/app/services/governance_adapters.py` → `governance_service.get_connector_policy_view` |
| **Servicio** | Nuevo helper interno `_gov_preflight(db, org_id, connector_row)` |
| **Modelo** | Lee `connector.gov_catalog_entry_id` |
| **Endpoint** | Indirecto: `POST /api/integraciones/conectores/{id}/ejecutar` |
| **Evento** | Ninguno nuevo; audit en WIRING-05 |
| **Permiso** | `integraciones.execute` (ya) |
| **Tenant** | `organization_id` en adapter y `_get_connector` |
| **Comportamiento** | Si hay `gov_catalog_entry_id`, cargar `ConnectorPolicyView`; si `provider_decision == DENEGADO` o restricción legal hold → **BLOQUEAR** ejecución con 422 claro. |
| **Prueba** | `test_execute_blocked_by_gov_policy`; `test_execute_without_catalog_skips_preflight` |
| **Severidad si falta** | **P1** (política ignorada) |

**P1 asociado:** **P1-02** (si omiten `organization_id` en llamada)

---

### WIRING-03 — Enforcement legal hold y export DENEGADO

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 ejecución / webhook |
| **Destino** | 1350 `GovLegalHold`, `evaluate_provider_export` |
| **Archivo origen** | `integration_service.py` (`execute_connector`, `receive_webhook`) |
| **Archivo destino** | `governance_service.py` (ya en `get_connector_policy_view`) |
| **Servicio** | Parte de `_gov_preflight` |
| **Modelo** | `gov_legal_holds`, `gov_provider_policies` |
| **Endpoint** | `/ejecutar`, `/webhook/{id}` |
| **Evento** | Reutilizar restricción en audit detail; hallazgo gov si bypass intentado |
| **Permiso** | `integraciones.execute` |
| **Tenant** | Holds filtrados por `organization_id` |
| **Comportamiento** | Legal hold activo → **BLOQUEAR**. DENEGADO export → **BLOQUEAR** salida externa. |
| **Prueba** | `test_execute_blocked_under_legal_hold`; `test_webhook_blocked_under_legal_hold` |
| **Severidad si falta** | **P0** si hold ignorado en producción |

---

### WIRING-04 — Minimización / enmascaramiento en salida

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 registros mapeados post-ejecución |
| **Destino** | 1350 `governance_masking.apply_mask` |
| **Archivo origen** | `integration_service.py` (tras `apply_mapping`, antes de señales/respuesta) |
| **Archivo destino** | `backend/app/services/governance_masking.py` |
| **Servicio** | `_apply_gov_masking(records, minimization_action)` |
| **Modelo** | N/A (transformación en memoria) |
| **Endpoint** | Respuesta de `/ejecutar` no expone PII en claro |
| **Evento** | N/A |
| **Permiso** | N/A |
| **Tenant** | Solo records del `organization_id` actual |
| **Comportamiento** | Si política `PERMITIDO_CON_TRANSFORMACIÓN`, aplicar `apply_mask` según `minimization_action`; si falla algoritmo → **BLOQUEAR** (no **CONTINUAR** con datos crudos). |
| **Prueba** | `test_execute_masks_email_fields`; `test_mask_failure_blocks_export` |
| **Severidad si falta** | **P1** (secreto/PII en payload) |

---

### WIRING-05 — Auditoría y linaje gobierno post-ejecución

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 ejecución exitosa/parcial |
| **Destino** | 1350 `record_access`, `add_lineage_event` |
| **Archivo origen** | `integration_service.py` (fin de `execute_connector`) |
| **Archivo destino** | `governance_service.py` |
| **Servicio** | `record_access(..., action="INTEGRACION_EJECUTAR")`; `add_lineage_event(step_type="INTEGRACION")` |
| **Modelo** | `gov_access_logs`, `gov_lineage_events` |
| **Endpoint** | N/A (side effect) |
| **Evento** | `gov.access` vía `record_access`; audit global `integraciones.conector.ejecutado` **se mantiene** |
| **Permiso** | N/A |
| **Tenant** | `organization_id` en ambas llamadas |
| **Comportamiento** | Siempre registrar acceso si hay `gov_catalog_entry_id`; linaje con `execution_id`, conteos valid/rejected. |
| **Prueba** | `test_execute_creates_gov_access_log`; `test_execute_creates_lineage_event` |
| **Severidad si falta** | **P1** (pérdida auditoría/linaje) |

---

### WIRING-06 — Consentimiento / autorización por purpose

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 preflight |
| **Destino** | 1350 `GovAuthorization` |
| **Archivo origen** | `integration_service._gov_preflight` |
| **Archivo destino** | `governance_service.list_authorizations` / nueva `check_authorization_for_purpose` |
| **Servicio** | Consulta autorización `VIGENTE` con `purpose` alineado a `purpose_code` del catálogo |
| **Modelo** | `gov_authorizations` |
| **Endpoint** | Opcional flag en catálogo gov `requires_authorization` (org policy) |
| **Evento** | N/A |
| **Permiso** | N/A |
| **Tenant** | `organization_id` |
| **Comportamiento** | Si catálogo exige purpose y no hay auth vigente → **BLOQUEAR**; si auth opcional no configurada → **CONTINUAR** con warning en audit detail. |
| **Prueba** | `test_execute_requires_consent_when_configured`; `test_execute_without_consent_requirement` |
| **Severidad si falta** | **P2** (solo si org exige consentimiento) |

---

### WIRING-07 — Sincronización health → continuidad

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 `get_health` / estado tras ejecución |
| **Destino** | 1360 `update_estado_servicio` vía `reportar-salud` |
| **Archivo origen** | `integration_service.py` — nuevo `sync_continuidad_from_connector` |
| **Archivo destino** | `continuidad_service.py` (`update_estado_servicio`) |
| **Servicio** | Mapeo health → `EstadoOperacional` |
| **Modelo** | `ContinuidadServicioCritico` (vía WIRING-09) |
| **Endpoint** | Interno; expone mismo estado en `GET /salud` |
| **Evento** | Reutilizar `SERVICIO_CAIDO` / `SERVICIO_DEGRADADO` (no duplicar) |
| **Permiso** | N/A (sistema) |
| **Tenant** | `organization_id` en servicio y conector |
| **Comportamiento** | Tras ejecución o cambio circuit: `circuit_open` o `NO_DISPONIBLE` → reportar; recuperación → `DISPONIBLE`. |
| **Prueba** | `test_health_sync_degrades_servicio`; `test_health_sync_recovers_servicio` |
| **Severidad si falta** | **P2** (continuidad manual) |

---

### WIRING-08 — Circuit breaker → alerta continuidad

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 `circuit_open_until`, `consecutive_failures` |
| **Destino** | 1360 `_alerta` / incidente opcional |
| **Archivo origen** | `integration_service.execute_connector` (rama fallo) |
| **Archivo destino** | `continuidad_service.py` |
| **Servicio** | Al abrir circuit: `update_estado_servicio(DEGRADADO)`; si threshold crítico → crear incidente SEV3 |
| **Modelo** | `cont_alertas`, `cont_incidentes` |
| **Endpoint** | N/A |
| **Evento** | **REUTILIZAR** `SERVICIO_DEGRADADO`; incidente `INCIDENTE` audit |
| **Permiso** | N/A |
| **Tenant** | `organization_id` |
| **Comportamiento** | No emitir evento nuevo si `_alerta` ya creó alerta para mismo `servicio_id` en ventana 5 min (evitar duplicados). |
| **Prueba** | `test_circuit_opens_alerts_once`; `test_incident_created_on_critical_failures` |
| **Severidad si falta** | **P2** |

---

### WIRING-09 — Mapping conector ↔ servicio crítico (`proveedor_ref`)

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 `IntegrationConnector.id` |
| **Destino** | 1360 `ContinuidadServicioCritico.proveedor_ref` |
| **Archivo origen** | `integration_service.ensure_continuidad_servicio` (nuevo) |
| **Archivo destino** | `continuidad_models.py`, `continuidad_service.create_servicio` |
| **Servicio** | Al activar conector: crear o resolver servicio con `proveedor_ref=f"connector:{connector_id}"` |
| **Modelo** | `cont_servicios_criticos` |
| **Endpoint** | `POST /conectores` opcional `register_continuidad: true` |
| **Evento** | N/A |
| **Permiso** | `continuidad.manage` si creación automática |
| **Tenant** | Servicio con mismo `organization_id`; búsqueda `proveedor_ref` **scoped por org** |
| **Comportamiento** | **Usar `connector_id` UUID** — no inventar otro id. Formato canónico: `connector:{id}`. |
| **Prueba** | `test_servicio_created_with_proveedor_ref`; `test_resolve_servicio_by_proveedor_ref` |
| **Severidad si falta** | **P2** (P2-01 colisión externa backup) |

**P2 asociado:** **P2-01**

---

### WIRING-10 — Legal hold bloquea purge/restore backup

| Campo | Detalle |
|-------|---------|
| **Origen** | 1350 `GovLegalHold` activo |
| **Destino** | 1360 `registrar_restore`, futura purge |
| **Archivo origen** | `continuidad_service.registrar_restore` |
| **Archivo destino** | `governance_service` — nuevo `assert_no_legal_hold_on_resource` |
| **Servicio** | Antes de restore: resolver `recurso`/`servicio_id` → `gov_catalog_entry_id` si mapeado |
| **Modelo** | `gov_legal_holds`, `cont_backup_ejecuciones` |
| **Endpoint** | `POST /api/continuidad/backups/restores` |
| **Evento** | **NUEVO** `RESTORE_BLOQUEADO_PRIVACIDAD` en `cont_alertas` (o reutilizar alerta genérica con tipo explícito) |
| **Permiso** | `backups.*` / `continuidad.manage` |
| **Tenant** | Hold por `organization_id` |
| **Comportamiento** | Hold activo en entry relacionada → **BLOQUEAR** restore real; simulada permitida con audit. |
| **Prueba** | `test_restore_blocked_under_legal_hold`; `test_simulated_restore_allowed_with_hold` |
| **Severidad si falta** | **P0** |

---

### WIRING-11 — Alineación retención gov ↔ backup

| Campo | Detalle |
|-------|---------|
| **Origen** | 1350 `GovRetentionPolicy` |
| **Destino** | 1360 `ContinuidadBackupPolitica.retencion_dias` |
| **Archivo origen** | `continuidad_service.create_politica_backup` |
| **Archivo destino** | `governance_service.retention_to_dict` |
| **Servicio** | Al crear política backup con `gov_catalog_entry_id` o `recurso` vinculado, calcular `retencion_dias` desde policy gov |
| **Modelo** | `gov_retention_policies`, `cont_backup_politicas` |
| **Endpoint** | `POST /backups/politicas` |
| **Evento** | N/A |
| **Permiso** | `continuidad.manage`, `datos.retention` |
| **Tenant** | Org en ambos |
| **Comportamiento** | Si gov `disposition` exige retención mayor → usar máximo; si conflicto → **ALERTAR** hallazgo gov `RETENCION_DIVERGENTE` (nuevo finding type en scan, no evento bus). |
| **Prueba** | `test_backup_retention_aligns_with_gov_policy`; `test_retention_mismatch_raises_finding` |
| **Severidad si falta** | **P1** |

---

### WIRING-12 — Restore validado contra política privacidad

| Campo | Detalle |
|-------|---------|
| **Origen** | 1360 restore |
| **Destino** | 1350 `evaluate_provider_export` |
| **Archivo origen** | `continuidad_service.registrar_restore` |
| **Archivo destino** | `governance_service.evaluate_provider_export` |
| **Servicio** | Gate pre-restore: clasificación restringida → **BLOQUEAR** restore REAL |
| **Modelo** | N/A |
| **Endpoint** | `POST /backups/restores` |
| **Evento** | `RESTORE_BLOQUEADO_PRIVACIDAD` (compartido con WIRING-10) |
| **Permiso** | backups + datos |
| **Tenant** | Org |
| **Comportamiento** | Restore que reintroduce datos clasificados sin transformación → **BLOQUEAR** + audit gov + cont. |
| **Prueba** | `test_restore_blocked_by_classification`; `test_restore_audit_dual` |
| **Severidad si falta** | **P0** |

---

### WIRING-13 — UI wizard: selector catálogo gobierno

| Campo | Detalle |
|-------|---------|
| **Origen** | Frontend `IntegracionWizardPage` |
| **Destino** | `GET /api/gobierno-datos/catalogo` |
| **Archivo origen** | `frontend/src/pages/IntegracionWizardPage.tsx` |
| **Archivo destino** | `frontend/src/api.ts` (`fetchGovCatalog` si 1350 integrado) |
| **Servicio** | N/A |
| **Modelo** | N/A |
| **Endpoint** | API gobierno catálogo |
| **Evento** | N/A |
| **Permiso** | `datos.view` para mostrar selector; `integraciones.create` para guardar |
| **Tenant** | Catálogo filtrado por org del usuario |
| **Comportamiento** | Dropdown opcional “Fuente de datos (gobierno)”; envía `gov_catalog_entry_id`. |
| **Prueba** | E2E o componente: selector visible con permiso |
| **Severidad si falta** | **P2** (solo UX) |

---

### WIRING-14 — Centro Control: agregadores tríada

| Campo | Detalle |
|-------|---------|
| **Origen** | 1330 health, 1350 dashboard, 1360 tablero |
| **Destino** | 1230 `control_center_service` / adapters |
| **Archivo origen** | `integration_service.list_connectors_summary`; `governance_service.dashboard_summary`; `continuidad_service.centro_control_resumen` |
| **Archivo destino** | `backend/app/services/control_center_adapters.py` (extensión) |
| **Servicio** | Nuevas funciones adapter sin nuevo dashboard |
| **Modelo** | N/A |
| **Endpoint** | `GET /api/centro-control/resumen-ejecutivo` (enriquecido) |
| **Evento** | N/A |
| **Permiso** | `control_center.view` |
| **Tenant** | Todas las consultas con `user.organization_id` |
| **Comportamiento** | Añadir bloques JSON: `integraciones`, `gobierno_datos`, `continuidad` (ver sección 13). |
| **Prueba** | `test_centro_control_includes_tríada_blocks` |
| **Severidad si falta** | **P2** |

---

## 2. 1330 → 1350 — Implementación `GovernanceConnectorAdapter`

### Decisión: dónde almacenar `catalog_entry_id`

| Opción | Veredicto |
|--------|-----------|
| Duplicar catálogo en `integration_connectors` | **NO** |
| Solo `config_json` sin FK | **NO** (sin integridad referencial) |
| **Columna nullable `gov_catalog_entry_id` FK** en `integration_connectors` | **SÍ** |

**Migración:** incluir en revisión `1330a1b2c3d4e` al reparent post-Fase 1 (ALTER ADD COLUMN), no en Fase 1 de D.

**Resolución sin catálogo:** conector sin FK → preflight omitido; audit warning `gov_preflight_skipped: no_catalog_link`.

### Necesidad real por capacidad

| Capacidad | ¿Necesario? | Wiring |
|-----------|-------------|--------|
| `catalog_entry_id` | **SÍ** | WIRING-01 |
| `apply_mask` | **SÍ** si salida contiene PII | WIRING-04 |
| `record_access` | **SÍ** | WIRING-05 |
| Linaje | **SÍ** | WIRING-05 |
| Clasificación | **SÍ** (vía adapter) | WIRING-02 |
| Retención | **PARCIAL** en ejecución; **SÍ** en backup (WIRING-11) | WIRING-02, 11 |
| Consentimiento | **CONDICIONAL** (org policy) | WIRING-06 |
| Auditoría | **SÍ** (dual: global + gov) | WIRING-05 |

---

## 3. Secuencia de ejecución con gobierno

```
1. Solicitud (API / webhook / job)
2. Resolver conector (_get_connector(org, id))
3. Si gov_catalog_entry_id:
   a. get_catalog_entry(org) — si missing → BLOQUEAR
   b. GovernanceConnectorAdapter.get_resource_policy
   c. Si legal hold / DENEGADO → BLOQUEAR
   d. Si requiere consent y no vigente → BLOQUEAR
4. execute_connector (SSRF, auth, retry, circuit) — 1330 existente
5. apply_mapping + validate_schema
6. Si PERMITIDO_CON_TRANSFORMACIÓN → apply_mask (fallo → BLOQUEAR)
7. Emitir señales si destination SENALES
8. record_access + add_lineage_event (si catalog linked)
9. write_audit integraciones.conector.ejecutado
10. sync_continuidad_from_connector (WIRING-07/08)
11. Commit
```

### Tabla de decisiones

| Condición | Acción |
|-----------|--------|
| Sin `gov_catalog_entry_id` | **CONTINUAR** (modo sin gobierno) + audit note |
| Catálogo no existe / otra org | **BLOQUEAR** 422 |
| Sin política proveedor (rank bajo) | **CONTINUAR** (evaluate default PERMITIDO) |
| Política DENEGADO | **BLOQUEAR** |
| Legal hold activo | **BLOQUEAR** |
| PERMITIDO_CON_TRANSFORMACIÓN | **CONTINUAR** tras mask |
| Mask falla | **BLOQUEAR** |
| Consent requerido y ausente | **BLOQUEAR** |
| Circuit abierto | **BLOQUEAR** (ya existe) |
| Ejecución falla tras retries | **DEGRADAR** conector + **ALERTAR** continuidad |
| Ejecución parcial schema | **CONTINUAR** + status PARCIAL + lineage |

---

## 4. 1330 → 1360 — `proveedor_ref`

### Formato canónico (sin nuevo identificador)

```
proveedor_ref = "connector:{integration_connectors.id}"
```

| Alternativa | Descartada porque |
|-------------|-------------------|
| `catalog_entry_id` | No identifica salud de conexión técnica |
| `connector.code` | Puede cambiar; no único global |
| Nombre lógico libre | Sin correlación automática |

### Resolución servicio

```python
# continuidad_service.resolve_servicio_by_proveedor_ref(db, org_id, f"connector:{cid}")
```

Índice lógico: query `(organization_id, proveedor_ref)` — si múltiples, usar el activo más reciente.

### Cableado automático

| Estado 1330 | `EstadoOperacional` 1360 | Alerta |
|-------------|--------------------------|--------|
| ACTIVO, circuit cerrado | DISPONIBLE | — |
| DEGRADADO / failures | DEGRADADO | SERVICIO_DEGRADADO |
| Circuit abierto | NO_DISPONIBLE | SERVICIO_CAIDO |
| Recuperación tras éxito | DISPONIBLE | (no alerta recuperación duplicada) |

---

## 5. Salud automática — eventos

| Concepto | Ya existe | Reutilizable | Nuevo |
|----------|-----------|--------------|-------|
| Conector sano | `last_success_at`, status ACTIVO | `DISPONIBLE` vía WIRING-07 | — |
| Degradado | `ConnectorStatus.DEGRADADO` | `SERVICIO_DEGRADADO` | — |
| Caído | `circuit_open` | `SERVICIO_CAIDO` | — |
| Recuperado | reset failures | `update_estado(DISPONIBLE)` | — |
| Timeout | `ExecutorError` category | audit ejecución fallida | — |
| Circuit abierto | modelo `circuit_open_until` | mismo que caído | — |
| Sync health explícito | — | — | **EVENTO-NUEVO-01:** opcional audit `integraciones.health.sync` (no bus) |
| Restore bloqueado privacidad | — | alerta `cont_alertas` | **EVENTO-NUEVO-02:** tipo `RESTORE_BLOQUEADO_PRIVACIDAD` |

**Eventos reutilizables:** 8 (sin duplicar alerta si estado no cambió).

**Eventos nuevos necesarios:** 2 (solo tipos de alerta/audit; **no** nuevo bus de mensajería).

**Anti-duplicación:** comparar `estado_operacional` previo antes de `_alerta`; debounce 5 min por `(org, servicio_id, tipo)`.

---

## 6. 1350 ↔ 1360 — Coordinación técnica

### A. Dato bajo legal hold en backup

| Regla | Implementación |
|-------|----------------|
| Backup **permitido** (copia forense) | Registrar backup con tag metadata `legal_hold_snapshot: true` |
| Purge/restore **bloqueado** | WIRING-10, WIRING-12 |
| Evidencia | `gov.legal_hold.create` + `cont_auditoria BACKUP` con `hold_id` |

### B. Vencimiento retención con copias existentes

| Regla | Implementación |
|-------|----------------|
| No borrar backup automáticamente sin job | Marcar `GovSubjectRequest` tipo `BORRADO` + estado **PENDIENTE** |
| Backup conservado hasta purge autorizado | `cont_backup_ejecuciones.estado_registro` + finding `PURGA_PENDIENTE` |

### C. Borrado diferido

| Regla | Implementación |
|-------|----------------|
| Registro | `GovSubjectRequest` con `status=PENDIENTE_PURGA_BACKUP` (ver sección 7) |
| Linaje | `add_lineage_event(step_type="BORRADO_SOLICITADO")` |
| Continuidad | No eliminar backup hasta cierre request |

### D. Restauración con política cambiada

| Regla | Implementación |
|-------|----------------|
| Evaluar política **al momento del restore** | `evaluate_provider_export` actual |
| Si ahora DENEGADO | **BLOQUEAR** aunque backup sea viejo |
| Audit | Dual gov + cont con `policy_snapshot` en metadata |

### E. Trazabilidad eliminación pendiente

| Regla | Implementación |
|-------|----------------|
| Dashboard gov | contador requests `PENDIENTE_PURGA_BACKUP` |
| Centro Control | WIRING-14 campo `purga_pendiente` |

### F. Recuperación reintroduce datos

| Regla | Implementación |
|-------|----------------|
| Restore REAL prod | Ya bloqueado en 1360 |
| Restore simulado | Permitido con `evaluate_provider_export` + mask si datos salen de entorno controlado |
| Post-restore | `record_access` acción `RESTORE` en gov si entry vinculada |

---

## 7. Modelo de estados

| Estado conceptual | Equivalente existente | Cambio necesario |
|-------------------|----------------------|------------------|
| `BORRADO_PENDIENTE_BACKUP` | `GovSubjectRequest.status` — **añadir valor** `PENDIENTE_PURGA_BACKUP` | **CAMBIO NECESARIO** (enum/string en gov) |
| `RETENIDO_LEGALMENTE` | `GovLegalHold.status == ACTIVO` | **YA EXISTE** |
| `PURGA_DIFERIDA` | `GovSubjectRequest` + finding `PURGA_PENDIENTE` | **PARCIAL** — formalizar status |
| `RESTAURADO_PENDIENTE_VALIDACION` | `ContinuidadRestorePrueba` sin validación gov | **CAMBIO NECESARIO** — campo `gov_validation_status` nullable en restore o metadata JSON |

**No modificar modelos en este documento** — marcar en ticket de implementación.

---

## 8. P1-01 y P1-02

### P1-01 — `catalog_entry_id` cross-org

| Campo | Detalle |
|-------|---------|
| **CAUSA** | Enlace conector a entry de otra organización |
| **RIESGO** | Políticas/retención de tenant B aplicadas a tenant A |
| **ESCENARIO** | Admin A envía `gov_catalog_entry_id` de org B en POST conector |
| **CORRECCIÓN** | WIRING-01: `get_catalog_entry(db, org_id, id)` en create/update; 404/422 si mismatch |
| **ARCHIVOS** | `integration_service.py`, `schemas_integration.py`, tests |
| **PRUEBAS** | `test_connector_rejects_other_org_catalog` |
| **CIERRE** | Test pasa; intento cross-org audit `integraciones.conector.rechazado` |

### P1-02 — Wiring cross-módulo sin `organization_id`

| Campo | Detalle |
|-------|---------|
| **CAUSA** | Llamadas directas a gov/cont sin pasar `organization_id` del conector |
| **RIESGO** | Datos de gobierno/continuidad de otro tenant |
| **ESCENARIO** | Helper interno usa solo `catalog_entry_id` sin org |
| **CORRECCIÓN** | Firma obligatoria `(db, organization_id, ...)` en todos los helpers WIRING-02…12 |
| **ARCHIVOS** | `integration_service.py`, `continuidad_service.py` (gate restore) |
| **PRUEBAS** | Suite multi-tenant: org A no ve logs/alertas de B tras wiring |
| **CIERRE** | 0 fallos en `test_tenant_isolation_wiring_*`; revisión código checklist |

**P1 con corrección definida:** **2**

---

## 9. P2-01

| Campo | Detalle |
|-------|---------|
| **Descripción** | `proveedor_ref` / `recurso` backup sin prefijo tenant en sistemas externos |
| **Mantener hasta** | Fase convergencia wiring cerrada (no bloquea integración app) |
| **Endurecer** | Al integrar backup real con storage externo: `recurso=f"{org_id}:connector:{id}"` |
| **Despliegue horizontal** | No afecta instancia única; **sí** si backups compartidos multi-tenant en mismo bucket |
| **Wiring** | WIRING-09 documenta formato; extensión org-prefix en WIRING-11 metadata |

---

## 10. Resolución de los 9 conflictos reales

Principio: **preservar base puente** (1230, 1240, 1250, UI fixes `d57b831`) + **fusionar** tres módulos sin eliminar identidad/Fase 1.

### `backend/app/main.py`

| Fuente | Aporta |
|--------|--------|
| Base puente | `baseline_models`, `external_models`, routers línea base, valoración, diagnósticos, inteligencia_externa, control_center |
| 1350 | `governance_models`, `governance.router` |
| 1360 | `continuidad_models`, `continuidad.router` |
| 1330 | `integration_models`, `integraciones.router` |
| **Resultado** | Todos los imports modelo + `include_router` de los tres + routers puente |

### `backend/app/permissions.py`

| Fuente | Aporta |
|--------|--------|
| Base | LINEA_BASE, VALORACION, DIAGNOSTICOS, INTELIGENCIA_EXTERNA, CONTROL_CENTER |
| 1350 | `DATOS_PERMISSIONS` + ALL_PERMISSIONS + ROLE fallbacks |
| 1360 | `CONTINUIDAD`, `INCIDENTES`, `BACKUPS` permissions |
| 1330 | `INTEGRATION_PERMISSIONS` |
| **Resultado** | Unión de conjuntos en admin/superadmin/operator/viewer según matriz existente |

### `backend/alembic/migration_ledger.json`

| Fuente | Aporta |
|--------|--------|
| Base | protected hasta `1250f1a2b3c4d` |
| Fase 1 (si ESCENARIO B) | 1300, 1370, 1380, 1350, 1360, merges |
| 1330 | `1330a1b2c3d4e` al final |
| **Resultado** | `baseline_head` = head final único; lista protected = unión ordenada sin duplicados |

### `backend/scripts/schema_repair.py`

| Fuente | Aporta |
|--------|--------|
| **Resultado** | `HEAD_REVISION` = head final post-wiring (Fase1_HEAD o `1330a` si 1330 último) |

### `frontend/src/api.ts`

| Fuente | Aporta |
|--------|--------|
| Base | línea base, valoración, diagnósticos, inteligencia externa, centro control |
| 1350 | bloque `fetchGov*` |
| 1360 | bloque `fetchContinuidad*` / tablero |
| 1330 | bloque `fetchIntegration*` |
| **Resultado** | Secciones apiladas; sin eliminar funciones puente |

### `frontend/src/App.tsx`

| Fuente | Aporta |
|--------|--------|
| Base | rutas diagnosticos, inteligencia-externa, lineas-base, CentroControl index |
| 1350 | `/gobernanza-datos` |
| 1360 | `/continuidad` |
| 1330 | `/integraciones/*` |
| **Resultado** | Todas las rutas en un `Routes` |

### `frontend/src/AppShell.tsx`

| Fuente | Aporta |
|--------|--------|
| Base | menú Análisis y control completo |
| 1350 | entrada gobernanza-datos |
| 1360 | entrada continuidad |
| 1330 | entrada integraciones |
| **Resultado** | Ítems adicionales en sección Análisis y control |

### `frontend/src/auth/permissions.ts`

| Fuente | Aporta |
|--------|--------|
| Base | rutas diagnósticos, inteligencia-externa |
| 1350 | `/gobernanza-datos` → `datos.view` |
| 1360 | `/continuidad` → `continuidad.view` |
| 1330 | `/integraciones*` → `integraciones.*` |
| **Resultado** | Mapa unificado `ROUTE_PERMISSIONS` |

### `tests/conftest.py`

| Fuente | Aporta |
|--------|--------|
| Base | baseline, valuation, diagnostic, external_models imports |
| 1350 | `governance_models` |
| 1360 | `continuidad_models` |
| 1330 | `integration_models` |
| **Resultado** | Todos los imports ORM para metadata completa |

---

## 11. Alembic — Escenario A y B

### ESCENARIO A — D aún no consolidó 1350/1360

Cadena recomendada (lineal, 1 head):

```
4b67183 (1250f)
  → 1350a1b2c3d4e
  → 1360a1b2c3d4e  (down_revision = 1350a)
  → 1330a1b2c3d4e  (down_revision = 1360a)
```

| Campo | Valor |
|-------|-------|
| **Preparado** | **SÍ** |
| **Merge revisions** | 0 |
| **Orden portado** | 1350 → 1360 → 1330 → wiring code → migración columna gov_catalog si en 1330 |

### ESCENARIO B — D consolidó Fase 1 (1350, 1360, identidad)

Cadena **probable** según ramas existentes:

```
4b67183 (1250f)
  → [1360a + 1350a según orden D]
  → MERGE_FASE1_DATOS (1350 + 1360)     # si paralelos
  → 1300a (reparent a MERGE_FASE1 o 1250a→reparent a head D)
  → 1370a
  → 1380a
  → HEAD_FASE1 (= 1380a típicamente)
  → 1330a1b2c3d4e (down_revision = HEAD_FASE1)  # NO 1250f
```

| Campo | Valor |
|-------|-------|
| **Preparado** | **SÍ** |
| **Rehacer Fase 1** | **NO** — solo reparent `1330a.down_revision` |
| **Merge adicional** | Solo si D dejó múltiples heads; resolver antes de 1330 |

### Inserción 1330 después de 1380

| Paso | Acción |
|------|--------|
| 1 | Obtener `HEAD_FASE1` SHA y revision id (ej. `1380a1b2c3d4e`) |
| 2 | Cherry-pick/portar código 1330 **sin** migración antigua down_revision |
| 3 | Editar `1330a1b2c3d4e`: `down_revision = HEAD_FASE1` |
| 4 | Si WIRING-01: misma migración o `1330b` add column `gov_catalog_entry_id` |
| 5 | Actualizar ledger + `HEAD_REVISION` → `1330a` (o `1330b` si split) |
| 6 | Roundtrip desde base puente |

**Inserción 1330 después de Fase 1:** **DEFINIDA**

---

## 12. Identidad (1300 / 1370 / 1380) — no romper genealogía

| Revision | down_revision actual (rama remota) | Nota |
|----------|-----------------------------------|------|
| 1300a | `1250a1b2c3d4e` | **Reparent obligatorio** en Fase 1 a head puente `1250f` o merge D |
| 1370a | `1300a` | Mantener tras 1300 |
| 1380a | `1370a` | Head identidad |

**1330 no depende de identidad** para wiring runtime, pero **sí** en orden Alembic: identidad antes de 1330 en ESCENARIO B.

**Permisos SSO/SCIM** no interfieren wiring salvo que ejecución conector use `get_current_user` — ya cumple.

---

## 13. Centro de Control — datos específicos tríada

Bloques JSON a añadir al agregador 1230 (WIRING-14):

### `integraciones` (1330)

```json
{
  "conectores_activos": n,
  "conectores_degradados": n,
  "circuit_abiertos": n,
  "ultimos_fallos": [{ "connector_id", "code", "error", "at" }],
  "tasa_exito_periodo": pct
}
```

### `gobierno_datos` (1350)

Desde `dashboard_summary`: `sin_clasificar`, `riesgo_alto`, `solicitudes_abiertas`, `hallazgos_abiertos`, `acciones_pendientes`, `legal_holds_activos` (nuevo count en dashboard o query).

### `continuidad` (1360)

Desde `centro_control_resumen`: `incidentes_abiertos`, `backups_fallidos`, `servicios_degradados`, `alertas_top`, `rto_rpo_incumplidos`.

### Acciones pendientes unificadas

Sumar: gov corrective actions + cont acciones correctivas + integraciones con circuit abierto.

---

## 14. Pruebas focales

### 1330 ↔ 1350 (mínimo 8)

1. `test_tenant_a_catalog_not_visible_to_b`
2. `test_connector_rejects_other_org_catalog` (P1-01)
3. `test_execute_blocked_by_gov_policy`
4. `test_execute_masks_fields`
5. `test_execute_creates_gov_access_log`
6. `test_execute_creates_lineage_event`
7. `test_execute_blocked_under_legal_hold`
8. `test_credentials_not_in_logs` (secret/headers)

### 1330 ↔ 1360 (mínimo 6)

9. `test_servicio_proveedor_ref_connector_id`
10. `test_health_sync_degrades_servicio`
11. `test_health_sync_recovers_servicio`
12. `test_circuit_opens_single_alert`
13. `test_connector_down_servicio_caido`
14. `test_tenant_b_no_servicio_from_a_connector`

### 1350 ↔ 1360 (mínimo 6)

15. `test_restore_blocked_under_legal_hold`
16. `test_restore_blocked_by_classification`
17. `test_backup_retention_aligns_gov`
18. `test_simulated_restore_allowed_with_hold`
19. `test_purge_deferred_subject_request`
20. `test_restore_dual_audit_gov_cont`

### Integración / regresión (mínimo 8)

21. `test_no_duplicate_alerts_on_repeated_health_sync`
22. `test_centro_control_tríada_blocks`
23. `test_migration_roundtrip_upgrade_downgrade_upgrade` (SQLite)
24. PostgreSQL roundtrip manual/script
25. `pytest tests/test_integraciones_1330.py`
26. `pytest tests/test_governance_1350.py`
27. `pytest tests/test_continuidad_1360.py`
28. `pytest tests/` regresión completa
29. `npm run build`

**Total pruebas focales definidas:** **29** (+ regresión global)

---

## 15. Criterios de aborto

| # | Criterio | Abortar si |
|---|----------|------------|
| 1 | P0 | **P0 > 0** |
| 2 | P1 abierto | P1-01 o P1-02 sin tests verdes |
| 3 | Multiempresa | Cualquier test cross-tenant falla |
| 4 | Secreto expuesto | Token/password en logs/audit/detail |
| 5 | Legal hold ignorado | Restore/ejecutar bajo hold activo |
| 6 | Restore viola política | Restore REAL con clasificación DENEGADO |
| 7 | Auditoría | Falta `record_access` o `integraciones.conector.ejecutado` |
| 8 | Linaje | Falta lineage en ejecución con catalog linked |
| 9 | Alembic | `alembic heads` ≠ 1 |
| 10 | Regresión | `pytest tests/` > 0 failed |
| 11 | Frontend | `npm run build` FAIL |
| 12 | Roundtrip | SQLite o PostgreSQL FAIL |

**Criterios de aborto:** **12**

---

## Orden de implementación (post-receta)

1. Completar Fase 1 D (ESCENARIO B) — **sin tocar** wiring
2. Reparent/portar 1330 → HEAD_FASE1
3. Resolver 9 conflictos hub (sección 10)
4. Implementar WIRING-01, 02, 03, 04, 05 (1330↔1350 core)
5. Implementar WIRING-07, 08, 09 (1330↔1360)
6. Implementar WIRING-06 (consent condicional)
7. Implementar WIRING-10, 11, 12 (1350↔1360)
8. Implementar WIRING-13 (UI)
9. Implementar WIRING-14 (Centro Control)
10. Cerrar P1-01, P1-02 con tests
11. Regresión + roundtrip + build
12. Declarar integración apta

---

## SALIDA FINAL

```
EMPLEADOS IA — RECETA WIRING 1330/1350/1360 PREPARADA

WIRING TOTAL:
14

1330↔1350:
7

1330↔1360:
3

1350↔1360:
3

P1 IDENTIFICADOS:
2

P1 CON CORRECCIÓN DEFINIDA:
2

P2:
1

EVENTOS REUTILIZABLES:
8

EVENTOS NUEVOS:
2

CONFLICTOS REALES:
9

ESCENARIO A PREPARADO:
SI

ESCENARIO B PREPARADO:
SI

INSERCIÓN 1330 DESPUÉS DE FASE 1:
DEFINIDA

ALEMBIC:
DEFINIDO

PRUEBAS:
29 focales + regresión + roundtrip + frontend

CRITERIOS DE ABORTO:
12

MODIFICACIONES:
0

CONVERGENCIA:
NO

VEREDICTO:
RECETA LISTA
```

---

*Documento de diseño — implementación posterior por agente de convergencia/wiring.*
