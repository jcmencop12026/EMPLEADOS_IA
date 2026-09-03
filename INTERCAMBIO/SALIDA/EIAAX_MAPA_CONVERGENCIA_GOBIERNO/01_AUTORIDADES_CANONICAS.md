# 01 — Autoridades canónicas EIAAX

**Agente:** A (análisis solo lectura)  
**Referencia propia:** Seguridad y Gobierno de Datos `c433bac`  
**Ancestro común:** BP1 `7e9abba` (migración `1405a1b2c3d4e`)  
**Fecha:** 2026-08-31

## SHAs analizados

| Rama / dominio | SHA | Migraciones post-1405 |
|----------------|-----|------------------------|
| Seguridad/Gobierno (ref.) | `c433bac` | `1410` gobierno → `1420` empresa_seguridad |
| BP2 | `ee57fab` | `1410` piiax_prep → `1420` motor_evaluacion |
| Centro Negocios | `fbfd6a2` | `1600` motor_econ → `1700` CN → `1710` cierre |
| Fábrica + Partners + Arquitecto | `2afd673` | `1410` partners → `1420` arquitecto → `1430` fábrica |
| Inteligencia Resultados | `af0e8cd` | `1410` resultados |
| Comunicaciones | `f32c815` | `1410` resultados → `1420` entregas_informe |
| Partners (solo) | `fe646d4` | `1410` partners |

---

## Tabla maestra de autoridad

| Dominio | Autoridad canónica | Consumidores (adaptar, no duplicar) |
|---------|-------------------|-------------------------------------|
| **RBAC** | `permissions.py` + `check_permission()` — deny-by-default | Todos los routers; Partners añade gate adicional |
| **Tenant / organización** | `organization_id` en toda query + membresía `User.organization_id` | Partners grant, vista entidad, comunicaciones |
| **Aprobaciones (decisión)** | `coordinator.decide_approval()` sobre `ApprovalRequest` | Fábrica, operaciones, BP2 motor acción |
| **Aprobaciones (solicitud transversal)** | `GobiernoAccionSolicitud` + `gobierno_operacional_service` | CN, BP2, dominios que requieran PROPUESTA/EJECUCIÓN |
| **Clasificación** | `gov_classification_levels` + `empresa_objeto_clasificacion` | BP1 evaluación, resultados, comunicaciones, CN |
| **Visibilidad** | `gobierno_visibilidad_log` vía `empresa_seguridad_service.set_visibilidad_nivel` | BP1 `visible_entidad`, resultados, vista entidad, CN PDF |
| **Auditoría (lectura)** | `empresa_seguridad_service.consultar_auditoria` (federada) | Centro Confianza, compliance |
| **Auditoría (escritura)** | `write_audit()` + eventos `GobiernoEvento` | Todos los servicios de dominio |
| **Evidencia** | `empresa_evidencia_vinculo` + refs de dominio | Hallazgos, aprobaciones, informes |
| **Trazabilidad** | `GET /api/empresa-seguridad/trazabilidad/{correlation_id}` | Dominios propagan `correlation_id` |
| **Políticas IA** | `gobierno_ia_policies` | Fábrica `EmployeeModelPolicy`, gateway |
| **Proveedor/modelo IA** | `llm_model_catalog` + `/api/llm` gateway | Fábrica validate-provider, FinOps |
| **Capacidad externa (no LLM)** | `ProveedorExternoAdapter` / PIIAX bridge | BP2 evaluación, integraciones 1330 |
| **Economía privada** | `economic_private_economy` + permiso `negocio.economy.private` / `finops.economy.private` | CN, motor económico, vista entidad |
| **Acciones sensibles** | `gobierno_accion_policies` (LECTURA/ANÁLISIS/PROPUESTA/EJECUCIÓN) | Coordinator, BP2, fábrica |

---

## Conflictos de doble autoridad

### C-01 — Dos motores de aprobación

| Campo | Valor |
|-------|-------|
| **ORIGEN** | CN `fbfd6a2` introduce `LocalNegocioApprovalAdapter`; Gobierno `c433bac` introduce `GobiernoAccionSolicitud`; legacy mantiene `ApprovalRequest` |
| **COMPONENTES** | `negocio_approval_adapter.py`, `gobierno_operacional_service`, `coordinator.decide_approval`, `ApprovalRequest` |
| **AUTORIDAD RECOMENDADA** | Decisión: `coordinator.decide_approval`. Solicitud transversal: `GobiernoAccionSolicitud`. CN: adaptador que delega, no tabla propia |
| **CONSERVAR** | `ApprovalRequest`, `decide_approval`, `GobiernoAccionSolicitud`, `ApprovalPort` (contrato) |
| **ADAPTAR** | `LocalNegocioApprovalAdapter` → `GobiernoNegocioApprovalAdapter` |
| **RETIRAR** | Lógica autónoma de `NegocioApprovalRecord` como fuente de verdad global |
| **RIESGO** | Dos bandejas, estados divergentes, aprobación CN sin trazabilidad gobierno |

### C-02 — Dos capas de visibilidad

| Campo | Valor |
|-------|-------|
| **ORIGEN** | BP1 `visible_entidad` en `evaluacion_models`; Gobierno `NIVELES_VISIBILIDAD`; Resultados/Comunicaciones flags locales |
| **COMPONENTES** | `evaluacion_service.set_visibilidad`, `empresa_seguridad_service.set_visibilidad_nivel`, `gobierno_visibilidad_log` |
| **AUTORIDAD RECOMENDADA** | `empresa_seguridad_service.set_visibilidad_nivel` (4 niveles) |
| **CONSERVAR** | `gobierno_visibilidad_log`, dual-write BP1 como adaptador temporal |
| **ADAPTAR** | Dominios escriben vía API gobierno; flags locales = caché derivada |
| **RETIRAR** | Endpoints que cambien visibilidad sin pasar por gobierno |
| **RIESGO** | Objeto visible en vista entidad pero RESTRINGIDO en gobierno |

### C-03 — Dos catálogos de proveedor

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Gateway LLM `b950`; Centro Confianza `catalogo_proveedores_ia` (reservado BP2); Fábrica `validate-provider` |
| **COMPONENTES** | `llm_model_catalog`, `gobierno_ia_policies`, `factory_bridge_service.validate_provider_for_test`, `evaluacion_proveedor_externo_service` |
| **AUTORIDAD RECOMENDADA** | LLM: `llm_model_catalog` + gateway. Externo: `ProveedorExternoAdapter` |
| **CONSERVAR** | Gateway, políticas gobierno, adapter PIIAX |
| **ADAPTAR** | Fábrica valida contra catálogo LLM; BP2 usa adapter externo |
| **RETIRAR** | Tercer catálogo paralelo en dominio |
| **RIESGO** | Modelo no autorizado, costos no trazados, bypass políticas IA |

### C-04 — Clasificación duplicada

| Campo | Valor |
|-------|-------|
| **ORIGEN** | Gobierno 1350 `GovClassificationLevel`; Empresa Seguridad `empresa_objeto_clasificacion`; campos sueltos en dominios |
| **COMPONENTES** | `governance_service`, `empresa_seguridad_service.asignar_clasificacion` |
| **AUTORIDAD RECOMENDADA** | `empresa_objeto_clasificacion` referenciando `gov_classification_levels` |
| **CONSERVAR** | Catálogo 1350 + capa transversal 1420 |
| **ADAPTAR** | Dominios llaman `asignar_clasificacion`; alias PUBLICA→PUBLICO |
| **RETIRAR** | Campos `clasificacion` aislados sin vínculo transversal |
| **RIESGO** | Mismo objeto con clasificaciones contradictorias |

### C-05 — Auditoría fragmentada

| Campo | Valor |
|-------|-------|
| **ORIGEN** | `audit_log`, `GovAccessLog`, `SecurityEvent`, `GobiernoEvento`, `PartnerAuditEvent` |
| **COMPONENTES** | `empresa_seguridad_service.consultar_auditoria`, `write_audit` |
| **AUTORIDAD RECOMENDADA** | Lectura federada: `consultar_auditoria`. Escritura: `write_audit` + eventos gobierno cuando aplique |
| **CONSERVAR** | Todas las tablas fuente; capa de agregación |
| **ADAPTAR** | Etiquetas español vía `empresa_audit_labels` |
| **RETIRAR** | UIs que lean solo una tabla |
| **RIESGO** | Incidente sin cadena completa en Centro Confianza |

---

## Principio de integración

> **Una autoridad, N adaptadores.** Los dominios (BP2, CN, Fábrica, Resultados, Comunicaciones, Partners) conservan modelos de negocio propios pero delegan decisiones transversales a las capas canónicas anteriores. GENERAL no debe elegir "cuál gana" por rama: debe reordenar migraciones y cablear adaptadores.

## Reservado para BP2 (P1 — no resolver en esta convergencia)

- Cierre `catalogo_proveedores_ref` en Centro Confianza
- Hook completo `GobiernoAccionSolicitud` ↔ `coordinator.decide_approval` para acciones BP2
