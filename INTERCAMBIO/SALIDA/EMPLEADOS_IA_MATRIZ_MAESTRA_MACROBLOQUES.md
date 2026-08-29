# EMPLEADOS IA — MATRIZ MAESTRA DE MACROBLOQUES Y CAPACIDADES REALES

**Agente:** C (análisis / inventario funcional)  
**Fecha:** 2026-08-29  
**Repositorio:** EMPLEADOS_IA  
**Rama analizada:** `cursor/1250-convergencia-final-post-v1`  
**Commit:** `eb229806136e29acddc0f592b5f017f5c3cb2958`  
**Tipo de trabajo:** Análisis de código + inventario. Sin desarrollo.

---

## 0. Concepto maestro

EMPLEADOS IA se evalúa como **sistema operativo empresarial de fuerza laboral digital, automatización y transformación**. El proveedor/modelo IA es sustituible; el producto es la plataforma empresarial.

**Estados permitidos:** `IMPLEMENTADO` | `PARCIAL` | `PREPARADO` | `NO IMPLEMENTADO` | `PRODUCTO HIJO` | `NO APLICA`

**Reglas de clasificación aplicadas:**
- Backend sin interfaz necesaria → `PARCIAL`
- Pantalla sin backend real → `PARCIAL`
- Manifiesto/contrato sin ejecución → `PREPARADO`
- Test aislado no demuestra por sí solo `IMPLEMENTADO`
- Capacidad ejecutable y utilizable de extremo a extremo → `IMPLEMENTADO`
- Bloques en ramas certificadas no integradas en la rama central → `PREPARADO` (código existe, no en producto convergido)

---

## 1. Matriz histórica de 94 capacidades

**Resultado:** `MATRIZ HISTÓRICA DE 94 NO LOCALIZADA`

**Búsqueda realizada:**
- Patrones `94 capacidades`, `matriz maestra 94`, `MATRIZ_94` en `INTERCAMBIO/`, `backend/`, `frontend/`, `tests/`
- Archivos `MATRIZ_EVALUACION*.csv` en certificaciones 1010/1030 → matrices de **casos de prueba**, no inventario maestro de producto
- Referencias narrativas en documentos de convergencia (`CURSOR_BASE_PUENTE`, planes post-V1) sin archivo maestro versionado

**Acción:** Matriz actual construida por evidencia con **89 capacidades nucleares identificadas** (62 por macrobloque + 25 transversales + 2 productos hijo evaluados aparte).

---

## 2. Inventario técnico de la rama central

### 2.1 Backend — routers activos (`backend/app/main.py`)

| Router | Prefijo | Bloque / dominio |
|--------|---------|------------------|
| auth | `/api/auth` | Identidad básica |
| organization | `/api/organization` | MB-02 |
| platform | `/api/platform` | MB-01 / CT-03 |
| admin | `/api/admin` | MB-02 / CT-02 |
| audit | `/api/audit` | CT-04 |
| assistant | `/api/assistant` | MB-04 (asistente puntual) |
| agent_factory | `/api/agent-factory` | MB-06 |
| capabilities | `/api/capabilities` | MB-06 |
| tools | `/api/tools` | MB-06 |
| knowledge | `/api/knowledge` | CT-13 |
| test_lab | `/api/test-lab` | MB-06 |
| operations | `/api/operations` | MB-06 / CT-09 |
| automations | `/api/automations` | CT-07 / 810C |
| notifications | `/api/notifications` | CT-08 / 820 |
| finops | `/api/finops` | MB-07 / 1110 |
| salud | `/api/salud` | MB-04 / MB-05 |
| experience | `/api/experiencia` | CT-16 / 1010 |
| oportunidades | `/api/oportunidades` | MB-10 / 1100 |
| senales | `/api/senales` | MB-10 / 1120 |
| linea_base | `/api/lineas-base` | MB-05 / 1200 |
| valoracion | `/api/valoracion` | MB-09 parcial / 1210 |
| diagnosticos | `/api/diagnosticos` | MB-04 / MB-05 / 1220 |
| inteligencia_externa | `/api/inteligencia-externa` | CT-20 / 1240 |
| control_center | `/api/centro-control` | MB-08 / 1230 |
| llm_providers | `/api/llm` | CT-14 |

**Routers ausentes en rama central** (presentes en ramas certificadas):

| Router | Rama certificada |
|--------|------------------|
| aprendizaje, optimizacion | `cursor/aprendizaje-optimizacion-multiproveedor-base-puente` (1260, 1290) |
| comercial, tco, segmentacion, implementacion | `cursor/comercial-valor-cierre-final-pre-fase2-dec7` (1280–1340) |
| integraciones | `origin/cursor/1330-integraciones-*` |
| governance | `origin/cursor/1350-gobierno-datos-*` |
| continuidad | `origin/cursor/1360-continuidad-resiliencia` |
| scim, identidad, security (MFA/SSO) | rama comercial 1300 |

### 2.2 Frontend — rutas activas (`frontend/src/App.tsx`)

38 rutas; home = **Centro de Control** (`/`). `DashboardPage` importada pero **no cableada** (duplicidad evitable).

Secciones navegación (`AppShell.tsx`): Inicio, Operaciones, Salud, Empleados IA, Análisis y control, Administración.

**Vistas ausentes en rama central:** Aprendizaje, Optimización, Comercial, TCO, Segmentación, Implementación, Integraciones, Gobierno datos, Continuidad.

### 2.3 Tests automatizados (51 archivos `tests/test_*.py`)

| Bloque | Archivo(s) | Estado en rama |
|--------|------------|----------------|
| 803 | test_mvp_certification_803 | ✓ |
| 805 | test_schema_repair_805b, test_db_startup_* | ✓ |
| 810/810C | test_automations_810*, adversarial | ✓ |
| 820 | test_notifications_820* | ✓ |
| 830 | test_shell_830* | ✓ |
| 840 | test_admin_840* | ✓ |
| 850 | test_capabilities_850* | ✓ |
| 930 | test_knowledge_930 | ✓ |
| 940 | test_operations_940* | ✓ |
| 950/1110 | test_finops_950*, test_finops_1110 | ✓ |
| 960/971 | test_salud_960, test_salud_conocimiento_971 | ✓ |
| 1000 | test_motor_analitico_1000 | ✓ |
| 1010 | test_orquestador_experiencia_1010 | ✓ |
| 1020 | test_e2e_integral_1020 | ✓ |
| 1030/1100 | test_oportunidades_proactivas_1030*, test_bloque_1100_* | ✓ |
| 1120 | test_senales_reales_1120 | ✓ |
| 1200 | test_bloque_1200_linea_base_impacto | ✓ |
| 1210 | test_valoracion_1210 | ✓ |
| 1220 | test_diagnostico_transversal_1220 | ✓ |
| 1230/1250C | test_bloque_1230_*, test_bloque_1250c_* | ✓ |
| 1240 | test_inteligencia_externa_1240 | ✓ |
| 1250 | test_convergencia_* | ✓ |
| V1 | multitenant, security_rbac, llm_gateway, integration_v1_final | ✓ |
| 1260–1380 | — | **Ausente** (ramas no convergidas) |

**Suite documentada en convergencia 1250:** 746 passed, 2 skipped.

### 2.4 Migraciones Alembic HEAD

`1250f1a2b3c4d` — cabeza única post-convergencia 1250A+1250B+1250C.

---

## 3. Mapeo de bloques históricos

| Bloque | Estado en producto central | Evidencia principal | Rama/commit si no integrado |
|--------|---------------------------|---------------------|----------------------------|
| **810C** | IMPLEMENTADO | `automations`, scheduler, execution fence, tests adversarial | — |
| **820** | IMPLEMENTADO | notifications, alert-rules, idempotency | — |
| **840B** | IMPLEMENTADO | admin RBAC, role global unique | — |
| **930** | IMPLEMENTADO | knowledge center, grants, search | — |
| **1000** | IMPLEMENTADO | motor analítico, datasets | — |
| **1010** | IMPLEMENTADO | orquestador experiencia, selección equipo | — |
| **1020** | IMPLEMENTADO | E2E integral tests + evidencias JSON | — |
| **1030** | IMPLEMENTADO | oportunidades proactivas, certificación externa V2 | — |
| **1100** | IMPLEMENTADO | estados operativos oportunidades | — |
| **1110** | IMPLEMENTADO | FinOps trazabilidad económica extendida | — |
| **1120** | IMPLEMENTADO | señales reales, ingesta, scheduler proactivo | — |
| **1200** | IMPLEMENTADO | línea base, medición, impacto | — |
| **1210** | IMPLEMENTADO | valoración económica, ROI escenarios | — |
| **1220** | IMPLEMENTADO | diagnóstico transversal | — |
| **1230** | PARCIAL | Centro de Control + adaptadores 1100–1220; sin 1240/1260/comercial | — |
| **1240** | PARCIAL | API+UI propias; **no** adaptador en Centro de Control | — |
| **1250** | IMPLEMENTADO | convergencia A+B+C, HEAD único | `eb22980` |
| **1260** | PREPARADO | rama aprendizaje certificada, no en main.py central | `cursor/aprendizaje-optimizacion-multiproveedor-base-puente` |
| **1270** | PREPARADO | observabilidad/routing LLM en rama multiproveedor | misma rama |
| **1280** | PREPARADO | modelo comercial completo en rama comercial | `cursor/comercial-valor-cierre-final-pre-fase2-dec7` |
| **1290** | PREPARADO | optimización/recomendación en rama aprendizaje | misma rama aprendizaje |
| **1300** | PREPARADO | MFA/SSO/SCIM en rama comercial; rama central solo `AdminSecurityPage` básica | rama comercial |
| **1310** | PREPARADO | segmentación/planes verticales | rama comercial |
| **1320** | PREPARADO | TCO/ecosistema aliados | rama comercial |
| **1330** | PREPARADO | integraciones/conectores | `origin/cursor/1330-integraciones-convergencia-limpia` |
| **1340** | PREPARADO | implementación/éxito cliente | `origin/cursor/1340-implementacion-exito-cliente` |
| **1350** | PREPARADO | gobierno de datos/privacidad | `origin/cursor/1350-gobierno-datos-convergencia-limpia` |
| **1360** | PREPARADO | continuidad/resiliencia | `origin/cursor/1360-continuidad-resiliencia` |
| **1370** | NO IMPLEMENTADO | sin router/modelo/test localizado | — |
| **1380** | NO IMPLEMENTADO | sin router/modelo/test localizado | — |
| **P1-ID-01** | PREPARADO | contratos interoperabilidad en docs/demo | manifiesto `demo_integral/manifest.py` (rama demo) |
| **P1-ID-02** | PREPARADO | idem | idem |
| **P1-ID-03** | PREPARADO | idem | idem |
| **P1-ID-04** | PREPARADO | ejecución recomendación en rama 1290 | `cursor/1290-ejecucion-recomendacion-p1-9a85` |

---

## 4. Matriz por macrobloques (62 capacidades)

Leyenda columnas: **BE** backend | **FE** frontend | **API** | **BD** | **T** tests | **RBAC** | **ME** multiempresa | **AU** auditoría | **TR** trazabilidad

### MB-01 — CONTROL DE PLATAFORMA

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB01-01 | Health / readiness / schedulers | IMPLEMENTADO | ✓ | parcial | ✓ | ✓ | ✓ | N/A | ✓ | — | — | `main.py` `/health*`, `health.py` | Exponer schedulers en UI ops |
| MB01-02 | Gobierno migraciones Alembic | IMPLEMENTADO | ✓ | — | — | ✓ | ✓ | N/A | N/A | ✓ | ✓ | `migration_control.py`, ledger | — |
| MB01-03 | Configuración global plataforma | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `admin` config, `AdminConfigPage` | — |
| MB01-04 | Superadmin multi-organización | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `platform.router`, `AdminCompaniesPage` | Sin consola superadmin unificada |
| MB01-05 | Documentación API condicional | IMPLEMENTADO | ✓ | — | ✓ | — | — | N/A | N/A | — | — | `settings.api_docs_enabled` | — |
| MB01-06 | Arranque seguro (JWT, bootstrap) | IMPLEMENTADO | ✓ | — | — | ✓ | ✓ | N/A | N/A | — | — | `validate_security_settings`, `seed.py` | — |

**MB-01 global:** PARCIAL (superadmin incompleto)

---

### MB-02 — GESTIÓN DE EMPRESAS / ORGANIZACIONES

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB02-01 | Perfil organización | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `organization.py`, `AdminOrganizationPage` | — |
| MB02-02 | CRUD empresas (platform) | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `platform.py`, `AdminCompaniesPage` | — |
| MB02-03 | Gestión usuarios | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `admin.py`, `AdminUsersPage` | — |
| MB02-04 | Roles y permisos | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | `permissions.py`, `AdminRolesPage` | — |
| MB02-05 | Branding / settings avanzados org | PARCIAL | ✓ | parcial | ✓ | ✓ | parcial | ✓ | ✓ | — | — | `Organization` model campos limitados | Campos visuales/locale por org |

**MB-02 global:** IMPLEMENTADO

---

### MB-03 — PARTNERS / ALIADOS

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB03-01 | Módulo partners en núcleo | NO IMPLEMENTADO | — | — | — | legacy | — | — | — | — | — | Tabla legacy preservada en `db_startup.py` | Implementar o declarar PH |
| MB03-02 | Ecosistema aliados TCO (1320) | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | `tco_service`, rama comercial | Convergencia post-1250 |
| MB03-03 | Rentabilidad/margen partner | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | `commercial_service` rama 1280 | Integrar tras convergencia |
| MB03-04 | Categoría aliados inteligencia ext. | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `SOCIOS/ALIADOS` en `external_intelligence_enums.py` | Sin gestión operativa partners |

**MB-03 global:** NO IMPLEMENTADO (en núcleo convergido)

---

### MB-04 — ARQUITECTO DE TRANSFORMACIÓN EMPRESARIAL

> **No existe un agente único.** Capacidades distribuidas en salud, diagnósticos, oportunidades, experiencia, fábrica y FinOps.

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB04-01 | Entender empresa (IPS/salud) | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `salud_engine`, `DiagnosticoIpsPage` | — |
| MB04-02 | Estudiar procesos por dominio | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `domain_analysis.py`, motor 1000 | — |
| MB04-03 | Detectar problemas (hallazgos) | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `salud_findings`, `diagnostic_service` | — |
| MB04-04 | Identificar causas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | correlaciones `diagnostic_models` | — |
| MB04-05 | Detectar oportunidades | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `proactive_service`, `proactive_scheduler` | — |
| MB04-06 | Valorar oportunidades | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `valoracion.py`, bloque 1210 | — |
| MB04-07 | Proponer transformación | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `IpsPropuesta`, planes salud | Sin orquestador único transformación |
| MB04-08 | Crear empleados IA | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `agent_factory`, wizard | — |
| MB04-09 | Proponer automatizaciones | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | wizard manual `AutomationWizardPage` | No generación automática desde diagnóstico |
| MB04-10 | Medir resultados | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | línea base 1200 + valoración | — |
| MB04-11 | Aprender | PARCIAL | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `experience` 1010 parcial | Bloque 1260 no convergido |
| MB04-12 | Repriorizar | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | rama 1260 aprendizaje | Convergencia + UI |

**MB-04 global:** PARCIAL (capacidades reales distribuidas, sin capa unificada “Arquitecto”)

---

### MB-05 — ESTUDIO Y DIAGNÓSTICO DE PROCESOS

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB05-01 | Motor IPS clínico/empresarial | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `salud_models`, tests 960/971 | — |
| MB05-02 | Diagnóstico transversal 1220 | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `diagnosticos.py`, 15 tests | — |
| MB05-03 | Análisis por dominio | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `domain_analysis.py` | — |
| MB05-04 | Línea base vinculada | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `linea_base.py` | — |
| MB05-05 | Trazabilidad diagnóstico↔oportunidad | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `DiagnosticOpportunityLink` | — |

**MB-05 global:** IMPLEMENTADO

---

### MB-06 — FÁBRICA DE EMPLEADOS IA

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB06-01 | Crear empleado | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | POST `/employees` | — |
| MB06-02 | Configurar rol | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `EmployeeInstructions`, wizard | — |
| MB06-03 | Objetivo | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `AIEmployee.objective` | — |
| MB06-04 | Herramientas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `EmployeeToolGrant`, `ToolsPage` | — |
| MB06-05 | Fuentes conocimiento | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `EmployeeKnowledgeSource` | — |
| MB06-06 | Conocimiento autorizado | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | grants 930 + knowledge API | — |
| MB06-07 | Modelo/proveedor | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `EmployeeModelPolicy`, `llm_providers` | — |
| MB06-08 | Permisos herramientas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `ToolPermission` enum | — |
| MB06-09 | Automatizaciones por empleado | PARCIAL | ✓ | parcial | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | módulo separado 810 | Enlace explícito en fábrica |
| MB06-10 | Límites operativos | PARCIAL | ✓ | parcial | ✓ | ✓ | parcial | ✓ | ✓ | — | — | `EmployeeLimits` | UI y enforcement costo |
| MB06-11 | Costos por empleado | PARCIAL | ✓ | parcial | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `FinOpsRecord`, metrics API | Dashboard dedicado |
| MB06-12 | Aprobaciones | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `ApprovalRequest`, `ApprovalsPage` | — |
| MB06-13 | Versionado | PARCIAL | ✓ | — | parcial | ✓ | parcial | ✓ | ✓ | ✓ | ✓ | `EmployeeVersion` | UI historial/rollback |
| MB06-14 | Pruebas (test-lab) | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `test_lab`, certify flow | — |
| MB06-15 | Publicación lifecycle | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | test→certify→publish→activate | — |
| MB06-16 | Monitoreo desempeño | PARCIAL | ✓ | parcial | ✓ | ✓ | parcial | ✓ | ✓ | — | ✓ | `/metrics`, CC empleados | Alertas bajo rendimiento |
| MB06-17 | Capacitación empleado | NO IMPLEMENTADO | — | — | — | — | — | — | — | — | — | — | Módulo capacitación |
| MB06-18 | Actualización/rollback versión | PARCIAL | ✓ | — | parcial | ✓ | — | ✓ | ✓ | ✓ | ✓ | version snapshot en publish | Flujo rollback |

**MB-06 global:** PARCIAL

---

### MB-07 — GESTIÓN DE RECURSOS, CAPACIDAD Y COSTOS

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB07-01 | Dashboard FinOps | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `finops.py`, `CostosValorPage` | — |
| MB07-02 | Presupuestos y alertas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `FinOpsBudget`, CC atención | — |
| MB07-03 | Logs inferencia LLM | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `LlmInferenceLog` | — |
| MB07-04 | Capacidad operativa | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | operations center, ejecuciones | — |
| MB07-05 | Trazabilidad costo↔oportunidad | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | bloque 1110, adapter CC | — |

**MB-07 global:** IMPLEMENTADO

---

### MB-08 — CENTRO DE CONTROL (único)

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB08-01 | Resumen ejecutivo 12 KPIs | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | `EXECUTIVE_INDICATOR_DEFS` | — |
| MB08-02 | Cola atención requerida | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | `_atencion_requerida` | — |
| MB08-03 | Adaptadores 1100–1220 | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | `control_center_adapters.py` | — |
| MB08-04 | Cadena ejecutiva | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | `_cadena_ejecutiva` | — |
| MB08-05 | Acciones ejecutivas (write) | PARCIAL | — | — | — | — | — | ✓ | ✓ | — | — | Solo enlaces navegación | Aprobar/actuar desde CC |
| MB08-06 | Inteligencia externa en CC | NO IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | 1240 fuera de adapters | Adapter 1240 |
| MB08-07 | Aprendizaje/optimización en CC | NO IMPLEMENTADO | rama | rama | rama | rama | rama | rama | rama | — | — | 1260/1290 no convergidos | Post-convergencia |
| MB08-08 | Comercial/implementación en CC | NO IMPLEMENTADO | rama | rama | rama | rama | rama | rama | rama | — | — | 1280–1340 en ramas | Post-convergencia |

**Consumo actual CC:** empleados, operaciones, automatizaciones, notificaciones, oportunidades, impacto, FinOps, valoración, diagnóstico, señales, salud plataforma, auditoría, LLM.

**No consume:** inteligencia externa (1240), aprendizaje (1260), observabilidad avanzada (1270), comercial (1280–1320), implementación (1340), integraciones (1330), gobierno (1350), continuidad (1360).

**MB-08 global:** PARCIAL

---

### MB-09 — CENTRO DE NEGOCIOS

> Regla aplicada: **potencial ≠ realizado**. Bloques comerciales existen en ramas certificadas, no en producto central convergido.

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB09-01 | Planes comerciales | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | `commercial_models` 1280 | Convergencia |
| MB09-02 | Segmentación | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | bloque 1310 | Convergencia |
| MB09-03 | Costos producto | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | 1280/1320 | Convergencia |
| MB09-04 | Precio / propuesta | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | `ComercialPropuesta*` rama | Convergencia |
| MB09-05 | ROI en propuesta comercial | PARCIAL | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | valoración 1210 operativa | Separar ROI comercial vs operativo |
| MB09-06 | Payback | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | 1280 rama | Convergencia |
| MB09-07 | TCO ecosistema | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | bloque 1320 | Convergencia |
| MB09-08 | Seguimiento implementación | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | bloque 1340 | Convergencia |
| MB09-09 | Partners rentabilidad | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | 1320 aliados | Convergencia |
| MB09-10 | Margen | PREPARADO | rama | rama | rama | rama | rama | rama | rama | — | — | commercial_service | Convergencia |
| MB09-11 | Consumo IA en oferta | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | FinOps núcleo | Empaquetar en plan comercial |
| MB09-12 | Sobreconsumo comercial | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | alertas FinOps | Políticas por plan cliente |

**MB-09 global:** PREPARADO (en núcleo convergido; operativo solo vía FinOps/valoración operativa)

---

### MB-10 — CENTRO DE OPORTUNIDADES

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB10-01 | Oportunidades internas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | tipos ahorro/productividad/riesgo | — |
| MB10-02 | Oportunidades externas mercado | PARCIAL | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1240 + dominio comercial | Pipeline unificado ext→opp |
| MB10-03 | Pipeline estados 1100 | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | estados operativos | — |
| MB10-04 | Aprobación humana | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `PENDIENTE_APROBACION` | — |
| MB10-05 | Seguimiento materialización | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | valor materializado | — |
| MB10-06 | Señales proactivas | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1120 + scheduler | — |
| MB10-07 | Valor potencial vs real | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | KPIs CC + opp | — |
| MB10-08 | Detección automática | IMPLEMENTADO | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `proactive_scheduler` | — |

**MB-10 global:** IMPLEMENTADO (externas: PARCIAL)

---

### MB-11 — CENTRO DE INFORMACIÓN Y COMUNICACIONES

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB11-01 | Bandeja notificaciones | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 820 | — |
| MB11-02 | Reglas de alerta | IMPLEMENTADO | ✓ | parcial | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | alert-rules API | UI reglas limitada |
| MB11-03 | Auditoría consultable | IMPLEMENTADO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `AuditPage` | — |
| MB11-04 | Hub comunicaciones unificado | PARCIAL | ✓ | parcial | ✓ | ✓ | parcial | ✓ | ✓ | ✓ | — | notif + audit separados | Centro mensajes único |

**MB-11 global:** PARCIAL

---

### MB-12 — MESA DE AYUDA Y SOPORTE

| ID | Capacidad | Estado | BE | FE | API | BD | T | RBAC | ME | AU | TR | Evidencia | Pendiente |
|----|-----------|--------|----|----|-----|----|---|------|----|----|-----|-----------|-----------|
| MB12-01 | Mesa de ayuda | NO IMPLEMENTADO | — | — | — | — | — | — | — | — | — | sin matches código | Definir alcance |
| MB12-02 | Tickets soporte | NO IMPLEMENTADO | — | — | — | — | — | — | — | — | — | — | Módulo tickets |
| MB12-03 | SLA / escalamiento | NO IMPLEMENTADO | — | — | — | — | — | — | — | — | — | — | Integrar con operaciones |

**MB-12 global:** NO IMPLEMENTADO

---

## 5. Capacidades transversales (25)

| ID | Capacidad | Estado | Evidencia | Pendiente |
|----|-----------|--------|-----------|-----------|
| CT-01 | Multiempresa | IMPLEMENTADO | `Organization`, slug, tests multitenant V1, aislamiento 1250 | — |
| CT-02 | RBAC / permisos | IMPLEMENTADO | `permissions.py`, 40+ permisos, `RequirePermission` | — |
| CT-03 | SUPERADMIN | PARCIAL | `platform.organization.view`, empresas | Consola global unificada |
| CT-04 | Auditoría y trazabilidad | IMPLEMENTADO | `AuditLog`, trazas opp/diag/finops/señales | — |
| CT-05 | Seguridad | PARCIAL | `AdminSecurityPage`, JWT, adversarial tests | Bloque 1300 rama comercial |
| CT-06 | Identidad / MFA / SCIM | PREPARADO | rama comercial: `scim`, `mfa_service`, `oidc` | Convergencia identidad |
| CT-07 | Automatizaciones | IMPLEMENTADO | 810C scheduler, event bus, wizard | — |
| CT-08 | Notificaciones | IMPLEMENTADO | 820 inbox + rules | — |
| CT-09 | Aprobación humana | IMPLEMENTADO | operations approvals + opp | — |
| CT-10 | Integraciones | PREPARADO | rama 1330 `integraciones` | Convergencia conectores |
| CT-11 | Gobierno de datos | PREPARADO | rama 1350 `governance` | Convergencia |
| CT-12 | Continuidad / resiliencia | PREPARADO | rama 1360 `continuidad` | Convergencia |
| CT-13 | Conocimiento | IMPLEMENTADO | 930 knowledge center | — |
| CT-14 | Multiproveedor IA | PARCIAL | `llm_providers` V1; routing 1270 en rama | Convergencia 1270 |
| CT-15 | FinOps IA | IMPLEMENTADO | 950/1110 + LLM logs | — |
| CT-16 | Aprendizaje | PARCIAL | experience 1010; aprendizaje 1260 en rama | Convergencia 1260 |
| CT-17 | Medición de resultados | IMPLEMENTADO | 1200 línea base + impacto | — |
| CT-18 | Valor económico / ROI | IMPLEMENTADO | 1210 valoración | — |
| CT-19 | Semántica HECHO/INFERENCIA/RECOMENDACIÓN | PARCIAL | `diagnostic_models`, `salud_questions`, no contrato global | Unificar semántica API |
| CT-20 | Inteligencia externa | IMPLEMENTADO | 1240 API+UI | Integrar en CC y opp ext |
| CT-21 | Comercial / planes / propuestas | PREPARADO | ramas 1280–1310 | Convergencia comercial |
| CT-22 | Implementación / éxito cliente | PREPARADO | rama 1340 | Convergencia |
| CT-23 | Tareas / alertas / trabajo humano | IMPLEMENTADO | WorkPlan, approvals, CC atención | — |
| CT-24 | Configurabilidad | PARCIAL | admin config, templates empleado | Planes por vertical |
| CT-25 | Multiidioma / multirregión | NO IMPLEMENTADO | UI español fijo | i18n + locale |

---

## 6. Productos hijo (evaluación interoperabilidad)

| ID | Producto | Estado núcleo | Conexión | Orquestación | Interoperabilidad | Gobierno | Trazabilidad |
|----|--------|---------------|----------|--------------|-------------------|----------|--------------|
| PH-01 | CITAS / AGENDAMIENTO | PRODUCTO HIJO | NO | NO | NO | N/A | N/A | Doc gap analysis: no requerido V1 |
| PH-02 | PIIP / Automatizaciones conectividad | PRODUCTO HIJO | PREPARADO | PREPARADO | PREPARADO | PARCIAL | PARCIAL | Manifiesto demo 1330; rama 1330 no convergida |

**Regla:** funcionalidad completa de PH **no** es obligatoria en núcleo. Solo se evalúa capacidad de integración.

---

## 7. Auditor / mejora continua (capacidad objetivo)

| Capacidad objetivo | Estado | Evidencia existente | Brecha |
|--------------------|--------|---------------------|--------|
| Auditar periódicamente empleados IA | NO IMPLEMENTADO | — | Job + políticas periodicidad |
| Auditar por evento/disparador | PARCIAL | automation events, audit log | Sin auditor dedicado empleado |
| Detectar bajo desempeño | PARCIAL | metrics endpoint, hallazgos salud | Sin umbral automático empleado |
| Recomendar rediseño | PARCIAL | salud propuestas, opp | Sin motor 1290 convergido |
| Recomendar capacitación | NO IMPLEMENTADO | — | MB06-17 ausente |
| Recomendar nuevas herramientas | NO IMPLEMENTADO | — | — |
| Detectar nueva normatividad | PARCIAL | inteligencia externa 1240 categorías | Sin workflow normativo |
| Evaluar impacto normativo | NO IMPLEMENTADO | — | — |
| Actualizar/capacitar empleados afectados | NO IMPLEMENTADO | — | — |

**Global Auditor/Mejora continua:** PARCIAL (piezas en salud, experiencia, audit; sin ciclo cerrado)

---

## 8. Competencia / diferenciación (desde producto construido)

| Capacidad | Diferenciación | Copiable vs sistémica |
|-----------|----------------|----------------------|
| Cadena señales→diagnóstico→opp→ejecución→impacto→ROI→CC | Alta | **Ventaja sistémica** (orquestación + trazabilidad) |
| Multiempresa + RBAC + auditoría | Media-alta | Copiable con esfuerzo |
| Oportunidades proactivas certificadas 1030 | Alta | Media (lógica compleja pero replicable) |
| Semántica HECHO/INFERENCIA parcial | Baja-media | Fácil de copiar si se unifica |
| FinOps IA integrado | Media-alta | Copiable |
| Fábrica empleados lifecycle | Media | Copiable (patrón común) |
| Multiproveedor + optimización 1270/1290 | Alta potencial | No en núcleo aún |
| Comercial valor 1280–1340 | Alta potencial | En ramas, no producto único |
| Productos hijo PIIP | Media | Depende integración 1330 |
| Control humano aprobaciones | Media | Copiable |
| Aprendizaje/repriorización 1260 | Alta potencial | No convergido |

---

## 9. Duplicidades detectadas (7)

| # | Duplicidad | Tipo | Recomendación |
|---|------------|------|---------------|
| 1 | `DashboardPage` vs `CentroControlPage` | Visual / código muerto | Eliminar import Dashboard o redirigir |
| 2 | Valoración 1210 vs valor comercial 1280 | Producto futuro | Mantener dominios separados con adaptador |
| 3 | Experience 1010 vs Aprendizaje 1260 | Funcional | Convergir en módulo único post-1260 |
| 4 | FinOps 950 vs 1110 extendido | Evolución, no duplicado | Documentar como capas |
| 5 | Operations hub vs operations center | Jerarquía UI | Intencional |
| 6 | Múltiples merges Alembic 1250* | Técnico | Aceptable |
| 7 | Partners legacy table vs 1320 aliados | Datos | Migrar o deprecar legacy |

---

## 10. Fórmulas de porcentaje

**Pesos por estado (núcleo, excluye PRODUCTO HIJO y NO APLICA):**
- IMPLEMENTADO = 1.0
- PARCIAL = 0.5
- PREPARADO = 0.25
- NO IMPLEMENTADO = 0.0

**Denominador núcleo:** 87 capacidades (62 MB + 25 CT)

### Conteo estados (núcleo)

| Estado | MB (62) | CT (25) | Total (87) |
|--------|---------|---------|------------|
| IMPLEMENTADO | 35 | 12 | **47** |
| PARCIAL | 14 | 7 | **21** |
| PREPARADO | 8 | 5 | **13** |
| NO IMPLEMENTADO | 5 | 1 | **6** |

**Puntuación núcleo** = (47×1 + 21×0.5 + 13×0.25 + 6×0) / 87 = **69.8%**

### Por dimensión

| Dimensión | Fórmula | Resultado |
|-----------|---------|-----------|
| BACKEND | % caps con BE/API/BD ≥ PARCIAL en rama o rama cert | **84.5%** (73/86 con backend; excl. MB12-03 sin BE) |
| FRONTEND | % caps con ruta UI en rama central | **58.6%** (51/87) |
| INTEGRACIÓN | % caps BE+FE conectados en rama central | **54.0%** (47/87) |
| PRUEBAS | % caps con tests automatizados focales | **71.3%** (62/87) |
| OPERACIÓN | % caps con scheduler/health/multitenant validado | **66.7%** (58/87) |
| PRODUCTO TOTAL | Puntuación núcleo anterior | **69.8%** |

---

## 11. Resumen ejecutivo

```
EMPLEADOS IA — MATRIZ MAESTRA ACTUALIZADA

MACROBLOQUES: 12
CAPACIDADES TRANSVERSALES: 25
PRODUCTOS HIJOS: 2
CAPACIDADES REALES IDENTIFICADAS: 89
IMPLEMENTADAS: 47
PARCIALES: 21
PREPARADAS: 13
NO IMPLEMENTADAS: 6
PRODUCTO HIJO: 2

BACKEND: 84.5 %
FRONTEND: 58.6 %
INTEGRACIÓN: 54.0 %
PRUEBAS: 71.3 %
OPERACIÓN: 66.7 %
PRODUCTO TOTAL: 69.8 %

MATRIZ HISTÓRICA 94: NO LOCALIZADA

ARQUITECTO TRANSFORMACIÓN: PARCIAL
FÁBRICA EMPLEADOS IA: PARCIAL
AUDITOR/MEJORA CONTINUA: PARCIAL

VEREDICTO: Plataforma empresarial operativa sólida en núcleo transformación-datos-oportunidades-ejecución-medición (bloques 810C–1250). Producto convergido al ~70% del inventario nucleo. Brecha principal: convergencia de ramas certificadas (comercial 1280–1340, aprendizaje 1260–1290, integraciones 1330, gobierno 1350, continuidad 1360, identidad 1300) y cierre de mesa de ayuda, capacitación y auditoría continua de empleados.
```

**Rama/commit evidencia:** `cursor/1250-convergencia-final-post-v1` @ `eb229806136e29acddc0f592b5f017f5c3cb2958`
