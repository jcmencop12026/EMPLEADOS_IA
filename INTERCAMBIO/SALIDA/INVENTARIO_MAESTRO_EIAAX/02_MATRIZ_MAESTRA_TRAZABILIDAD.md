# 02 — Matriz maestra de trazabilidad EIAAX

**Producto evaluado:** SHA `b19b04dd438f5b13b422e9a760f54fa074fb52ed`
**Fecha UTC:** 2026-08-31
**Filas evaluadas:** **136** capacidades/requerimientos

---

## Leyenda de clasificación

| Color | Significado |
|---|---|
| **VERDE** | Funciona y cumple la decisión funcional vigente |
| **AMARILLO** | Existe pero está parcial |
| **AZUL** | Existe técnicamente; falta integración o exposición |
| **ROJO** | No existe |
| **NARANJA** | Existe pero requiere adaptación importante |
| **NEGRO** | Duplicado u obsoleto |
| **MORADO** | Funciona; necesita adaptación UX transversal (Norma Visual, tablas, etc.) |
| **X** | Opción/ruta visible muerta o no funcional |

**Decisión vigente:** la más reciente documentada en INTERCAMBIO/SALIDA (Fase 2 central, convergencia C1/C2, gates certificados). Requisitos anteriores compatibles se conservan en la columna *Origen*.

---

## Resumen por color (denominador = 136)

| Color | Filas | % |
|---|---:|---:|
| VERDE | 58 | 42,6% |
| AMARILLO | 22 | 16,2% |
| MORADO | 18 | 13,2% |
| AZUL | 5 | 3,7% |
| NARANJA | 4 | 2,9% |
| NEGRO | 3 | 2,2% |
| ROJO | 24 | 17,6% |
| X | 2 | 1,5% |

**Operativo (VERDE+AMARILLO+MORADO):** 98/136 = **72,1%**
**Completo según decisión vigente (VERDE):** 58/136 = **42,6%**
**Brecha material (ROJO+NEGRO):** 27/136 = **19,9%**

---

## Columnas de la matriz

Cada fila detallada incluye: Macrobloque · Capacidad · Decisión vigente · Origen · Estado · Evidencia técnica · Evidencia visual · Backend · Frontend · Modelo/datos · Migración · Permisos · Pruebas · Terminación · Brecha · Acción · Prioridad · Dependencias · V1 comercial/POST-V1

---

## MB-01 — Control de Plataforma

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB01-01 | Auth login + sesión | VERDE | `auth.py` | `LoginPage` | `test_v1_hotfix_login.py` | — | A |
| MB01-02 | MFA TOTP | VERDE | `security.py` | `MiSeguridadPage` | `test_bloque_1300_seguridad_avanzada.py` | — | A |
| MB01-03 | SSO OIDC/SAML | VERDE | `identidad.py` | `AdminIdentidadPage` | `test_identidad_1370.py` | — | A |
| MB01-04 | SCIM provisioning | AMARILLO | `scim.py` | admin identidad | `test_scim_1380.py` | P2 | A |
| MB01-05 | Admin usuarios/roles | VERDE | `admin.py` | `/administracion/*` | `test_admin_840*.py` | — | A |
| MB01-06 | Audit log | VERDE | `audit.py` | `/auditoria` | `test_security_rbac_v1.py` | — | A |
| MB01-07 | Automatizaciones + scheduler | VERDE | `automations.py` | `/automatizaciones` | `test_automations_810*.py` | — | A |
| MB01-08 | Notificaciones | VERDE | `notifications.py` | `/notificaciones` | `test_notifications_820*.py` | — | A |
| MB01-09 | Knowledge | VERDE | `knowledge.py` | `/conocimiento` | `test_knowledge_930.py` | — | A |
| MB01-10 | Integraciones conectores | AMARILLO | `integraciones.py` | `/integraciones` | `test_integraciones_1330.py` | P2 KPI CC | A |
| MB01-11 | Gobernanza datos | VERDE | `governance.py` | `/gobernanza-datos` | `test_governance_1350.py` | — | A |
| MB01-12 | Continuidad | VERDE | `continuidad.py` | `/continuidad` | `test_continuidad_1360.py` | — | A |
| MB01-13 | Health / migration control | VERDE | `main.py` | — | `test_migration_control.py` | — | A |
| MB01-14 | Capacidades / herramientas / test-lab | VERDE | routers catálogo | `/capacidades`, `/herramientas`, `/test-lab` | `test_capabilities_850*.py` | — | A |

---

## MB-02 — Empresas / Organizaciones

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB02-01 | Perfil organización tenant | VERDE | `organization.py` | admin org | `test_multitenant_v1.py` | — | A |
| MB02-02 | Platform org CRUD SUPERADMIN | VERDE | `platform.py` | `AdminCompaniesPage` | `test_convergencia_c2.py` | — | A |
| MB02-03 | Aislamiento multiempresa | VERDE | `tenant_scope`, servicios | — | C2 A–B, multitenant | — | A |
| MB02-04 | Contexto org SUPERADMIN | VERDE | `resolve_organization_id` | `OrganizationContextBar` | C2 C,K,L | — | A |
| MB02-05 | Org inactiva bloqueada | VERDE | `ensure_organization_active` | — | C2 inactive test | — | A |

---

## MB-03 — Partners / Aliados

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB03-01 | Módulo Partners API | ROJO | — | — | — | **P1 comercial** | B |
| MB03-02 | UI gestión partners | ROJO | — | — | — | **P1 comercial** | B |
| MB03-03 | Tabla legacy `partners` | NARANJA | — | — | `test_db_startup_805d.py` | C | C |
| MB03-04 | TCO proveedores/aliados | AMARILLO | `tco.py` | `/tco` | `test_tco_1320.py` | P2 | A |

*Decisión vigente:* Partners como macrobloque propio pendiente; TCO aliados cubre ecosistema parcialmente (Tramo 4 / 1320).

---

## MB-04 — Arquitecto de Transformación

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB04-01 | Orquestador / assistant | VERDE | `assistant.py` | API | `test_orchestrator_e2e.py` | — | A |
| MB04-02 | Centro operaciones | VERDE | `operations.py` | `/operaciones` | `test_operations_940*.py` | — | A |
| MB04-03 | Ejecuciones / aprobaciones | VERDE | `operations.py` | `/ejecuciones`, `/aprobaciones` | gate G1-G4 | — | A |
| MB04-04 | Experiencia / selección equipo | VERDE | `experience.py` | — | `test_orquestador_experiencia_1010.py` | — | A |
| MB04-05 | Módulo UI "Arquitecto" dedicado | AZUL | distribuido | sin página marca | — | POST-V1 | C |
| MB04-06 | Coordinador agent factory | VERDE | `agent_factory.py` | wizard | `test_agent_factory_e2e.py` | — | A |

---

## MB-05 — Estudio / Diagnóstico de Procesos

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB05-01 | Diagnóstico transversal 1220 | VERDE | `diagnosticos.py` | `/diagnosticos` | `test_diagnostico_transversal_1220.py` | — | A |
| MB05-02 | Señales 1120 | VERDE | `senales.py` | `/senales` | `test_senales_reales_1120.py` | — | A |
| MB05-03 | Líneas base / impacto 1200 | VERDE | `linea_base.py` | `/lineas-base` | `test_bloque_1200_linea_base_impacto.py` | — | A |
| MB05-04 | Salud IPS | VERDE | `salud.py` | `/salud/diagnostico` | `test_salud_960.py` | — | A |
| MB05-05 | Inteligencia externa 1240 | VERDE | `inteligencia_externa.py` | `/inteligencia-externa` | `test_inteligencia_externa_1240.py` | — | A |
| MB05-06 | Valoración económica 1210 | VERDE | `valoracion.py` | comercial/opp | `test_valoracion_1210.py` | — | A |
| MB05-07 | Motor analítico 1000 | VERDE | servicios | — | `test_motor_analitico_1000.py` | — | A |
| MB05-08 | Wizard "Estudio procesos" marca | AZUL | vía diagnosticos | parcial | — | POST-V1 | C |
| MB05-09 | Expediente evaluación adaptativo | AMARILLO | diagnosticos + opp | detail pages | parcial | P2 | B |
| MB05-10 | Evaluación preliminar/profunda | AMARILLO | diagnosticos generar | UI básica | 1220 tests | P2 | B |

---

## MB-06 — Fábrica de Empleados IA

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB06-01 | Ciclo vida create→publish | VERDE | `agent_factory.py` | wizard | `test_employee_lifecycle_factory_mb06.py` | — | A |
| MB06-02 | Guards aprobación humana | VERDE | lifecycle | wizard | `test_auditor_factory_cycle.py` | — | A |
| MB06-03 | Certificar / test / rollback | VERDE | factory endpoints | wizard | `test_agent_factory_e2e.py` | — | A |
| MB06-04 | Directorio empleados | VERDE | list/detail | `/directorio` | e2e factory | — | A |
| MB06-05 | Auditor empleados MVP | VERDE | `empleados_auditor.py` | `/empleados/auditoria` | `test_employee_auditor_mvp.py` | — | A |
| MB06-06 | Auditor ↔ Fábrica ↔ Trabajo | VERDE | contratos | `/trabajo` | G2/G3 gate | — | A |
| MB06-07 | Densidad botones wizard | MORADO | — | wizard UX | P2 MATRIZ | P2 UX | B |

---

## MB-07 — Recursos, Capacidad y Costos

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB07-01 | FinOps único 1110 | VERDE | `finops.py` | `/costos-valor` | `test_finops_1110.py` | — | A |
| MB07-02 | MB-07 consumption planner | VERDE | planner + finops | CC pestaña IA | `test_consumption_planner_mb07.py` | — | A |
| MB07-03 | Multiproveedor LLM 1270 | VERDE | `llm_providers.py` | admin proveedores | `test_bloque_1270_multiproveedor.py` | — | A |
| MB07-04 | TCO asignación costos | VERDE | `tco.py` | `/tco` | `test_tco_1320.py` | — | A |
| MB07-05 | Consumo IA trazable | VERDE | finops records | CostosValorPage | finops 950 | — | A |

---

## MB-08 — Centro de Control BI

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB08-01 | Resumen ejecutivo API | VERDE | `control_center.py` | `CentroControlPage` | 1230/1250c/C2 | — | A |
| MB08-02 | 6 pestañas ejecutivas | VERDE | adapters | CC UI | tramo6e | — | A |
| MB08-03 | Wiring MB-07/11/12 | VERDE | `control_center_adapters.py` | CC panels | tramo6e | — | A |
| MB08-04 | Home C1-R1 RBAC-aware | VERDE | — | `HomePage` | `test_c1_r1_home_route.py` | — | A |
| MB08-05 | Badges semánticos HECHO/INFERENCIA | VERDE | CC metadata | SemanticBadge | porque_p1 | — | A |
| MB08-06 | KPI integraciones CC | AMARILLO | adapter parcial | CC gap | 1240 gaps | P2 | B |
| MB08-07 | DashboardPage huérfano | NEGRO | — | sin ruta | — | limpiar | C |
| MB08-08 | Gráficos dinámicos ejecutivos | AMARILLO | datos tabulares | sin charts avanzados | — | POST-V1 | C |

---

## MB-09 — Centro de Negocios

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB09-01 | Comercial 1280 | VERDE | `comercial.py` | `/comercial` | `test_modelo_comercial_1280.py` | — | A |
| MB09-02 | Segmentación 1310 | VERDE | `segmentacion.py` | `/comercial/segmentacion` | `test_segmentacion_1310.py` | — | A |
| MB09-03 | TCO 1320 | VERDE | `tco.py` | `/tco` | `test_tco_1320.py` | — | A |
| MB09-04 | Implementación 1340 | VERDE | `implementacion.py` | `/implementacion` | `test_implementacion_1340.py` | — | A |
| MB09-05 | Reglas POTENCIAL / credential_mode | VERDE | commercial_service | UI labels | cierre comercial | — | A |
| MB09-06 | CC wiring comercial completo | AMARILLO | parcial valor tab | links | tramo4 notes | P2 | B |
| MB09-07 | Propuestas comerciales PDF/export | AMARILLO | API | UI básica | comercial tests | P2 | B |

---

## MB-10 — Centro de Oportunidades

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB10-01 | Oportunidades 1030/1100 | VERDE | `oportunidades.py` | `/oportunidades` | 1030/1100 tests | — | A |
| MB10-02 | Pipeline activar/evaluar | VERDE | actions | detail | 1100 operativo | — | A |
| MB10-03 | Optimización 1290 | VERDE | `optimizacion.py` | `/optimizacion` | `test_optimizacion_1290.py` | — | A |
| MB10-04 | Aprendizaje 1260 | VERDE | `aprendizaje.py` | `/aprendizaje` | `test_aprendizaje_1260.py` | — | A |
| MB10-05 | Cadena CC oportunidades | VERDE | CC service | CC Resumen | 1250c | — | A |
| MB10-06 | E2E integral 1020 | VERDE | cross-module | — | `test_e2e_integral_1020.py` | — | A |

---

## MB-11 — Información y Comunicaciones

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB11-01 | Canales / plantillas / reglas | VERDE | `comunicaciones.py` | `/comunicaciones` | `test_mb11_comunicaciones.py` | — | A |
| MB11-02 | Contrato CC | VERDE | contrato-centro-control | CC | tramo6d/6e | — | A |
| MB11-03 | Contrato Mi Trabajo | VERDE | contrato-mi-trabajo | `/trabajo` | mb11 integración | — | A |
| MB11-04 | Preferencias usuario | VERDE | preferencias | UI | mb11 | — | A |

---

## MB-12 — Mesa de Ayuda / Soporte

| ID | Capacidad | Estado | Backend | Frontend | Pruebas | Prioridad | Grupo |
|---|---|---|---|---|---|---|---|
| MB12-01 | Casos / workflow | VERDE | `soporte.py` | `/soporte` | `test_mesa_ayuda_mb12.py` | — | A |
| MB12-02 | SLA / auto-case / dedup | VERDE | soporte service | detail | mb12 + 820 | — | A |
| MB12-03 | Contrato CC + Trabajo | VERDE | contratos | CC/trabajo | tramo6a | — | A |
| MB12-04 | Agentes asignables | VERDE | agentes-asignables | assign UI | mb12 | — | A |

---

## Transversal — Plataforma y gobierno

| ID | Capacidad | Estado | Evidencia | Grupo |
|---|---|---|---|---|
| TX-01 | RBAC deny-by-default | VERDE | `permissions.py`, C2 | A |
| TX-02 | Mi Trabajo bandeja única | VERDE | `trabajo.py`, G2/G3 | A |
| TX-03 | Navegación menú unificado | MORADO | `menu.ts` — sidebar largo P2 | B |
| TX-04 | Home route determinístico | VERDE | C1-R1 certificado | A |
| TX-05 | Aprobación humana G1-G4 | VERDE | gate post6d | A |
| TX-06 | Trazabilidad / correlación | VERDE | audit, events | A |
| TX-07 | PostgreSQL + Alembic 53 rev | VERDE | head `1341a1b2c3d4e` | A |
| TX-08 | Español UI | AMARILLO | labels.ts — residual EN P2 | B |
| TX-09 | Tablas EIAAX (paginación/col.) | MORADO | P2 transversal histórico | C |
| TX-10 | Ayuda contextual | AMARILLO | tooltips parciales | C |
| TX-11 | Confianza semántica | VERDE | HECHO/INFERENCIA/RECOMENDACIÓN | A |
| TX-12 | Qué/por qué/quién (CC) | VERDE | `test_centro_control_porque_p1.py` | A |
| TX-13 | ANTES/PROYECTADO/REAL | AMARILLO | líneas base parcial | B |
| TX-14 | Shadow Mode | ROJO | solo roadmap docs | C |
| TX-15 | Medición resultados post-impl | AMARILLO | implementación hitos | B |
| TX-16 | Docker prod V1 compose | X | EVOLUCIÓN POST-F2 | C |

---

## Transversal — Identidad y experiencia EIAAX

| ID | Capacidad | Estado | Evidencia | Grupo |
|---|---|---|---|---|
| ID-01 | Norma Visual EIAAX completa | ROJO | no implementada | C |
| ID-02 | Tema claro/oscuro | ROJO | — | C |
| ID-03 | Logos / iconografía EIAAX | ROJO | shell genérico | B |
| ID-04 | EIAAX HERO / CORPORATIVO | ROJO | — | C |
| ID-05 | EX 08 / EX MICRO / NODO / ÓRBITA / X | ROJO | — | C |
| ID-06 | Personalidad verbal | ROJO | — | C |
| ID-07 | Config central identidad | ROJO | — | C |
| ID-08 | Vista Entidad | ROJO | — | B |
| ID-09 | Agente EIAAX permanente UI | AMARILLO | assistant API sin persona | B |
| ID-10 | PIIAX producto hijo | ROJO | — | C |
| ID-11 | Citas/Agendamiento hijo | ROJO | — | C |
| ID-12 | Shell responsive básico | VERDE | build + MATRIZ D | A |

---

## Nota sobre numeración MB

La matriz Fase 2 interna (`MATRIZ_ESTADO_REAL_FINAL_FASE2.md`) usa MB-01=Operaciones. **Este inventario usa la taxonomía maestra del producto** (MB-01=Control Plataforma, MB-09=Centro Negocios) según instrucción de inventario.

---

## Índice de evidencia técnica principal

| Área | Rutas / archivos clave |
|---|---|
| Backend routers | `backend/app/routers/*.py` (41 routers, ~526 handlers) |
| Frontend | `frontend/src/App.tsx` (~70 rutas), `navigation/menu.ts` |
| Modelos | 29 archivos, ~230 clases SQLAlchemy |
| Pruebas | 91 archivos, 1284 funciones, 1280 PASS |
| Diseño acumulado | `INTERCAMBIO/SALIDA/*.md` (433+ documentos) |

Ver detalle por grupo en `03_CAPACIDADES_EXISTENTES.md`, `04_BRECHAS_V1_COMERCIAL.md`, `05_ROADMAP_POST_V1.md`.
