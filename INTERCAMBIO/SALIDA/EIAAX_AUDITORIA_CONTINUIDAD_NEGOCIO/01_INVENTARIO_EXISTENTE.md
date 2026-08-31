# 01 — Inventario de capacidades existentes

**Proyecto:** EIAAX  
**Agente:** B — Auditoría funcional / inventario de brechas  
**Base de referencia:** Centro de Negocios cierre integral — SHA `fbfd6a2`  
**Rama:** `cursor/centro-negocios-eiaax-3581`  
**Fecha auditoría:** 2026-08-31  

## Leyenda de clasificación

| Clase | Significado |
|-------|-------------|
| **OPERATIVA** | Modelo + servicio + API + migración + pruebas (+ UI cuando aplica) |
| **PARCIAL** | Capas incompletas o integración pendiente |
| **ESTRUCTURAL** | Esquema/código sin recorrido operativo completo |
| **AUSENTE** | No implementado en el producto |
| **DUPLICADA** | Solapamiento con otro módulo vigente |
| **OBSOLETA** | Código huérfano o reemplazado por versión más reciente |

## Matriz resumen por dominio

| Dominio | Clasificación | Evidencia principal |
|---------|---------------|---------------------|
| Centro de Negocios (1700/1710) | **OPERATIVA** | `negocio_models.py`, `negocio_service.py`, `centro_negocios.py`, migraciones `1700`/`1710`, `test_centro_negocios_1710.py` |
| Comercial 1280 | **OPERATIVA** + **DUPLICADA** | `commercial_models.py`, `commercial_service.py`, `comercial.py`, `ComercialPage.tsx` |
| Oportunidades 1030 | **OPERATIVA** | `opportunity_models.py`, `oportunidades.py`, `test_oportunidades_proactivas_1030.py` |
| Evaluación 1405 | **OPERATIVA** | `evaluacion_models.py`, `evaluacion_service.py`, `test_bloque_producto_1_evaluacion.py` |
| Valoración 1210 | **OPERATIVA** | `valuation_models.py`, `valuation_service.py`, `test_valoracion_1210.py` |
| Motor Económico 1600 | **OPERATIVA** + **DUPLICADA** (sobre FinOps) | `economic_motor_models.py`, `economic_motor_service.py`, `test_economic_motor_1600.py` |
| Implementación / Éxito cliente 1340 | **OPERATIVA** (camino crítico) / **PARCIAL** (sub-entidades) | `implementacion_models.py` (21 tablas), `implementacion_service.py`, `test_implementacion_1340.py` |
| Empleados IA / Fábrica | **OPERATIVA** | `orchestration_models.py`, `agent_factory.py`, `employee_lifecycle_service.py`, `test_agent_factory_e2e.py` |
| Automatizaciones 810 | **OPERATIVA** | `automation_models.py`, `automation_service.py`, `test_automations_810.py` |
| Centro de Control 1250C | **OPERATIVA** | `control_center_service.py`, `control_center_adapters.py`, `test_bloque_1250c_centro_control_integrado.py` |
| Knowledge 930 | **PARCIAL** | `knowledge_models.py`, `knowledge_service.py`; CC marca integración pendiente |
| FinOps / Consumo MB-07 | **OPERATIVA** | `finops_models.py`, `consumption_planner_models.py`, `test_finops_950.py`, `test_consumption_planner_mb07.py` |
| Facturación plataforma | **AUSENTE** | Sin módulo invoicing; referencias "facturación" son dominio Salud IPS |
| Línea base / impacto 1200 | **OPERATIVA** | `baseline_models.py`, `baseline_service.py`, `test_bloque_1200_linea_base_impacto.py` |
| Soporte MB-12 | **OPERATIVA** | `support_models.py`, `support_service.py`, `test_mesa_ayuda_mb12.py` |
| Continuidad / incidentes 1360 | **PARCIAL** | `continuidad_models.py`; separado de soporte, no unificado |
| SLA | **PARCIAL** | Políticas en `SupportSlaPolicy`; no SLA transversal post-go-live en impl |
| Reporting ejecutivo | **PARCIAL** | Distribuido en CC, comunicaciones MB-11, diagnósticos; sin módulo único |
| Onboarding organizaciones | **PARCIAL** | `platform.py` API; sin wizard UI self-service |
| Offboarding org | **AUSENTE** | Sin flujo baja tenant |
| Offboarding Empleado IA | **OPERATIVA** (mínimo) | `retire_employee` en `employee_lifecycle_service.py` |
| Renovación / expansión | **PARCIAL** | `ExitoClienteRenovacion`, `ExitoClienteExpansion`; API sin UI ni workflow |
| Cambios de alcance | **PARCIAL** | Negociación/versionado comercial; sin entidad "change request" post-contrato |
| TCO 1320 | **OPERATIVA** | Integrado en tablero implementación vía `proposal_id` |
| Integraciones 1330 | **OPERATIVA** | `integration_models.py`, `integraciones.py` |
| Gobierno datos 1350 / Identidad 1370 / SCIM 1380 | **OPERATIVA** | Migraciones y routers dedicados |
| Optimización 1290 / Aprendizaje 1260 | **OPERATIVA** | Post-operación analítica, no enlazada automáticamente a contrato |
| Auditoría plataforma | **OPERATIVA** | `audit.py`, `write_audit` transversal |
| Notificaciones 820 | **OPERATIVA** | `notifications.py` |
| Mi Trabajo (bandeja humana) | **OPERATIVA** | `trabajo_service.py`, `TrabajoPage.tsx` |
| Dashboard legacy | **OBSOLETA** | `DashboardPage.tsx` no enrutada; reemplazada por `CentroControlPage` |

---

## 1. Centro de Negocios (1700/1710)

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/negocio_models.py` — extensiones, versiones, negociación, aprobaciones, PDF, contrato, sync, fases precio |
| Enums | `backend/app/negocio_enums.py` |
| Servicio | `backend/app/services/negocio_service.py` |
| PDF | `backend/app/services/negocio_pdf_service.py` |
| Aprobaciones | `backend/app/services/negocio_approval_adapter.py` |
| Sync oportunidad | `backend/app/services/negocio_sync_service.py` |
| Router | `backend/app/routers/centro_negocios.py` — 19 endpoints |
| Migraciones | `1700a1b2c3d4e_centro_negocios_eiaax.py`, `1710a1b2c3d4e_centro_negocios_cierre.py` |
| Tests | `tests/test_centro_negocios_1700.py` (4), `tests/test_centro_negocios_1710.py` (10) |
| UI | `frontend/src/pages/CentroNegociosPage.tsx`, `CentroNegociosDetailPage.tsx` |

**Capacidades:** pipeline, propuesta desde expediente, enriquecimiento, transiciones, motor económico, negociación, versionado, PDF formal, aprobaciones multinivel, contratación, sync bidireccional oportunidad, conversión a implementación.

---

## 2. Comercial 1280

**Clasificación:** OPERATIVA · **DUPLICADA** con Centro de Negocios (misma entidad `CommercialProposal`)

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/commercial_models.py` |
| Servicio | `backend/app/services/commercial_service.py` |
| Router | `backend/app/routers/comercial.py` |
| Migración | `1280a1b2c3d4e_modelo_comercial_valor_1280.py` |
| Tests | `tests/test_modelo_comercial_1280.py` |
| UI | `ComercialPage.tsx`, `ComercialPropuestaDetailPage.tsx` |

---

## 3. Oportunidades proactivas 1030

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/opportunity_models.py` |
| Servicio | `backend/app/services/proactive_service.py` |
| Router | `backend/app/routers/oportunidades.py` — incluye `POST /{id}/resultado` |
| UI | `OportunidadesPage.tsx`, `OportunidadDetailPage.tsx` |

---

## 4. Evaluación 1405

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/evaluacion_models.py` |
| Servicio | `backend/app/services/evaluacion_service.py` |
| Router | `backend/app/routers/evaluaciones.py` |
| UI | `EvaluacionesPage.tsx`, `EvaluacionConsolePage.tsx` |

Vinculación comercial: `NegocioProposalExtension.evaluacion_id`, `create_proposal_from_expediente`.

---

## 5. Valoración económica 1210

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/valuation_models.py` — esperado, escenarios, real, costos ejecución |
| Servicio | `backend/app/services/valuation_service.py` |
| Router | `backend/app/routers/valoracion.py` |
| Adapter CC | `ValoracionAdapter` en `control_center_adapters.py` |

---

## 6. Motor Económico 1600

**Clasificación:** OPERATIVA · **DUPLICADA** (facade sobre FinOps 950/1110 y planificador MB-07)

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/economic_motor_models.py` |
| Servicio | `backend/app/services/economic_motor_service.py` |
| Router | `backend/app/routers/motor_economico.py` |
| Enlace negocio | `NegocioProposalExtension.economic_recommendation_id`, `negocio_price_decisions` |

Semántica valor: POTENCIAL no entra en `valor_realizado` (`economic_motor_service.py` L39, tests L92).

---

## 7. Implementación y éxito del cliente 1340

**Clasificación:** OPERATIVA (camino crítico) · PARCIAL (tareas, fases, entregables)

| Capa | Archivo |
|------|---------|
| Modelos | `backend/app/implementacion_models.py` — 21 tablas |
| Enums | `backend/app/implementacion_enums.py` |
| Servicio | `backend/app/services/implementacion_service.py` (~760 líneas) |
| Router | `backend/app/routers/implementacion.py` — 27 endpoints |
| Migración | `1340a1b2c3d4e_implementacion_exito_cliente_1340.py` |
| Tests | `tests/test_implementacion_1340.py` — 18 tests |
| UI | `ImplementacionPage.tsx`, `ImplementacionDetailPage.tsx` |
| CC | `ImplementacionAdapter` en `control_center_adapters.py` L1069 |

**Sub-capacidades:**

| Sub-capacidad | Clasificación |
|---------------|---------------|
| Proyectos | OPERATIVA |
| Hitos | OPERATIVA |
| Readiness | OPERATIVA |
| Piloto + go-live | OPERATIVA |
| Plan éxito / medición valor | OPERATIVA |
| Salud cliente | OPERATIVA |
| Fases | PARCIAL (solo create) |
| Tareas | PARCIAL (solo create) |
| Requisitos / bloqueadores | PARCIAL (create; sin resolver vía API) |
| Riesgos | PARCIAL (create; sin cerrar) |
| Entregables | AUSENTE |
| Dependencias JSON | ESTRUCTURAL (almacenadas, no validadas) |
| Renovación / expansión | PARCIAL (create-only API) |

---

## 8. Empleados IA y operación

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `orchestration_models.py`, `employee_audit_models.py` |
| Fábrica | `agent_factory.py`, `services/agent_factory.py` |
| Ciclo de vida | `employee_lifecycle_service.py` — configurar → certificar → activar → retirar |
| Ejecuciones | `routers/operations.py`, `coordinator.py` |
| Auditor empleados | `empleados_auditor.py`, `employee_audit_service.py` |
| UI | `DirectoryPage`, `EmployeeDetailPage`, `ExecutionsPage`, `OperationsHubPage` |

---

## 9. Automatizaciones

**Clasificación:** OPERATIVA

| Capa | Archivo |
|------|---------|
| Modelos | `automation_models.py` |
| Servicio | `automation_service.py`, `automation_scheduler.py` |
| Router | `routers/automations.py` |
| UI | `AutomationsPage.tsx`, `AutomationRunsPage.tsx` |

---

## 10. Knowledge

**Clasificación:** PARCIAL

| Capa | Archivo |
|------|---------|
| Centro conocimiento | `knowledge_models.py`, `knowledge_service.py`, `knowledge.py` |
| Ingesta empleado | `KnowledgeSource` en `orchestration_models.py` |
| UI | `KnowledgePage.tsx` |
| Gap CC | `control_center_service.py` — módulo conocimiento marcado pendiente |

---

## 11. Centro de Control

**Clasificación:** OPERATIVA

Consolida 15+ adaptadores (`OportunidadesAdapter`, `LineaBaseAdapter`, `FinOpsAdapter`, `ValoracionAdapter`, `ComercialAdapter`, `ImplementacionAdapter`, etc.) en `control_center_adapters.py`.

Endpoints: `GET /api/centro-control/resumen-ejecutivo`, `GET /api/centro-control/indicadores-config`.

---

## 12. FinOps, consumo, facturación

**Clasificación:** OPERATIVA (FinOps/consumo) · AUSENTE (facturación)

| Capa | Archivo |
|------|---------|
| FinOps | `finops_models.py`, `finops_service.py`, `finops.py` |
| Planificador MB-07 | `consumption_planner_models.py`, `consumption_planner_service.py` |
| LLM gateway | `llm_models.py`, `llm_execution.py` |
| UI | `CostosValorPage.tsx`, `CentroControlPage.tsx` (sección IA y costos) |

---

## 13. Soporte, SLA, incidentes

| Módulo | Clasificación | Evidencia |
|--------|---------------|-----------|
| Mesa ayuda MB-12 | OPERATIVA | `support_models.py`, `soporte.py`, `SoportePage.tsx` |
| Continuidad 1360 | PARCIAL | `continuidad_models.py` — incidentes DR/BCP separados de soporte |
| SLA | PARCIAL | `SupportSlaPolicy`; no SLA contractual ligado a contrato negocio |

---

## 14. Reporting, indicadores, resultados

**Clasificación:** PARCIAL (distribuido)

| Fuente | Rol |
|--------|-----|
| Centro de Control | Indicadores ejecutivos `EXECUTIVE_INDICATOR_DEFS` |
| Línea base 1200 | Medición impacto real |
| Valoración 1210 | Esperado vs real por oportunidad |
| Implementación 1340 | `ExitoClienteObjetivo`, `medir_objetivo`, salud |
| Oportunidades | `register_result` |
| Comunicaciones MB-11 | Reportes ejecutivos |
| Motor analítico 1000 | Pipeline hipótesis |

**Nota:** No construir "Inteligencia de Resultados" — capacidades distribuidas ya existen (Agente D).

---

## 15. Onboarding / organizaciones

**Clasificación:** PARCIAL

| Capa | Archivo |
|------|---------|
| Multi-tenant | `models.py` — `Organization`, `User` |
| API onboarding | `platform.py` — `POST /api/platform/organizations` |
| Identidad SSO | `identidad.py`, migración 1370 |
| SCIM | `scim.py`, migración 1380 |
| Admin UI | `AdminCompaniesPage.tsx`, `AdminOrganizationPage.tsx` |

`OrganizationPage.tsx` — **OBSOLETA** (no enrutada).

---

## 16. Renovación, expansión, upsell

**Clasificación:** PARCIAL

| Capa | Archivo |
|------|---------|
| Modelos | `ExitoClienteRenovacion`, `ExitoClienteExpansion` |
| API | `POST /api/implementacion/exito/renovaciones`, `.../expansiones` |
| Test | `test_renovacion_expansion` en `test_implementacion_1340.py` |
| UI | **AUSENTE** |
| CRM / upsell formal | **AUSENTE** — expansión es registro interno, no pipeline comercial automático |

---

## 17. Offboarding

| Ámbito | Clasificación | Evidencia |
|--------|---------------|-----------|
| Empleado IA | OPERATIVA (mínimo) | `retire_employee`, `POST .../employees/{id}/retire`, test `test_retire_employee` |
| Organización/tenant | AUSENTE | Sin API cierre org |
| Proyecto implementación | PARCIAL | Estados terminales en enum; sin workflow offboarding cliente |
| Exportación datos | PARCIAL | Gobierno datos 1350; sin export pack contractual |

---

## 18. Auditoría y notificaciones

| Módulo | Clasificación | Evidencia |
|--------|---------------|-----------|
| Auditoría plataforma | OPERATIVA | `audit.py`, `write_audit` en servicios |
| Auditoría impl | OPERATIVA | `impl_auditoria` |
| Notificaciones | OPERATIVA | `notifications.py`, `NotificationsPage.tsx` |

---

## 19. Capacidades adicionales relevantes (fuera checklist)

| Módulo | Clasificación | Notas |
|--------|---------------|-------|
| Diagnóstico 1220 | OPERATIVA | Antecedente evaluación |
| Señales 1120 | OPERATIVA | Alimenta oportunidades |
| Segmentación 1310 | OPERATIVA | Planes verticales |
| TCO 1320 | OPERATIVA | En tablero impl |
| Optimización 1290 | OPERATIVA | Post-operación, no auto-enlazada |
| Aprendizaje 1260 | OPERATIVA | Recalibración patrones |
| Experiencia 1010 | OPERATIVA | Orquestador UX |
| Integraciones 1330 | OPERATIVA | Conectores externos |
| Bandeja Mi Trabajo | OPERATIVA | Soporte + aprobaciones unificadas |

---

## Conclusión inventario

EIAAX **ya posee** un ecosistema amplio post-contratación. El núcleo **contratación → implementación → go-live → operación → medición** existe con evidencia en código, migraciones y tests. Las brechas principales no son ausencia de módulos enteros sino **integración entre capas**, **continuidad de datos en conversión**, y **ciclos de vida incompletos** en sub-entidades de implementación.
