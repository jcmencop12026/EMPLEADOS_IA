# CURSOR — Mapa quirúrgico de integración 1330 / 1350 / 1360

## Resumen ejecutivo

Análisis **solo lectura** del código real en las ramas limpias/portables para determinar el wiring funcional pendiente entre **Integraciones (1330)**, **Gobierno de datos (1350)** y **Continuidad (1360)** al portarse sobre la futura **base puente V1/post-V1**.

**No se ha modificado código, no se ha iniciado convergencia.**

---

## Referencias analizadas

| Pieza | Rama | Commit funcional | Alembic |
|-------|------|------------------|---------|
| **1330** | `cursor/1330-integraciones-convergencia-limpia` | `9fd0118` (origen `5271ae54`) | `1330a1b2c3d4e` ← `1250f1a2b3c4d` |
| **1350** | `cursor/1350-gobierno-datos-convergencia-limpia` | `3d5bf04` | `1350a1b2c3d4e` ← `1250f1a2b3c4d` |
| **1360** | `cursor/1360-continuidad-resiliencia` | `3edc637` | `1360a1b2c3d4e` ← `1250f1a2b3c4d` |
| **Base histórica** | `cursor/1250-convergencia-final-post-v1` | `eb229806` | head `1250f1a2b3c4d` |

Las tres piezas son **ramas gemelas** desde `1250f1a2b3c4d` en sus versiones limpias actuales.

---

## 1. 1330 ↔ 1350 — Gobierno y conectores

### Artefactos clave en 1350

| Componente | Ubicación | Rol |
|------------|-----------|-----|
| `GovernanceConnectorAdapter` | `governance_adapters.py` | Vista de política por `catalog_entry_id` |
| `get_connector_policy_view()` | `governance_service.py` | Clasificación, export eval, legal hold, retención, purpose |
| `evaluate_provider_export()` | `governance_service.py` | PERMITIDO / DENEGADO / PERMITIDO_CON_TRANSFORMACIÓN |
| `record_access()` | `governance_service.py` | Auditoría de accesos |
| `apply_mask()` / `sanitize_secret_fields()` | `governance_masking.py` | Minimización / enmascaramiento |
| `create_legal_hold()` / `release_legal_hold()` | `governance_service.py` | Legal hold por catálogo |
| `create_authorization()` | `governance_service.py` | Consentimiento / autorización |
| `record_export()` | `governance_service.py` | Exportación con evaluación previa |
| `add_lineage_event()` | `governance_service.py` | Linaje / trazabilidad |
| API preparada | `GET /api/gobierno-datos/adaptador-1330/catalogo/{entry_id}` | Adaptador REST (permiso `datos.view`) |

### Estado en 1330

| Área | Estado | Evidencia |
|------|--------|-----------|
| Consumo de `GovernanceConnectorAdapter` | **PENDIENTE** | `integration_service.py` no importa governance |
| Enlace conector ↔ catálogo gobierno | **PENDIENTE** | `IntegrationConnector` sin `catalog_entry_id` / FK a `gov_catalog_entries` |
| Catálogo UI conectores | **YA IMPLEMENTADO** | `list_catalog()` estático de tipos (API, SFTP, webhook…) |
| Auditoría ejecución | **YA IMPLEMENTADO** | `write_audit` `integraciones.conector.*` |
| Secretos | **YA IMPLEMENTADO** | `secret_ref`, `resolve_secret`, config sin password en respuesta |
| SSRF / red | **YA IMPLEMENTADO** | `integration_security.py` |
| Señales (puente datos) | **YA IMPLEMENTADO** | `_emit_signals()` → `signal_ingestion_service` |
| Minimización en payload | **PENDIENTE** | No llama `apply_mask` |
| Legal hold pre-ejecución | **PREPARADO** | Lógica en `get_connector_policy_view`; no enforced en 1330 |
| Retención post-ejecución | **PENDIENTE** | Sin coordinación con `GovRetentionPolicy` |
| Consentimiento | **PREPARADO** | `GovAuthorization` existe; sin check en conector |
| Exportación formal | **PARCIAL** | Export gov vía API; ejecución conector no registra `GovExportRecord` |
| Trazabilidad gobierno | **PENDIENTE** | Sin `add_lineage_event` en flujo conector |

### Matriz por flujo (1330 ↔ 1350)

| Flujo | Estado | Wiring final previsto |
|-------|--------|----------------------|
| Clasificación de datos | **PREPARADO** | Vía catálogo gov + adapter; falta FK/enlace en conector |
| Retención | **PREPARADO** | `retention_policy_id` en vista; falta enforcement en lifecycle ejecuciones |
| Privacidad / minimización | **PARCIAL** | Políticas y `apply_mask` en 1350; falta aplicar en `execute_connector` |
| Consentimiento | **PREPARADO** | `GovAuthorization`; falta validar purpose/consent antes de ejecutar |
| Legal hold | **PREPARADO** | Detectado en `get_connector_policy_view`; falta bloquear execute/export |
| Borrado | **PENDIENTE** | Subject requests en 1350; sin hook desde datos ingeridos por conector |
| Exportación | **PARCIAL** | `record_export` en gov; conector no registra exportación ni evalúa salida externa |
| Auditoría | **PARCIAL** | Audit global + `gov.access` API; conector no llama `record_access` |
| Trazabilidad | **PREPARADO** | `add_lineage_event`; falta en éxito/fallo de ejecución |
| Credenciales / conexiones | **YA IMPLEMENTADO** | 1330 autónomo; gov no gestiona secretos de conector (correcto) |

### Dónde debe ocurrir el wiring (sin implementar)

1. **`integration_service.execute_connector()`** — preflight: `GovernanceConnectorAdapter.get_resource_policy()`; abortar si restricciones críticas.
2. **Mismo flujo** — post-validación: `apply_mask` según `minimization_action`.
3. **Mismo flujo** — post-ejecución: `record_access`, `add_lineage_event`, opcional `record_export` si salida externa.
4. **Modelo / schema** — `catalog_entry_id` opcional en `IntegrationConnector` + validación `organization_id`.
5. **UI** — wizard conector: selector de entrada catálogo gobierno (API ya expuesta).

**Veredicto 1330↔1350:** **PARCIAL** (adaptador y APIs listos; enforcement en runtime **PENDIENTE**).

---

## 2. 1330 ↔ 1360 — Salud, fallos y continuidad

### Conceptos separados

| Concepto | Módulo | Qué es hoy |
|----------|--------|------------|
| **HEALTH** | 1330 | `get_health()`, campos `last_success_at`, `circuit_open`, `consecutive_failures` en conector |
| **OBSERVABILIDAD** | 1330 + audit global | Ejecuciones, `error_message` truncado, audit `integraciones.conector.*` |
| **CONTINUIDAD** | 1360 | Servicios críticos, incidentes, planes, backups, SLO, RTO/RPO, alertas `cont_alertas` |

### Qué expone 1330

- `GET /api/integraciones/conectores/{id}/salud` — estado, circuit breaker, success rate.
- Estados conector: `ACTIVO`, `DEGRADADO`, `BORRADOR`, circuit `circuit_open_until`.
- Reintentos, timeouts, idempotencia en `execute_connector`.
- Sin endpoint que empuje salud a continuidad.

### Qué ofrece 1360

- `POST /api/continuidad/servicios/{id}/reportar-salud` — actualiza `estado_operacional`; flag `integracion_1330: True` en respuesta.
- `update_estado_servicio()` — genera alertas `SERVICIO_CAIDO`, `SERVICIO_DEGRADADO`.
- `ContinuidadServicioCritico.proveedor_ref` — campo texto para referencia externa (puede almacenar `connector:{id}`).
- Tablero: `integracion_1330_prep.reportar_salud` (documentación de endpoint; path en doc ≠ path real exacto).
- Incidentes, modo degradado, fallback, escalamiento — **sin** auto-creación desde conector.

### Estado integración

| Enlace | Estado |
|--------|--------|
| Health 1330 → reportar_salud 1360 | **PENDIENTE** |
| Circuit abierto → incidente continuidad | **PENDIENTE** |
| Degradado conector → `EstadoOperacional.DEGRADADO` servicio | **PENDIENTE** |
| Recuperación → `DISPONIBLE` | **PENDIENTE** |
| Mapping conector ↔ servicio crítico | **PREPARADO** (manual vía `proveedor_ref` / creación servicio) |
| RTO/RPO por conector | **PENDIENTE** (RTO/RPO solo en servicio 1360) |

**Veredicto 1330↔1360:** **PARCIAL** (capacidades en ambos lados; **cableado automático PENDIENTE**).

---

## 3. 1350 ↔ 1360 — Retención, backups y recuperación

### Capacidades actuales

| 1350 | 1360 |
|------|------|
| `GovRetentionPolicy.disposition` (default `REVISIÓN_MANUAL`) | `ContinuidadBackupPolitica.retencion_dias` |
| `GovLegalHold` por `catalog_entry_id` o alcance org | Backups por `recurso` string + `servicio_id` |
| `GovSubjectRequest` (borrado/acceso) | `ContinuidadRestorePrueba`, verificaciones backup |
| `record_export` con evaluación | `registrar_restore`, `verificar_backup` |
| Sin tabla de “borrado diferido” explícita | Sin consulta a legal hold antes de purge |

### Preguntas obligatorias (arquitectura del proyecto)

| Pregunta | Análisis |
|----------|----------|
| **A. Legal hold + backup** | Hoy **sin coordinación**. Backup puede existir independiente; legal hold no bloquea creación backup en 1360. **PENDIENTE:** validar hold antes de purge/restore y marcar backups bajo hold. |
| **B. Borrado vs copias** | Política gov `disposition` no enlaza con `retencion_dias` backup. **PENDIENTE:** workflow borrado diferido (subject request → ticket backup → evidencia). |
| **C. Eliminación diferida** | Parcial vía `GovSubjectRequest` estados; sin registro explícito “pendiente en backup”. **PENDIENTE:** entidad o estado compartido. |
| **D. Evidencia gobierno en continuidad** | `cont_auditoria` separada de `write_audit` / `gov.access`. **PENDIENTE:** replicar eventos críticos (export, hold, restore) en ambos o índice cruzado. |
| **E. Restore vs privacidad** | **PENDIENTE:** antes de `registrar_restore`, evaluar clasificación/`evaluate_provider_export` del recurso restaurado. |

**Veredicto 1350↔1360:** **PARCIAL** (modelos ricos; **política cruzada PENDIENTE**).

---

## 4. Multiempresa

### Mecanismos existentes

| Módulo | Aislamiento |
|--------|-------------|
| 1330 | `organization_id` en conector, ejecución, webhook; `_get_connector(db, org_id, …)` |
| 1350 | Filtro `organization_id` en catálogo, holds, policies, logs |
| 1360 | `_ensure_scope(org_id, entity.organization_id)` → 404 |

### Riesgos al integrar (sin implementar)

| ID | Riesgo | Nivel |
|----|--------|-------|
| R1 | `catalog_entry_id` en conector sin validar org del entry | **P1** |
| R2 | `proveedor_ref` / `recurso` backup sin prefijo tenant en sistemas externos | **P2** |
| R3 | Webhook por token de conector (org implícita en row) — correcto si no se filtra token | — |
| R4 | Wiring futuro que omita `organization_id` en llamadas cruzadas | **P1** (preventivo) |

| Nivel | Cantidad |
|-------|----------|
| P0 | 0 |
| P1 | 2 |
| P2 | 1 |

---

## 5. Seguridad

### Qué NO debe aparecer en logs

- Valores de `secret_ref` / tokens webhook en claro.
- Headers `Authorization`, API keys (1330 ya redacta en `redact_sensitive_headers`).
- Payloads completos de datos personales en `error_message` / audit detail (truncar + enmascarar).
- Contenido de backups en `error_seguro` más allá de mensaje seguro.

### Qué debe enmascararse

- Campos PII en registros mapeados antes de audit/log (`apply_mask` 1350).
- Metadata export (`sanitize_secret_fields` ya en gov).

### Qué sí debe auditarse

| Acción | Módulo | Ya existe |
|--------|--------|-----------|
| Crear/editar/probar/ejecutar conector | 1330 | `integraciones.conector.*` |
| Acceso a catálogo gov | 1350 | `gov.access` vía API / `record_access` |
| Export / legal hold | 1350 | `gov.export`, `gov.legal_hold.*` |
| Backup / restore / incidente | 1360 | `cont_auditoria`, alertas |

---

## 6. Eventos

| Evento conceptual | Estado |
|-------------------|--------|
| CONECTOR_CAIDO | **REUTILIZABLE** → `SERVICIO_CAIDO` (1360) al mapear conector→servicio |
| CONECTOR_RECUPERADO | **REUTILIZABLE** → `update_estado_servicio(DISPONIBLE)` |
| SINCRONIZACION_FALLIDA | **YA EXISTE** → ejecución `FALLIDA` + audit `integraciones.conector.ejecutado` |
| POLITICA_RETENCION_AFECTADA | **REUTILIZABLE** → hallazgo `RETENCION_AUSENTE` (1350 scan) |
| LEGAL_HOLD_ACTIVO | **REUTILIZABLE** → restricción en adapter + `gov.legal_hold.create` |
| BACKUP_FALLIDO | **YA EXISTE** → `_alerta(..., "BACKUP_FALLIDO")` |
| RECUPERACION_EJECUTADA | **YA EXISTE** → audit restore en 1360 |
| SLA/RTO/RPO breach | **YA EXISTE** → `SLA_INCUMPLIDO`, `RTO_INCUMPLIDO`, `RPO_EN_RIESGO` |

| Métrica | n |
|---------|---|
| EVENTOS REUTILIZABLES | **8** |
| EVENTOS NUEVOS NECESARIOS | **2** (opcionales: `CONECTOR_HEALTH_SYNC` explícito; `RESTORE_BLOQUEADO_PRIVACIDAD` si no se usa alerta genérica) |

---

## 7. Centro de Control (1230) — datos específicos tríada

**Solo aporte 1330/1350/1360** (mapa general en agente A).

| Fuente | Datos a exponer al adaptador 1230 |
|--------|-----------------------------------|
| **1330** | Conectores activos/degradados; circuit abierto; últimos errores; tasa éxito; ejecuciones fallidas recientes |
| **1350** | `dashboard_summary`: sin clasificar, riesgo alto, solicitudes abiertas, hallazgos, acciones pendientes, exportaciones |
| **1360** | `tablero` / `centro_control_resumen`: servicios degradados, incidentes abiertos, backups fallidos, alertas top, RTO/RPO incumplidos |

**Wiring pendiente:** extender `control_center_service` / adapters (similar a `integraciones_futuras` en `eb229806`) — **no duplicar agregación completa aquí**.

---

## 8. Alembic — esquema recomendado

### Situación actual (ramas limpias)

```
1250f1a2b3c4d
    ├── 1330a1b2c3d4e
    ├── 1350a1b2c3d4e
    └── 1360a1b2c3d4e
```

→ **3 heads** si se mergean sin reparent.

### Opciones

| Estrategia | Descripción | Pros | Contras |
|------------|-------------|------|---------|
| **A. Lineal reparent** | `1250f → 1350a → 1360a → 1330a` | Una head, sin merge revision, orden refleja dependencias (gov → cont → conectores) | Cambiar `down_revision` de 1360 y 1330 en convergencia |
| **B. Paralelo + merge** | Aplicar tres ramas + `merge(1350,1360)` + opcional merge con 1330 | Preserva revision IDs originales | 1–2 merge revisions; más complejidad ledger |
| **C. Híbrida** | `1250f → 1350a → merge(1350,1360) → 1330a` | Gov primero; continuidad en paralelo corto | Una merge revision mínima |

### Recomendación

**Opción A (lineal)** sobre base puente:

1. `BASE_PUENTE` (= head puente, sustituye `1250f` si la puente ya integra convergencia previa)
2. `1350a1b2c3d4e`
3. `1360a1b2c3d4e` (`down_revision` → `1350a1b2c3d4e`)
4. `1330a1b2c3d4e` (`down_revision` → `1360a1b2c3d4e`)

**Por qué:** 1350 provee políticas que 1330 debe consumir; 1360 consume salud de 1330; orden minimiza wiring sin merge migrations; una sola head.

**NO modificar migraciones en este análisis.**

---

## 9. Conflictos entre piezas

Simulación `git merge-tree` (pares de ramas limpias):

| Pareja | Archivos con conflicto real |
|--------|----------------------------|
| 1350 + 1360 | 6 |
| 1330 + 1350 | 6 |
| 1330 + 1360 | 9 |
| **Unión única** | **9** |

### Archivos con CONFLICTO REAL (unión)

1. `backend/alembic/migration_ledger.json`
2. `backend/app/main.py`
3. `backend/app/permissions.py`
4. `backend/scripts/schema_repair.py`
5. `frontend/src/App.tsx`
6. `frontend/src/AppShell.tsx`
7. `frontend/src/api.ts`
8. `frontend/src/auth/permissions.ts`
9. `tests/conftest.py`

### CONFLICTO PROBABLE

- Modelos/servicios/routers **propios** de cada bloque: **SIN CONFLICTO** (namespaces distintos: `integration_*`, `gov_*`, `cont_*`).
- `backend/app/routers/governance.py` vs `integraciones.py` vs `continuidad.py`: **SIN CONFLICTO**.
- Tests focales: **SIN CONFLICTO** entre archivos (`test_integraciones_1330`, `test_governance_1350`, `test_continuidad_1360`).

| Clasificación | n |
|---------------|---|
| CONFLICTO REAL | **9** |
| CONFLICTO PROBABLE | **0** (los 9 son mecánicos inevitables) |
| SIN CONFLICTO | resto (~50+ archivos exclusivos) |

---

## 10. Receta de integración ejecutable (conceptual)

### PASO 1 — Base puente

- Fijar SHA remoto exacto de base puente (General).
- Verificar head Alembic único y roundtrip SQLite/PostgreSQL en puente.
- **Aborto:** head múltiple o regresión 1110/1120.

### PASO 2 — Portar 1350 limpio

- Merge/cherry-pick `3d5bf04` sobre puente.
- Resolver 6 archivos hub si ya hay otra pieza; si es primero, solo integración ledger/HEAD.
- **Pruebas:** `test_governance_1350.py`, migration control, roundtrip.
- **Aborto:** fallo governance o migración.

### PASO 3 — Portar 1360

- Aplicar `3edc637`; reparent futuro `down_revision` → `1350a` (si estrategia lineal).
- Resolver conflictos en 9 archivos hub (acumulativo).
- **Pruebas:** `test_continuidad_1360.py`, roundtrip.
- **Aborto:** fallo continuidad o heads > 1 sin plan.

### PASO 4 — Portar 1330 limpio

- Aplicar `9fd0118`; reparent `down_revision` → head tras 1360 (lineal).
- Resolver conflictos hub + rutas integraciones en App/AppShell.
- **Pruebas:** `test_integraciones_1330.py`, roundtrip.
- **Aborto:** regresión 1120 o pérdida 1230/1240/1250.

### PASO 5 — Wiring 1350 ↔ 1330

- Enlace `catalog_entry_id`; preflight adapter; mask; `record_access` + lineage.
- **Pruebas:** nuevos/integration tests cruzados (a definir en convergencia).

### PASO 6 — Wiring 1330 ↔ 1360

- Scheduler o hook post-ejecución: health → `reportar_salud`; circuit → estado servicio.
- Crear/actualizar `ContinuidadServicioCritico` con `proveedor_ref=connector:{id}`.

### PASO 7 — Wiring 1350 ↔ 1360

- Validación legal hold antes purge restore; alinear `retencion_dias` con gov policy.
- Restore gate con `evaluate_provider_export`.

### PASO 8 — Centro Control

- Añadir agregadores 1330/1350/1360 al adaptador 1230 (coordinado con agente A).

### PASO 9 — Regresión final

- `pytest tests/` completo.
- PostgreSQL roundtrip.
- `npm run build`.
- **Aborto:** cualquier P0; regresión > 0; heads ≠ 1.

---

## Wiring nuevo necesario (resumen)

| # | Wiring |
|---|--------|
| 1 | FK/enlace `catalog_entry_id` conector → gov catálogo |
| 2 | Preflight `GovernanceConnectorAdapter` en `execute_connector` |
| 3 | Enforcement legal hold / DENEGADO |
| 4 | `apply_mask` en salida |
| 5 | `record_access` + lineage en ejecución |
| 6 | Consentimiento (`GovAuthorization`) opcional por purpose |
| 7 | Health 1330 → `reportar_salud` 1360 |
| 8 | Circuit/degradado → estado servicio + alerta |
| 9 | Mapping conector ↔ `ContinuidadServicioCritico` |
| 10 | Legal hold bloquea purge/restore backup |
| 11 | Alineación retención gov ↔ `retencion_dias` backup |
| 12 | Restore validado contra política privacidad |
| 13 | UI wizard: selector catálogo gobierno |
| 14 | Centro Control: agregadores tríada |

**WIRING NUEVO NECESARIO: 14** (puntos discretos; algunos pueden ser un solo PR de integración).

---

## SALIDA FINAL

```
EMPLEADOS IA — INTEGRACIÓN 1330/1350/1360 MAPEADA

1330 FUNCIONAL:
9fd0118

1350 FUNCIONAL:
3d5bf04

1360 FUNCIONAL:
3edc637

1330↔1350:
PARCIAL

1330↔1360:
PARCIAL

1350↔1360:
PARCIAL

WIRING NUEVO NECESARIO:
14

EVENTOS REUTILIZABLES:
8

EVENTOS NUEVOS NECESARIOS:
2

RIESGOS MULTIEMPRESA:
3

P0:
0

P1:
2

P2:
1

CONFLICTOS REALES:
9

CONFLICTOS PROBABLES:
0

ALEMBIC RECOMENDADO:
Lineal BASE_PUENTE → 1350a → 1360a → 1330a (reparent down_revision; 1 head)

ORDEN DE INTEGRACIÓN:
Base puente → 1350 → 1360 → 1330 → wiring cruzado → Centro Control → regresión

CENTRO CONTROL — DATOS A EXPONER:
Conectores (estado/circuit/errores); gobierno (dashboard 1350); continuidad (incidentes/backups/RTO/RPO/alertas)

MODIFICACIONES:
0

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

CONVERGENCIA:
NO

VEREDICTO:
APTO PARA INTEGRACIÓN
```

---

*Análisis generado sin modificar código, sin crear ramas, sin convergencia.*
