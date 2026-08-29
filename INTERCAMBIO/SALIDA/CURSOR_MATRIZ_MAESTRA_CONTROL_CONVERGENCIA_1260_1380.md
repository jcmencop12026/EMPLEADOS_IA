# EMPLEADOS_IA — MATRIZ MAESTRA DE CONTROL DE CONVERGENCIA 1260–1380

**Tipo:** Control / documentación — **SOLO LECTURA**  
**Fecha:** 2026-08-29 (actualizado con insumos A/B/C)  
**Agente:** GENERAL (no duplica trabajos A / B / C / D)  
**Protocolo auditoría Fase 1:** `CURSOR_PROTOCOLO_AUDITORIA_FASE1_CONVERGENCIA.md`

---

## Referencia base oficial

| Campo | Valor |
|-------|-------|
| **Rama** | `cursor/base-puente-v1-post-v1` |
| **BASE funcional fijada** | `4b67183af1d527684e41cad0b02d7a997d3b2499` |
| **HEAD funcional código** | `d57b831e41b8e017da612c3c442f9f29c981f674` |
| **HEAD remoto actual** | Puede incluir commits **documentales** posteriores — verificar con `git rev-parse` |
| **Alembic HEAD** | `1250f1a2b3c4d` |
| **Certificación SQLite base** | 774 passed, 4 skipped |
| **PostgreSQL** | PENDIENTE (no certificado) |
| **Frontend base** | PASS |

### Fases de comparación

| Fase | Alcance | Responsable |
|------|---------|-------------|
| **BASE** | Puente certificada (1100–1250 + V1) | Fijada |
| **FASE 1** | 1360 → 1350 → merge Alembic → 1300 → 1370 → 1380 | **D** (en curso) |
| **FASE 2** | 1260, 1270, 1290, 1330, cadena comercial | Posterior |
| **FINAL** | Convergencia integral 1260–1380 + matriz 94 | Objetivo |

### Ancla funcional vs commits documentales

| Concepto | SHA / regla |
|----------|-------------|
| **Ancla funcional de convergencia** | `4b67183af1d527684e41cad0b02d7a997d3b2499` (base puente certificada) |
| **Último commit de código puro** | `d57b831e41b8e017da612c3c442f9f29c981f674` |
| **Commits documentales posteriores** | No alteran la huella funcional; no cambiar ancla sin justificación expresa |

**Regla de oro:** cualquier fila con estado **PERDIDO** en una fase posterior respecto a BASE es hallazgo de convergencia y dispara criterio de aborto.

---

## 1. Inventario de preservación (huella BASE)

Inventario levantado desde código real de `origin/cursor/base-puente-v1-post-v1` (`4b67183`).

### 1.1 Resumen cuantitativo BASE

| Artefacto | Cantidad |
|-----------|----------|
| Routers (`backend/app/routers/`, sin `__init__`) | **24** |
| Endpoints API routers | **216** |
| Endpoints app (`main.py`) | **4** (`/`, `/health`, `/health/live`, `/health/ready`) |
| Permisos (`ALL_PERMISSIONS`) | **72** |
| Módulos de modelos | **13** (72 clases SQLAlchemy) |
| Servicios (`backend/app/services/`) | **54** |
| Migraciones Alembic | **30** |
| Páginas frontend | **42** |
| Rutas frontend (`App.tsx`) | **38** autenticadas + `/login` |
| Tests (`tests/`, focal base) | **54** archivos `.py` |

### 1.2 Bloque 1100 — Oportunidades operativo

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `oportunidades.py` |
| **Endpoints (14)** | `/api/oportunidades`, `/resumen`, `/{id}`, `/senales`, `/senales/{id}/procesar`, `/pipeline-proactivo`, `/{id}/evaluar`, `/priorizar`, `/{id}/siguiente-accion`, `/{id}/aprobar`, `/{id}/activar`, `/{id}/seguimiento`, `/{id}/resultado`, `/{id}/trazabilidad` |
| **Servicios** | `proactive_service.py`, `proactive_scheduler.py` |
| **Modelos** | `opportunity_models.py` (6 clases) |
| **Permisos (5)** | `oportunidades.view`, `.manage`, `.evaluate`, `.approve`, `.activate` |
| **Migración** | *(hereda 1030; sin migración exclusiva 1100)* |
| **Frontend** | `OportunidadesPage.tsx`, `OportunidadDetailPage.tsx` — rutas `/oportunidades`, `/oportunidades/:opportunityId` |
| **Tests** | `test_bloque_1100_oportunidades_operativo.py` |
| **Integraciones** | Pipeline proactivo, motor analítico, experiencia 1010 |

### 1.3 Bloque 1110 — FinOps trazabilidad

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `finops.py` |
| **Endpoints (13)** | `/api/finops/dashboard`, `/consumptions`, `/opportunities/{id}/economics`, `/rates`, `/values`, `/budgets`, `/drill-down` (+ POST/PATCH) |
| **Servicios** | `finops_service.py`, `motor_analitico/finops_bridge.py` |
| **Modelos** | `finops_models.py` (4 clases) |
| **Permisos (4)** | `finops.view`, `.manage`, `.budget`, `.rates` |
| **Migración** | `1110a1b2c3d4e` ← `d1e2f3a4b5c6` |
| **Frontend** | `CostosValorPage.tsx` — ruta `/costos-valor` |
| **Tests** | `test_finops_1110.py` |

### 1.4 Bloque 1120 — Señales reales

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `senales.py` |
| **Endpoints (5)** | `/api/senales/fuentes`, `/ingesta`, `/senales`, `/{signal_id}/trazabilidad` |
| **Servicios** | `signal_ingestion_service.py` |
| **Modelos** | `opportunity_models.py` (señales) |
| **Permisos** | *(vía oportunidades / operaciones)* |
| **Migración** | `1120a1b2c3d4e` ← `d1e2f3a4b5c6` |
| **Frontend** | `SenalesPage.tsx`, `SenalDetailPage.tsx` — rutas `/senales`, `/senales/:signalId` |
| **Tests** | `test_senales_reales_1120.py` |

### 1.5 Bloque 1200 — Línea base

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `linea_base.py` |
| **Endpoints (8)** | `/api/lineas-base` CRUD, mediciones, validar, atribución, por oportunidad |
| **Servicios** | `baseline_service.py` |
| **Modelos** | `baseline_models.py` (4 clases) |
| **Permisos (3)** | `linea_base.view`, `.manage`, `.validate` |
| **Migración** | `1200a1b2c3d4e` ← `d1e2f3a4b5c6` |
| **Frontend** | `LineasBasePage.tsx`, `LineaBaseDetailPage.tsx` — rutas `/lineas-base`, `/lineas-base/:lineaBaseId` |
| **Tests** | `test_bloque_1200_linea_base_impacto.py` |

### 1.6 Bloque 1210 — Valoración económica / ROI

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `valoracion.py` |
| **Endpoints (8)** | `/api/valoracion/opportunities/{id}` (+ roi, expected, scenarios, real, costs, validate) |
| **Servicios** | `valuation_service.py` |
| **Modelos** | `valuation_models.py` (6 clases) |
| **Permisos (4)** | `valoracion.view`, `.manage`, `.validate`, `.roi` |
| **Migración** | `1210b2c3d4e5f` ← `1110a1b2c3d4e` |
| **Frontend** | Integrado en `OportunidadDetailPage.tsx` (pestaña valoración) |
| **Tests** | `test_valoracion_1210.py` |

### 1.7 Bloque 1220 — Diagnóstico transversal

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `diagnosticos.py` |
| **Endpoints (8)** | `/api/diagnosticos/dominios`, `/config/indicadores`, `/generar`, `/{id}`, `/validar`, `/trazabilidad` |
| **Servicios** | `diagnostic_service.py` |
| **Modelos** | `diagnostic_models.py` (8 clases) |
| **Permisos (4)** | `diagnosticos.view`, `.generate`, `.validate`, `.manage` |
| **Migración** | `1220a1b2c3d4e` ← `1120a1b2c3d4e` |
| **Frontend** | `DiagnosticosPage.tsx`, `DiagnosticoDetailPage.tsx` — rutas `/diagnosticos`, `/diagnosticos/:diagnosticId` |
| **Tests** | `test_diagnostico_transversal_1220.py` |

### 1.8 Bloque 1230 — Centro de Control

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `control_center.py` |
| **Endpoints (2)** | `/api/centro-control/resumen-ejecutivo`, `/indicadores-config` |
| **Servicios** | `control_center_service.py`, `control_center_adapters.py` |
| **Modelos** | *(agregación; sin modelo exclusivo)* |
| **Permisos (1)** | `control_center.view` |
| **Migración** | *(sin migración exclusiva 1230)* |
| **Frontend** | `CentroControlPage.tsx` — ruta `/` (índice) |
| **Tests** | `test_bloque_1230_centro_control.py`, `test_bloque_1250c_centro_control_integrado.py` |
| **Integraciones** | Adapters a 1240, FinOps, diagnóstico, oportunidades |

### 1.9 Bloque 1240 — Inteligencia Externa

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | `inteligencia_externa.py` |
| **Endpoints (13)** | `/api/inteligencia-externa/contexto`, `/fuentes`, `/ingesta`, `/senales`, clasificación, relevancia, validar, oportunidad, riesgo |
| **Servicios** | `external_intelligence_service.py` |
| **Modelos** | `external_models.py` (4 clases) |
| **Permisos (4)** | `inteligencia_externa.view`, `.manage`, `.ingest`, `.validate` |
| **Migración** | `1240c3d4e5f6a` ← `1120a1b2c3d4e` |
| **Frontend** | `InteligenciaExternaPage.tsx`, `InteligenciaExternaDetailPage.tsx` — rutas `/inteligencia-externa`, `/inteligencia-externa/senales/:signalId` |
| **Tests** | `test_inteligencia_externa_1240.py` |

### 1.10 Bloque 1250 — Convergencia post-V1

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Router** | *(integración en routers existentes)* |
| **Migraciones** | `1250a1b2c3d4e` (merge 1200+1210+1220), `1250b1c2d3e4f` (merge 1220+1240), `1250f1a2b3c4d` (HEAD final) |
| **Servicios** | `control_center_adapters.py` (extensión) |
| **Config** | `migration_ledger.json`, `schema_repair.HEAD_REVISION = 1250f1a2b3c4d` |
| **Tests** | `test_convergencia_1250a.py`, `test_convergencia_1250b.py`, `test_convergencia_final_1250.py`, `test_migration_control.py` |

### 1.11 Correcciones finales V1 (inmutables)

| Tipo | Artefactos protegidos |
|------|----------------------|
| **Routers** | `auth.py`, `admin.py`, `platform.py`, `llm_providers.py`, `organization.py` |
| **Servicios** | `authorization.py`, `tenant_service.py`, `llm_provider_service.py` |
| **Modelos** | `models.py` (org/user/RBAC), `llm_models.py` |
| **Migraciones** | `b950a1b2c3d4`, `c1a2b3c4d5e6`, `d1e2f3a4b5c6` |
| **Config seguridad** | `security_config.py`, `db_url.py`, `config.py` |
| **Docker** | `docker-compose.yml`, `docker_entrypoint.sh`, `alembic/env.py` |
| **Frontend** | `Admin*Page.tsx` (7), `LoginPage.tsx`, Knowledge auth en UI |
| **Tests** | `test_security_rbac_v1.py`, `test_multitenant_v1.py`, `test_llm_gateway_v1.py`, `test_docker_database_url.py`, `test_knowledge_930.py`, `test_integration_v1_final.py`, `test_p0_precertificacion_v1.py`, `test_prerelease_v1_corrections.py` |

### 1.12 Plataforma transversal BASE (no eliminable)

| Dominio | Router | Permisos clave |
|---------|--------|----------------|
| Operaciones | `operations.py` (21 ep.) | `operations.*` (6) |
| Automatizaciones | `automations.py` (11) | `automation.*` (8) |
| Conocimiento | `knowledge.py` (27) | `knowledge.*` (5) |
| Empleados IA | `agent_factory.py` (14) | `employee.*` (8) |
| Capacidades/Herramientas | `capabilities.py`, `tools.py` | `capability.*`, `tool.*` |
| Salud IPS | `salud.py` (14) | `salud.*` (5) |
| Notificaciones | `notifications.py` (11) | `notification.*`, `alert_rule.*` |
| Auditoría | `audit.py` (1) | `audit.view` |
| LLM Gateway | `llm_providers.py` (7) | `llm.*` (3) |
| Plataforma | `platform.py` (4) | `platform.organization.*` (3) |

---

## 2. Inventario de incorporación (1260–1380)

Estructura idéntica a §1. **Solo registro** de lo que debe aparecer tras incorporar cada bloque.  
Referencias de rama/commit (no re-auditados funcionalmente).

| Bloque | Rama | HEAD SHA |
|--------|------|----------|
| 1260 | `cursor/1260-aprendizaje-repriorizacion` | `6a6cfbcfaf64fde501e0586700d8e6639498f644` |
| 1270 | `cursor/1270-multiproveedor-observabilidad-9a85` | `f89639a7305f86dabe149337de3a89c189372a01` |
| 1280 | `cursor/1280-modelo-comercial-valor-85e4` | `9a616739c4ab1f0766cf7d46005baf2a4c3e4fec` |
| 1290 | `cursor/1290-optimizacion-recomendaciones` | `7141b434772f1510a58f6f23db3e21bff871103b` |
| 1300 | `cursor/1300-seguridad-avanzada-mfa` | `09194d8f281a1506d694844dead43e5ee93849e6` |
| 1310 | `cursor/1310-segmentacion-planes-verticales` | `379ffcf04cd0d56a3aeda0b307f718845d5c12d3` |
| 1320 | `cursor/1320-tco-ecosistema-aliados` | `703bbf9dfe3075a3c8fa622c1cb9056995b23be4` |
| 1330 | `cursor/1330-integraciones-reales-conectores` | `5271ae54f62113b231b20541700e102c6dca3320` |
| 1340 | `cursor/1340-implementacion-exito-cliente` | `5670a5727943a50bb78e3d1d41af7ed745516059` |
| 1350 | `cursor/1350-gobierno-datos-privacidad` | `3216b7d826e4de7626a0cd59b9401b5722e11fee` |
| 1360 | `cursor/1360-continuidad-resiliencia` | `4e3e8b2978d4c290fb4c28fcac218104e438a9e5` |
| 1370 | `cursor/1370-identidad-empresarial-sso` | `3c545f64fe06569ecadbfa8523d65af798d472e3` |
| 1380 | `cursor/1380-aprovisionamiento-scim` | `a1c3319e87a4bd17279ab3b4756cca006208e932` |

### 2.1–2.13 Resumen por bloque (artefactos netos a incorporar)

| Bloque | Router | Endpoints | Permisos nuevos | Migración | Frontend | Tests |
|--------|--------|-----------|-----------------|-----------|----------|-------|
| **1260** | `aprendizaje.py` | 11 `/api/aprendizaje/*` | 4 `aprendizaje.*` | `1260a1b2c3d4e` | `AprendizajePage`, `AprendizajeDetailPage` | `test_aprendizaje_1260.py` |
| **1270** | *(ext. `llm_providers.py`)* | 8 `/api/llm/*` | 0 | `1270a1b2c3d4e` | mod. `AdminLlmProvidersPage` | `test_bloque_1270_multiproveedor.py` |
| **1280** | `comercial.py` | 17 `/api/comercial/*` | 5 `comercial.*` | `1280a1b2c3d4e`, `1280b2c3d4e5f` | `ComercialPage`, `ComercialPropuestaDetailPage` | `test_modelo_comercial_1280.py` |
| **1290** | `optimizacion.py` | 12 `/api/optimizacion/*` | 5 `optimizacion.*` | `1290a1b2c3d4e` | `OptimizacionPage`, `OptimizacionDetailPage` | `test_optimizacion_1290.py` |
| **1300** | `security.py` | 14 `/api/security/*` | 4 `seguridad.*` | `1300a1b2c3d4e` | `MiSeguridadPage` | `test_bloque_1300_seguridad_avanzada.py` |
| **1310** | `segmentacion.py` | 18 `/api/segmentacion/*` | 6 `segmentacion.*` / `planes.*` | `1310a1b2c3d4e` | `SegmentacionPage` | `test_segmentacion_1310.py` |
| **1320** | `tco.py` | 26 `/api/tco/*` | 6 `tco.*` / `alianzas.*` / `proveedores.*` | `1320a1b2c3d4e` | `TcoPage` | `test_tco_1320.py` |
| **1330** | `integraciones.py` | 10 `/api/integraciones/*` | 6 `integraciones.*` | `1330a1b2c3d4e` | `IntegracionesPage`, `IntegracionDetailPage`, `IntegracionWizardPage` | `test_integraciones_1330.py` |
| **1340** | `implementacion.py` | 28 `/api/implementacion/*` | 6 `implementacion.*` / `exito_cliente.*` | `1340a1b2c3d4e` | `ImplementacionPage`, `ImplementacionDetailPage` | `test_implementacion_1340.py` |
| **1350** | `governance.py` | 41 `/api/gobierno-datos/*` | 7 `datos.*` | `1350a1b2c3d4e` | `GobernanzaDatosPage` | `test_governance_1350.py` |
| **1360** | `continuidad.py` | 31 `/api/continuidad/*` | 10 `continuidad.*` / `incidentes.*` / `backups.*` | `1360a1b2c3d4e` | `ContinuidadPage` | `test_continuidad_1360.py` |
| **1370** | `identidad.py` | 19 `/api/identidad/*` | 5 `identidad.*` | `1370a1b2c3d4e` | `AdminIdentidadPage` | `test_identidad_1370.py` |
| **1380** | `scim.py` + ext. `identidad.py` | 15 `/scim/v2/*` + 8 admin SCIM | 0 (reusa `identidad.*`) | `1380a1b2c3d4e` | mod. `AdminIdentidadPage` | `test_scim_1380.py` |

**Dependencias de incorporación (no doble contar):**

```
1260 → 1290
1280 → 1310, 1320 → 1340
1300 → 1370 → 1380
1270, 1330, 1350, 1360 — hojas independientes
```

---

## 3. Matriz maestra de control

**Leyenda de estados:**

| Estado | Significado |
|--------|-------------|
| **PRESENTE** | Verificado en la fase |
| **A INCORPORAR** | Debe aparecer al integrar el bloque |
| **PENDIENTE INTEGRACIÓN** | Bloque fuera de alcance de la fase actual |
| **NO APLICA** | No corresponde al bloque |
| **PERDIDO** | Existía en fase anterior y desapareció — **hallazgo crítico** |

### 3.1 Matriz — preservación BASE (bloques 1100–1250 + V1)

| CAPACIDAD | BLOQUE | BACKEND | API | FRONTEND | PERMISO | MIGRACIÓN | TEST | BASE | FASE 1 | FASE 2 | FINAL | ESTADO |
|-----------|--------|---------|-----|----------|---------|-----------|------|------|--------|--------|-------|--------|
| Oportunidades operativo | 1100 | `oportunidades.py` | 14 ep. | 2 páginas | 5 | — | `test_bloque_1100_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| FinOps trazabilidad | 1110 | `finops.py` | 13 ep. | `CostosValorPage` | 4 | `1110a1` | `test_finops_1110` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Señales reales | 1120 | `senales.py` | 5 ep. | 2 páginas | — | `1120a1` | `test_senales_reales_1120` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Línea base | 1200 | `linea_base.py` | 8 ep. | 2 páginas | 3 | `1200a1` | `test_bloque_1200_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Valoración ROI | 1210 | `valoracion.py` | 8 ep. | en Oportunidad | 4 | `1210b2` | `test_valoracion_1210` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Diagnóstico transversal | 1220 | `diagnosticos.py` | 8 ep. | 2 páginas | 4 | `1220a1` | `test_diagnostico_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Centro de Control | 1230 | `control_center.py` | 2 ep. | `CentroControlPage` | 1 | — | `test_bloque_1230_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Inteligencia Externa | 1240 | `inteligencia_externa.py` | 13 ep. | 2 páginas | 4 | `1240c3` | `test_inteligencia_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Convergencia 1250 | 1250 | adapters | — | CC integrado | — | `1250a/b/f` | `test_convergencia_*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| RBAC / auth V1 | V1 | `auth.py`, `admin.py` | 18 ep. | Admin* | 15+ | `d1e2f3` | `test_security_rbac_v1` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Multitenant V1 | V1 | `platform.py`, `tenant_service` | 5 ep. | Admin empresas | 3 | `c1a2b3` | `test_multitenant_v1` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| LLM Gateway V1 | V1 | `llm_providers.py` | 7 ep. | Admin LLM | 3 | `b950a1` | `test_llm_gateway_v1` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Knowledge auth V1 | V1 | `knowledge.py` | 27 ep. | Knowledge* | 5 | — | `test_knowledge_930` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| DATABASE_URL seguro | V1 | `db_url.py` | — | — | — | — | `test_docker_database_url` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Bootstrap/JWT/CORS prod | V1 | `security_config.py` | — | — | — | — | `test_p0_precertificacion_v1` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Operaciones 940 | plat. | `operations.py` | 21 ep. | 3 páginas | 6 | — | `test_operations_940` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Automatizaciones 810 | plat. | `automations.py` | 11 ep. | 3 páginas | 8 | — | `test_automations_810*` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Conocimiento 930 | plat. | `knowledge.py` | 27 ep. | 2 páginas | 5 | — | `test_knowledge_930` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Empleados IA 802 | plat. | `agent_factory.py` | 14 ep. | wizard | 8 | — | `test_agent_factory_e2e` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |
| Migración control | 1250 | `migration_control.py` | — | — | — | ledger | `test_migration_control` | PRESENTE | PRESENTE | PRESENTE | PRESENTE | OK |

### 3.2 Matriz — incorporación FASE 1 (D en curso)

| CAPACIDAD | BLOQUE | BACKEND | API | FRONTEND | PERMISO | MIGRACIÓN | TEST | BASE | FASE 1 | FASE 2 | FINAL | ESTADO |
|-----------|--------|---------|-----|----------|---------|-----------|------|------|--------|--------|-------|--------|
| Continuidad / resiliencia | 1360 | `continuidad.py` | 31 ep. | `ContinuidadPage` | 10 | `1360a1` | `test_continuidad_1360` | — | A INCORPORAR | — | PRESENTE | PENDIENTE |
| Gobierno de datos | 1350 | `governance.py` | 41 ep. | `GobernanzaDatosPage` | 7 | `1350a1` | `test_governance_1350` | — | A INCORPORAR | — | PRESENTE | PENDIENTE |
| Merge Alembic 1350∥1360 | 1250+ | — | — | — | — | merge rev. | `assert_single_head` | — | A INCORPORAR | — | 1 cabeza | PENDIENTE |
| Seguridad avanzada MFA | 1300 | `security.py` | 14 ep. | `MiSeguridadPage` | 4 | `1300a1`* | `test_bloque_1300_*` | — | A INCORPORAR | — | PRESENTE | PENDIENTE |
| Identidad empresarial SSO | 1370 | `identidad.py` | 19 ep. | `AdminIdentidadPage` | 5 | `1370a1` | `test_identidad_1370` | — | A INCORPORAR | — | PRESENTE | PENDIENTE |
| Aprovisionamiento SCIM | 1380 | `scim.py` | 23 ep. | mod. Identidad | — | `1380a1` | `test_scim_1380` | — | A INCORPORAR | — | PRESENTE | PENDIENTE |

> *`1300a1` en rama fuente apunta a `1250a`; en convergencia debe re-anclarse a `1250f` o HEAD vigente post-merge 1350∥1360.

### 3.3 Matriz — incorporación FASE 2 y posteriores

| CAPACIDAD | BLOQUE | BACKEND | API | FRONTEND | PERMISO | MIGRACIÓN | TEST | BASE | FASE 1 | FASE 2 | FINAL | ESTADO |
|-----------|--------|---------|-----|----------|---------|-----------|------|------|--------|--------|-------|--------|
| Aprendizaje repriorización | 1260 | `aprendizaje.py` | 11 ep. | 2 páginas | 4 | `1260a1` | `test_aprendizaje_1260` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Multiproveedor observabilidad | 1270 | ext. LLM | 8 ep. | mod. Admin LLM | 0 | `1270a1` | `test_bloque_1270_*` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Optimización recomendaciones | 1290 | `optimizacion.py` | 12 ep. | 2 páginas | 5 | `1290a1` | `test_optimizacion_1290` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Integraciones conectores | 1330 | `integraciones.py` | 10 ep. | 3 páginas | 6 | `1330a1` | `test_integraciones_1330` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Modelo comercial valor | 1280 | `comercial.py` | 17 ep. | 2 páginas | 5 | `1280a1/b2` | `test_modelo_comercial_1280` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Segmentación planes | 1310 | `segmentacion.py` | 18 ep. | 1 página | 6 | `1310a1` | `test_segmentacion_1310` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| TCO ecosistema aliados | 1320 | `tco.py` | 26 ep. | 1 página | 6 | `1320a1` | `test_tco_1320` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |
| Implementación éxito cliente | 1340 | `implementacion.py` | 28 ep. | 2 páginas | 6 | `1340a1` | `test_implementacion_1340` | — | PENDIENTE | A INCORPORAR | PRESENTE | PENDIENTE |

### 3.4 Reglas de detección PERDIDO

Al comparar HEAD de una fase contra BASE, marcar **PERDIDO** si:

1. Un router BASE desaparece de `main.py` `include_router`
2. Un endpoint BASE deja de responder (diff OpenAPI o grep rutas)
3. Un permiso BASE sale de `permissions.py` / `ALL_PERMISSIONS`
4. Una migración BASE protegida desaparece del árbol
5. Una página/ruta BASE desaparece de `App.tsx` / `AppShell.tsx`
6. Un test focal BASE desaparece sin reemplazo equivalente
7. Un archivo V1 inmutable (`security_config.py`, `db_url.py`, etc.) es debilitado o eliminado
8. `control_center.py` o `inteligencia_externa.py` eliminados o vaciados
9. `external_models.py` o modelos 1240 eliminados
10. `CentroControlPage` deja de ser ruta índice `/`

---

## 4. Seguridad V1 inmutable — checklist

Estos **14 controles** deben permanecer **PRESENTES** tras TODAS las fases.

| # | Control | Archivo / ámbito | Verificación | BASE |
|---|---------|------------------|--------------|------|
| 1 | Bootstrap seguro prod | `security_config.py` | Rechaza password por defecto en prod/PG | PRESENTE |
| 2 | JWT producción | `security_config.py` | Mín. 32 chars; sin default inseguro | PRESENTE |
| 3 | CORS producción | `security_config.py` | Sin `*` en prod | PRESENTE |
| 4 | DATABASE_URL encoding | `db_url.py` | `URL.create` para caracteres especiales | PRESENTE |
| 5 | Precedencia DATABASE_URL | `config.py` | `.env` explícito sobre `POSTGRES_*` | PRESENTE |
| 6 | Docker env requeridos | `docker-compose.yml` | `JWT_SECRET`, `BOOTSTRAP_ADMIN_PASSWORD`, `POSTGRES_PASSWORD` | PRESENTE |
| 7 | Entrypoint migraciones | `docker_entrypoint.sh` | `validate_migrations` + `alembic upgrade head` | PRESENTE |
| 8 | Alembic URL segura | `alembic/env.py` | `resolve_database_url_from_environ()` | PRESENTE |
| 9 | Knowledge autenticado | `knowledge.py` router | Descarga con auth; sin acceso anónimo | PRESENTE |
| 10 | RBAC deny-by-default | `authorization.py` | Sin permiso → 403 | PRESENTE |
| 11 | Multiempresa | `tenant_service.py`, queries | `organization_id` en datos sensibles | PRESENTE |
| 12 | SUPERADMIN protegido | `permissions.py`, admin | Roles protegidos; break-glass restringido | PRESENTE |
| 13 | UI español | frontend páginas BASE | Labels visibles en español (no regresión) | PRESENTE |
| 14 | Secretos no versionados | repo scan | 0 secretos en código commiteado | PRESENTE |

**Pruebas de regresión V1 obligatorias tras cada fase:**

`test_security_rbac_v1.py`, `test_docker_database_url.py`, `test_knowledge_930.py`, `test_multitenant_v1.py`, `test_p0_precertificacion_v1.py`

---

## 5. Alembic — evolución planificada

### 5.1 BASE (fijada)

```
HEAD: 1250f1a2b3c4d
Cadena: … → 1250a → 1250b → 1250f
schema_repair.HEAD_REVISION = "1250f1a2b3c4d"
```

### 5.2 FASE 1 (D — en curso)

| Paso | Revisión(es) | down_revision esperado (rama fuente) | down_revision en convergencia | Cabeza tras paso |
|------|-------------|-------------------------------------|-------------------------------|------------------|
| 1. 1360 | `1360a1b2c3d4e` | `1250f1a2b3c4d` | `1250f1a2b3c4d` | `1360a1` |
| 2. 1350 | `1350a1b2c3d4e` | `1250a1b2c3d4e` *(fuente)* | `1250f1a2b3c4d` o HEAD vigente | 2 heads: `1360a1`, `1350a1` |
| 3. Merge 1350∥1360 | `1390m1` *(propuesto)* | — | `(1360a1, 1350a1)` | 1 cabeza merge |
| 4. 1300 | `1300a1b2c3d4e` | `1250a1` *(fuente)* | HEAD post-merge | +1 cadena |
| 5. 1370 | `1370a1b2c3d4e` | `1300a1` | HEAD vigente | +1 |
| 6. 1380 | `1380a1b2c3d4e` | `1370a1` | HEAD vigente | **1 cabeza** (cierre Fase 1) |

### 5.3 Fases posteriores

| Grupo | Revisiones | Dependencia | Notas |
|-------|------------|-------------|-------|
| Observabilidad | `1270a1` | paralelo a cadena comercial | Extiende `llm_providers` |
| Aprendizaje | `1260a1` → `1290a1` | secuencial | 1290 depende 1260 en rama fuente |
| Comercial | `1280a1` → `1280b2` → `1320a1` → `1340a1` → `1310a1` | secuencial (receta C) | **1310 no bloquea 1340** |
| TCO | `1320a1` | tras `1280b2` | Parte de cadena C |
| Éxito cliente | `1340a1` | tras `1320a1` | Antes de 1310 |
| Segmentación | `1310a1` | tras `1340a1` | Último en cadena C |
| Conectores | `1330a1` | **después de 1380** (receta B) | Inserción Fase 2 definida |
| Merge final | `1390f1` *(propuesto)* | todas las cabezas residuales | **1 cabeza** al cierre |

### 5.4 Bifurcaciones conocidas (rama fuente — re-anclar en convergencia)

| Revisión | down_revision en rama fuente | Re-anclar a |
|----------|------------------------------|-------------|
| `1300a1` | `1250a1b2c3d4e` | `1250f1a2b3c4d` o HEAD Fase 1 |
| `1350a1` | `1250a1b2c3d4e` | `1250f1a2b3c4d` |
| `1260a1` | `1250a1b2c3d4e` | HEAD vigente |
| `1330a1` | `1120a1b2c3d4e` | HEAD vigente |
| `1270a1` | `1210b2c3d4e5f` | HEAD vigente |

**NO crear migraciones en este documento.** Solo planificación.

---

## 6. Criterios automáticos de ABORTO

| # | Condición | Acción |
|---|-----------|--------|
| 1 | **P0 > 0** | ABORTAR |
| 2 | **P1 > 0** | ABORTAR |
| 3 | Archivo funcional BASE eliminado | ABORTAR |
| 4 | Endpoint BASE existente desaparecido | ABORTAR |
| 5 | Permiso BASE existente perdido | ABORTAR |
| 6 | Aislamiento multiempresa roto | ABORTAR |
| 7 | SUPERADMIN desprotegido | ABORTAR |
| 8 | Más de una cabeza Alembic al cierre de fase | ABORTAR |
| 9 | Migración PostgreSQL falla | ABORTAR |
| 10 | Suite con regresión (fallos nuevos vs fase anterior) | ABORTAR |
| 11 | Frontend no compila (`npm run build`) | ABORTAR |
| 12 | Seguridad V1 perdida (cualquier ítem §4) | ABORTAR |
| 13 | Estado **PERDIDO** en matriz §3 | ABORTAR |
| 14 | `control_center` o `inteligencia_externa` eliminados | ABORTAR |
| 15 | Nuevo dashboard CC creado (viola receta A) | ABORTAR |
| 16 | Wiring 1330↔1350↔1360 roto (receta B) | ABORTAR |
| 17 | Cadena comercial fuera de orden C | ABORTAR |
| 18–27 | Criterios aborto CC (receta A, §8.3) | ABORTAR |
| 28–44 | Criterios aborto comercial (receta C, §10.3) | ABORTAR |

> **P2 conocido permitido temporalmente:** SCIM rate limiting en memoria (1380) — documentar, no rechazar Fase 1 por sí solo.

---

## 7. Control de tests — batería por fase

### 7.1 Matriz de tests

| BLOQUE | TESTS FOCALES | TESTS INTEGRACIÓN | SQLITE | POSTGRESQL | FRONTEND | E2E |
|--------|---------------|-------------------|--------|------------|----------|-----|
| **BASE puente** | `test_migration_control`, `test_convergencia_final_1250`, V1 focal (5) | `test_integration_v1_final` | **774 pass** | PENDIENTE | PASS | — |
| **1100** | `test_bloque_1100_oportunidades_operativo` | con 1030 upstream | obligatorio | obligatorio | build | — |
| **1110** | `test_finops_1110` | con 950 upstream | obligatorio | obligatorio | build | — |
| **1120** | `test_senales_reales_1120` | — | obligatorio | obligatorio | build | — |
| **1200** | `test_bloque_1200_linea_base_impacto` | — | obligatorio | obligatorio | build | — |
| **1210** | `test_valoracion_1210` | con oportunidades | obligatorio | obligatorio | build | — |
| **1220** | `test_diagnostico_transversal_1220` | — | obligatorio | obligatorio | build | — |
| **1230** | `test_bloque_1230_centro_control` | `test_bloque_1250c_*` | obligatorio | obligatorio | build | — |
| **1240** | `test_inteligencia_externa_1240` | con 1250b | obligatorio | obligatorio | build | — |
| **1250** | `test_convergencia_1250a/b`, `test_convergencia_final_1250` | todos anteriores | obligatorio | obligatorio | build | — |
| **1260** | `test_aprendizaje_1260` | — | obligatorio | obligatorio | build | — |
| **1270** | `test_bloque_1270_multiproveedor` | con LLM V1 | obligatorio | obligatorio | build | — |
| **1280** | `test_modelo_comercial_1280` | — | obligatorio | obligatorio | build | — |
| **1290** | `test_optimizacion_1290` | con 1260 | obligatorio | obligatorio | build | — |
| **1300** | `test_bloque_1300_seguridad_avanzada` | con auth V1 | obligatorio | obligatorio | build | — |
| **1310** | `test_segmentacion_1310` | con 1280 | obligatorio | obligatorio | build | — |
| **1320** | `test_tco_1320` | con 1280 | obligatorio | obligatorio | build | — |
| **1330** | `test_integraciones_1330` | con finops | obligatorio | obligatorio | build | — |
| **1340** | `test_implementacion_1340` | con 1320 | obligatorio | obligatorio | build | — |
| **1350** | `test_governance_1350` | — | obligatorio | obligatorio | build | — |
| **1360** | `test_continuidad_1360` | — | obligatorio | obligatorio | build | — |
| **1370** | `test_identidad_1370` | con 1300 | obligatorio | obligatorio | build | — |
| **1380** | `test_scim_1380` | con 1370 | obligatorio | obligatorio | build | — |

### 7.2 Batería acumulativa por fase

| Tras fase | Comando mínimo |
|-----------|----------------|
| **BASE** | Suite completa SQLite (774+) + `npm run build` + tests V1 focal |
| **FASE 1** | BASE + `test_continuidad_1360` + `test_governance_1350` + `test_bloque_1300_*` + `test_identidad_1370` + `test_scim_1380` + `assert_single_head` |
| **FASE 2** | FASE 1 + tests 1260/1270/1290/1330 + cadena C + wiring B (29 focal) + CC A (48) |
| **FINAL** | Todos los tests §7.1 + PostgreSQL real + frontend + matriz 94 |

**Referencias de prueba por insumo:**

| Insumo | Pruebas documentadas |
|--------|---------------------|
| **A (CC)** | 48 pruebas integración CC |
| **B (wiring)** | 29 focales + regresión + roundtrip + frontend |
| **C (comercial)** | Tests por bloque + 17 criterios aborto |

---

## 8. Control Centro de Control — insumo A (cerrado)

**Documento fuente:** `CURSOR_RECETA_INTEGRACION_FINAL_CENTRO_CONTROL_POST_V1.md`

### 8.1 Resultado cerrado

| Campo | Valor |
|-------|-------|
| **Bloque ancla** | 1230 (Centro de Control existente) |
| **Dashboard único** | **SÍ** — extender `CentroControlPage`, **NO crear otro dashboard** |
| **Endpoint principal** | `GET /api/centro-control/resumen-ejecutivo` |
| **Endpoints nuevos obligatorios** | **0** |
| **Secciones del resumen** | **12** |
| **Integraciones con bloques** | **14** |
| **Adaptadores** | **14** (`control_center_adapters.py`) |
| **Alertas** | **22** |
| **Acciones** | **22** |
| **Gaps UI conocidos** | **4** (P2 documentados; no bloquean Fase 1) |
| **Pruebas integración CC** | **48** |
| **Criterios de aborto CC** | **10** |

### 8.2 Integración por bloque (extensión del CC existente)

La integración final **extiende** el Centro de Control 1230. Cada bloque incorporado debe aportar datos vía adaptadores al resumen ejecutivo — sin routers CC nuevos.

| Bloque | Integración CC (receta A) | Adaptador | Alertas | Acciones | Fase |
|--------|---------------------------|-----------|---------|----------|------|
| 1260 | Aprendizaje / repriorización | Sí | Sí | Sí | FASE 2 |
| 1270 | Observabilidad multiproveedor LLM | Sí | Sí | Sí | FASE 2 |
| 1280 | KPIs comerciales / propuestas | Sí | Sí | Sí | FASE 2 |
| 1290 | Recomendaciones optimización | Sí | Sí | Sí | FASE 2 |
| 1300 | Eventos seguridad / MFA | Sí | Sí | Sí | FASE 1 |
| 1310 | Segmentación / planes | Sí | Sí | Sí | FASE 2 |
| 1320 | TCO / aliados | Sí | Sí | Sí | FASE 2 |
| 1330 | Salud conectores | Sí | Sí | Sí | FASE 2 (post-1380) |
| 1340 | Implementación / éxito cliente | Sí | Sí | Sí | FASE 2 |
| 1350 | Riesgo datos / privacidad | Sí | Sí | Sí | FASE 1 |
| 1360 | Continuidad / incidentes / SLO | Sí | Sí | Sí | FASE 1 |
| 1370 | Identidad / SSO | Sí | Sí | Sí | FASE 1 |
| 1380 | SCIM aprovisionamiento | Sí | Sí | Sí | FASE 1 |
| 1230/1250 | Núcleo CC + adapters base | Base | Base | Base | BASE |

### 8.3 Criterios de aborto Centro de Control (receta A)

| # | Condición | Acción |
|---|-----------|--------|
| CC-A1 | Se crea un segundo dashboard ejecutivo | ABORTAR |
| CC-A2 | Desaparece `GET /api/centro-control/resumen-ejecutivo` | ABORTAR |
| CC-A3 | `CentroControlPage` deja de ser ruta `/` | ABORTAR |
| CC-A4 | `control_center.py` o `control_center_service.py` eliminados | ABORTAR |
| CC-A5 | Adaptadores BASE (1240, FinOps, diagnóstico) eliminados | ABORTAR |
| CC-A6 | Sección obligatoria del resumen (1 de 12) ausente sin justificación | ABORTAR |
| CC-A7 | Integración Fase 1 (1300/1350/1360/1370/1380) sin adaptador | FAIL Fase 2/FINAL |
| CC-A8 | Alerta o acción documentada eliminada sin reemplazo | ABORTAR |
| CC-A9 | Endpoint CC nuevo obligatorio ≠ 0 en receta A | ABORTAR si se añade sin acta |
| CC-A10 | Regresión en 48 pruebas CC al integrar bloque | ABORTAR |

---

## 9. Control integraciones 1330/1350/1360 — insumo B (cerrado)

**Documento fuente:** `CURSOR_RECETA_WIRING_1330_1350_1360.md`

### 9.1 Resultado cerrado

| Campo | Valor |
|-------|-------|
| **Puntos de wiring totales** | **14** |
| **1330 ↔ 1350** | **7** puntos |
| **1330 ↔ 1360** | **3** puntos |
| **1350 ↔ 1360** | **3** puntos |
| **P1 conocidos** | **2** (con solución definida) |
| **P2 conocidos** | **1** |
| **Eventos reutilizables** | **8** |
| **Eventos nuevos** | **2** |
| **Conflictos reales** | **9** |
| **Pruebas** | **29** focales + regresión + roundtrip + frontend |
| **Escenario post-Fase 1** | **DEFINIDO** |
| **Inserción 1330** | **Después de 1380** (Fase 2) |

### 9.2 Matriz de wiring

| ID | Par | Puntos | Tipo | Fase aplicación |
|----|-----|--------|------|-----------------|
| W-B1..W-B7 | 1330 ↔ 1350 | 7 | Linaje, exportación, clasificación, auditoría datos | FASE 2 |
| W-B8..W-B10 | 1330 ↔ 1360 | 3 | Dependencias críticas, fallback, degradado | FASE 2 |
| W-B11..W-B13 | 1350 ↔ 1360 | 3 | Retención, legal-hold, backups | FASE 1 verificar base; FASE 2 wiring completo |
| W-B14 | Transversal | 1 | Event bus / hooks compartidos | FASE 2 |

### 9.3 P1 / P2 y conflictos (receta B)

| ID | Severidad | Descripción | Solución | Bloquea Fase 1 |
|----|-----------|-------------|----------|----------------|
| P1-B1 | P1 | Conflicto permisos gobierno/conectores en hub | Unión en `permissions.py` | NO (1330 no en F1) |
| P1-B2 | P1 | Evento duplicado exportación/backup | Reutilizar evento E-03 | NO |
| P2-B1 | P2 | Latencia salud conector en CC | Adapter async documentado | NO |
| C-B1..C-B9 | Conflicto | 9 archivos hub con solapamiento real | Resolución por unión (no ciega) | Verificar en F1 hub 1350∥1360 |

**Archivos hub afectados por conflictos B:** `main.py`, `permissions.py`, `migration_ledger.json`, `schema_repair.py`, `api.ts`, `App.tsx`, `AppShell.tsx`, `auth/permissions.ts`, `conftest.py`

---

## 10. Control cadena comercial / implementación — insumo C (cerrado)

**Documento fuente:** `CURSOR_RECETA_PORTADO_CADENA_COMERCIAL_IMPLEMENTACION.md`

### 10.1 Orden funcional definitivo

```
1280 (modelo comercial)
  → 1320 (TCO / aliados)
    → 1340 (implementación / éxito cliente)
      → 1310 (segmentación — NO bloquea 1340)
```

> **Corrección respecto a versión anterior:** 1310 va **después** de 1340, no en paralelo temprano con 1280.

### 10.2 Commits fuente identificados (receta C)

| Orden | SHA | Bloque / contenido |
|-------|-----|-------------------|
| 1 | `e64676b` | 1280 — núcleo comercial |
| 2 | `64fb7d9` | 1280 — scope externo (`1280b2`) |
| 3 | `f8f5e17` | 1320 — TCO |
| 4 | `80cc277` | 1340 — implementación |
| 5 | `14f05d4` | 1340 — éxito cliente |
| 6 | `aa04780` | 1310 — segmentación |

### 10.3 Re-parent y conflictos

| Campo | Valor |
|-------|-------|
| **Re-parent migración** | `1280a1b2c3d4e` → `down_revision = 1250f1a2b3c4d` |
| **Conflictos previstos** | **12** (archivos hub + dominio comercial) |
| **Criterios de aborto** | **17** |
| **1310 bloquea 1340** | **NO** |

### 10.4 Artefactos por bloque (portado Fase 2)

| Bloque | Router | Migraciones | Permisos | Frontend | Tests |
|--------|--------|-------------|----------|----------|-------|
| **1280** | `comercial.py` | `1280a1`, `1280b2` | 5 `comercial.*` | `ComercialPage`, `ComercialPropuestaDetailPage` | `test_modelo_comercial_1280` |
| **1320** | `tco.py` | `1320a1` | 6 `tco.*` / `alianzas.*` | `TcoPage` | `test_tco_1320` |
| **1340** | `implementacion.py` | `1340a1` | 6 `implementacion.*` / `exito_cliente.*` | `ImplementacionPage`, `ImplementacionDetailPage` | `test_implementacion_1340` |
| **1310** | `segmentacion.py` | `1310a1` | 6 `segmentacion.*` / `planes.*` | `SegmentacionPage` | `test_segmentacion_1310` |

### 10.5 Criterios de aborto cadena comercial (resumen — 17 totales en receta C)

| # | Condición |
|---|-----------|
| C-C1 | Orden de portado distinto a 1280→1320→1340→1310 |
| C-C2 | `1280a` no re-anclado a `1250f` |
| C-C3 | Router `comercial.py` ausente tras 1280 |
| C-C4 | Migración `1280b2` omitida |
| C-C5 | `tco.py` incorporado antes de `1280b2` |
| C-C6 | `1340` bloqueado por ausencia de 1310 |
| C-C7..C-C17 | Conflictos hub sin resolución por unión; permisos comerciales perdidos; tests focales fallidos; regresión V1; multiempresa roto; etc. *(detalle en receta C)* |

---

## 11. Matriz 94 capacidades — mecanismo post-convergencia

La matriz anterior de **94 capacidades está desactualizada**. **NO recalcular porcentaje ahora.**

### Mecanismo de actualización (solo tras convergencia FINAL)

1. Tomar inventario integral de A (mapa completado) como catálogo maestro
2. Por cada capacidad del catálogo, cruzar con filas de §3 de este documento
3. Asignar estado: `INTEGRADO` / `PARCIAL` / `P2` / `FUTURO` / `NO APLICA`
4. Generar entregable: `INTERCAMBIO/SALIDA/CURSOR_MATRIZ_94_CAPACIDADES_POST_CONVERGENCIA.md`
5. Calcular porcentaje solo en ese documento, con acta de certificación

**Columnas propuestas para matriz 94 (futura):**

`ID | CAPACIDAD | BLOQUE | BACKEND | API | FRONTEND | PERMISO | TEST | ESTADO | NOTAS`

---

## 12. Procedimiento de comparación por fase

Cuando D (u otro agente) termine una fase:

```
1. git fetch origin
2. git rev-parse origin/<rama-fase>
3. Para cada fila §3 con BASE=PRESENTE:
   - verificar artefacto en HEAD fase
   - si ausente → marcar PERDIDO → ABORTAR
4. Para filas A INCORPORAR de la fase:
   - verificar presencia → marcar PRESENTE o fallar
5. Ejecutar batería §7.2
6. alembic heads → debe ser 1
7. Checklist §4 completo
8. Aplicar protocolo Fase 1: CURSOR_PROTOCOLO_AUDITORIA_FASE1_CONVERGENCIA.md
9. Registrar resultado en INTERCAMBIO/SALIDA/
```

---

## 13. Transición a Fase 2 (criterio preparado)

Si Fase 1 recibe veredicto **A** o **B** (ver protocolo §9):

| Elemento | Acción |
|----------|--------|
| **Nueva base acumulativa** | HEAD certificado de D tras Fase 1 |
| **Alembic ancla** | `1380a1b2c3d4e` (verificar revisión merge real de D) |
| **Fase 2 — piezas** | 1330 (post-1380), cadena C (1280→1320→1340→1310), 1260/1290/1270, extensiones CC (A) |
| **NO ejecutar** | Fase 2 hasta cierre formal gate Fase 1 |

---

## Restricciones respetadas

- NO modificado código de aplicación
- NO ramas funcionales / cherry-pick / merge / rebase
- NO migraciones creadas
- NO main, V1, PR #32
- NO Docker / OpenAI / Ollama
- NO duplicados trabajos A / B / C / D
- NO porcentaje final recalculado
- NO `git add .`

---

## Salida final

```
EMPLEADOS IA — MATRIZ MAESTRA DE CONVERGENCIA ACTUALIZADA

BASE FUNCIONAL:
4b67183af1d527684e41cad0b02d7a997d3b2499

PLACEHOLDER A:
SUSTITUIDO (receta CC — §8)

PLACEHOLDER B:
SUSTITUIDO (receta wiring 1330/1350/1360 — §9)

PLACEHOLDER C:
SUSTITUIDO (receta cadena comercial — §10)

CAPACIDADES CONTROLADAS:
68

ARTEFACTOS BASE PROTEGIDOS:
157

ENDPOINTS BASE CONTROLADOS:
220

PERMISOS CONTROLADOS:
72

VISTAS CONTROLADAS:
42

PRUEBAS BASE CONTROLADAS:
54

REFERENCIAS PRUEBA A/B/C:
48 (CC) + 29 (wiring) + focal comercial

CHECKS SEGURIDAD V1:
14

CRITERIOS DE ABORTO:
44 (14 base + 10 CC + 17 comercial + 3 wiring)

CENTRO CONTROL:
RECETA A CERRADA

INTEGRACIÓN 1330/1350/1360:
RECETA B CERRADA

CADENA COMERCIAL:
RECETA C CERRADA (1280→1320→1340→1310)

PROTOCOLO FASE 1:
CURSOR_PROTOCOLO_AUDITORIA_FASE1_CONVERGENCIA.md

PORCENTAJE FINAL RECALCULADO:
NO

MODIFICACIONES FUNCIONALES:
0

MAIN:
NO MODIFICADO

V1:
NO MODIFICADA

VEREDICTO:
LISTO PARA AUDITAR HEAD DE D
```

---

## Veredicto

**LISTO PARA AUDITAR HEAD DE D** — matriz actualizada con insumos A/B/C cerrados. Aplicar `CURSOR_PROTOCOLO_AUDITORIA_FASE1_CONVERGENCIA.md` cuando D entregue HEAD de Fase 1.
