# EMPLEADOS IA / EIAAX — AUDITORÍA FUNCIONAL PREINTEGRACIÓN V1 + V2

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** C  
**Modo:** SOLO LECTURA — sin inventario maestro EIAAX, sin modificar código  
**Fecha:** 2026-08-31  
**Árbol analizado:** convergencia Fase 2 (`dc1e6cda` / `cursor/convergencia-final-fase2-85e4`) vs baseline V1 (`e8cb853` / `cursor/v1-multitenant`)

---

## 1. ALCANCE Y DEFINICIONES

| Término | Significado en este documento |
|---|---|
| **V1** | Release instalable certificada — Paquetes A–E, multitenant, RBAC, LLM gateway, PostgreSQL. SHA ref. `e8cb853`. Alembic HEAD `d1e2f3a4b5c6`. |
| **V2 (Fase 2)** | POST-V1 + tramos 6A–6E + bloques 1100–1380 + MB-06/07/11/12 + convergencia UI. SHA ref. `dc1e6cda`. Alembic HEAD `1341a1b2c3d4e`. |
| **Integración V1+V2** | Puente/merge que debe preservar delta V1 (seguridad, Docker, knowledge auth) **y** superficie V2 (CC, Mi Trabajo, Auditor, etc.) sin regresión. |

**Principio rector:** presencia de menú ≠ funcionalidad. Cada recorrido exige verificación de API backend, permiso efectivo y aislamiento por `organization_id`.

**Referencias previas:** `CURSOR_ANALISIS_PUENTE_V1_FINAL_POST_V1.md`, `MAPA_FINAL_PLATAFORMA_FASE2.md`, `CERTIFICACION_INTEGRAL_FINAL_C_E2E.md`, `RECTIFICACION_CERTIFICACION_INTEGRAL_FINAL_C.md`.

---

## 2. RESUMEN EJECUTIVO

| Dimensión | V1 | V2 | Riesgo integración |
|---|---|---|---|
| Autenticación / sesión | JWT, login, token expiry | + MFA, SSO, sesiones (1300/1370) | Medio — guards prod V1 deben sobrevivir |
| SUPERADMIN | Platform org CRUD, cross-tenant deny | + contexto explícito CC/Mi Trabajo/finops planner | Alto — `?organization_id=` nuevo |
| Multiempresa | Matriz 8 recursos cross-tenant | + 15+ módulos V2 con aislamiento propio | **Alto** — V1 no cubre CC/Auditor/MB |
| Mi Trabajo | No existe bandeja unificada | `/api/trabajo/*` única, 6 fuentes | **Alto** — dedup G2/G3 solo en V2 |
| Empleados / Fábrica | Factory E2E baseline | + MB-06 lifecycle, aprobaciones publish | Alto |
| Auditor | No existe | MVP + ciclo Mejora→Fábrica | **Crítico** — CAS solo V2 |
| Centro de Control | 1230 básico en POST-V1 | 6E integrado, 12+ adaptadores | Alto — alias `/` `/centro-control` |
| Concurrencia | 810C/820 adversarial | + CAS auditor/fábrica post-6D | **Crítico** |
| Config / infra | DATABASE_URL, prod security | + planner MB-07, canales MB-11, planes 1310 | Medio |

**Recorridos críticos post-integración (mínimo):** login → CC → Mi Trabajo → Directorio → Auditor→Fábrica (sin doble ejecución) → Costos/Valor → RBAC 403 → multiempresa A≠B → SUPERADMIN cross-org explícito.

---

## 3. MATRIZ FUNCIONAL PREINTEGRACIÓN

Leyenda severidad: **P0** bloqueante convergencia | **P1** alto | **P2** medio | **P3** bajo.

| RECORRIDO | V1 | V2 (cambio) | RIESGO | PRUEBA DE CONVERGENCIA | SEV |
|---|---|---|---|---|---|
| **Login JWT** | `/api/auth/login`, bootstrap admin, org activa | Igual + validaciones prod endurecidas (heredadas puente) | Rechazo login org inactiva roto | `test_shell_830.py`, `test_multitenant_v1::test_inactive_company_blocks_login`, `test_security_rbac_v1::test_inactive_user_login_rejected` | P1 |
| **Token expirado / inválido** | 401 en rutas protegidas | Igual | Bypass accidental en rutas nuevas V2 | `test_security_rbac_v1::test_expired_token_rejected` + smoke POST integración en CC/trabajo | P1 |
| **SUPERADMIN — listar/crear empresas** | `/api/platform/organizations` | Igual; KPI CC enlaza `/administracion/empresas` (fix convergencia) | Enlace roto a orgs | `test_multitenant_v1::test_superadmin_can_list_and_create_company`, `test_convergencia_final_fase2::test_convergencia_kpi_organizaciones_enlace` | P1 |
| **SUPERADMIN — contexto cross-org CC** | No existe CC integrado | `GET /api/centro-control/resumen-ejecutivo?organization_id=` | Fuga datos org B en org A | `test_centro_control_tramo6e`, `test_bloque_1250c::test_1250c_superadmin_org_context`, `test_centro_control_porque_p1::test_cc_superadmin_org_context` | P0 |
| **SUPERADMIN — Mi Trabajo / FinOps planner** | No | `organization_id` opcional en `/api/trabajo/*`, `/api/finops/planner/*` | Contexto usuario vs org equivocado | `test_convergencia_final_fase2::test_convergencia_mi_trabajo_adapter_usa_viewer` + manual cross-org resumen | P1 |
| **Tenant admin — NO crear empresas** | 403 platform API | Igual | Elevación privilegio | `test_multitenant_v1::test_tenant_admin_cannot_create_company` | P0 |
| **Empresa inactiva** | Bloquea login y scheduler | + CC 403 empresa inactiva | Usuario fantasma en módulos V2 | `test_p0_precertificacion_v1`, `test_bloque_1250c::test_1250c_empresa_inactiva` | P0 |
| **Usuarios CRUD** | `/api/admin/users`, permisos en `/me` | + SCIM 1380, identidad 1370 | Provisioning cruzado | `test_admin_840.py`, `test_scim_1380.py` (spot) | P1 |
| **Inyección organization_id en user create** | Rechazo/ignorar | Debe mantenerse en V2 | Usuario en org ajena | `test_security_rbac_v1::test_create_user_rejects_or_ignores_organization_id_injection` | P0 |
| **Roles / permisos — viewer limitado** | Matriz 403 audit/assistant/coordinator | + ~40 códigos nuevos (CC, auditor, comms, soporte…) | Menú visible pero API abierta | `test_security_rbac_v1` (baseline) + `test_centro_control_tramo6e::test_centro_control_rbac_denied_without_permission` + `test_gate_post6d::test_concurrency_unauthorized_user_denied` | P0 |
| **Roles — no asignar admin** | Operator no asigna admin | Igual | Escalada rol | `test_security_rbac_v1::test_operator_cannot_assign_admin_role` | P0 |
| **Multiempresa — empleados** | Cross-tenant list/detail/edit denied | + factory paths | IDOR empleado | `test_multitenant_v1::test_cross_tenant_employee_*` | P0 |
| **Multiempresa — conocimiento** | Cross-tenant denied | Igual | Fuga documentos | `test_multitenant_v1::test_cross_tenant_knowledge_denied`, `test_knowledge_930.py` | P0 |
| **Multiempresa — automatizaciones** | Cross-tenant denied | Igual | Ejecución cross-org | `test_multitenant_v1::test_cross_tenant_automation_denied`, `test_automations_810c_adversarial.py` | P1 |
| **Multiempresa — operaciones/finops** | Cross-tenant denied | + drill-down finops | Costos visibles cross-org | `test_multitenant_v1::test_cross_tenant_finops_denied`, `test_finops_950_adversarial::test_drill_down_cross_tenant` | P0 |
| **Multiempresa — oportunidades/auditoría** | Cross-tenant denied | Igual | Datos analíticos cruzados | `test_multitenant_v1::test_cross_tenant_opportunities/audit_denied` | P1 |
| **Multiempresa — CC / Auditor / MB-11 / MB-12** | **No cubierto V1** | Aislamiento por org en adaptadores | **Fuga principal V2** | `test_centro_control_tramo6e::test_centro_control_tenant_isolation`, `test_mb11_comunicaciones` (cross), `test_mesa_ayuda_mb12`, `test_auditor_integracion_mi_trabajo` | P0 |
| **Centro de Control — resumen** | 1230 POST-V1 básico | 6E: 12 módulos, 6 pestañas, `valor_consolidado` | CC vacío o error crudo | `test_centro_control_tramo6e`, `test_centro_control_cableado_ejecutivo_fase2`, `test_bloque_1250c` | P1 |
| **CC — alias `/` y `/centro-control`** | Solo `/` | Rutas equivalentes + `/panel`→`/` | Rutas muertas / doble estado | `test_convergencia_final_fase2::test_convergencia_ruta_centro_control_alias` | P1 |
| **CC — drill-down a módulos** | Enlaces parciales 1100–1240 | + MB-07/11/12, auditor, mi_trabajo, integraciones panel | Menú sin API | Certificación C (23 enlaces) + `test_fase2_drill_down_enlaces` | P1 |
| **CC — Mi Trabajo resumen (no 2ª bandeja)** | N/A | Adapter usa usuario autenticado; nota “bandeja en /trabajo” | Segunda bandeja o `.first()` wrong user | `test_convergencia_final_fase2::test_convergencia_mi_trabajo_adapter_usa_viewer`, `test_bandeja_trabajo_humano.py` | P0 |
| **Mi Trabajo — bandeja única `/trabajo`** | Items dispersos (ops, notif) | `/api/trabajo/items` unificado, dedup | Duplicados auditor/1290/comms | `test_bandeja_trabajo_humano.py`, `test_gate_post6d::test_g2/g3`, integraciones auditor/mb11/mesa | P0 |
| **Mi Trabajo — contexto usuario** | N/A | Items filtrados por user/org del token | Items de otro usuario | `test_auditor_integracion_mi_trabajo`, `test_mesa_ayuda_integracion_mi_trabajo` | P1 |
| **Directorio / Empleados IA** | `/directorio`, `/api/agent-factory/employees` | + lifecycle MB-06, estados publish/approve | Regresión factory E2E | `test_agent_factory_e2e.py`, `test_employee_lifecycle_factory_mb06.py` | P1 |
| **Fábrica — ciclo publish/approve** | certify→publish→activate | + `request-approval`, high-impact ops, segregación UI | Auto-publish sin humano | `test_employee_lifecycle_factory_mb06.py`, `test_auditor_factory_cycle::test_contrato_fabrica_no_auto_execution` | P0 |
| **Auditor — ejecutar / hallazgos** | No existe | `/api/empleados-auditor/*`, salud determinística | Hallazgo cross-org | `test_employee_auditor_mvp.py`, `test_auditor_integracion_mi_trabajo.py` | P1 |
| **Auditor → Mi Trabajo → Fábrica** | No existe | Ciclo completo con trazabilidad | Ruta rota post-merge | `test_auditor_factory_cycle.py` (9 tests) | P0 |
| **Auditor/Fábrica — CAS concurrencia** | No existe | `_atomic_claim_trace_execution`, ≤1 aprobación | **Doble ejecución** | `test_gate_post6d_correcciones.py` (-k concurrency) + carrera `test_auditor_factory_cycle`→concurrency | P0 |
| **auto_execution_blocked** | Parcial (ops human gate) | Explícito en auditor adapter + G1 | Ejecución automática hallazgo | `test_gate_post6d::test_g1`, `test_auditor_factory_cycle` | P0 |
| **Aprobación humana — oportunidades** | 1030 proactive chain | + G4 optimización AUTOMÁTICA ≠ autoaprobación | Bypass aprobación opp | `test_oportunidades_proactivas_1030.py`, `test_gate_post6d::test_g4` | P0 |
| **Aprobación humana — 1290** | No | Ejecución humana pendiente en bandeja | Auto-ejecución recomendación | `test_optimizacion_1290.py`, `test_bandeja_trabajo_humano` | P1 |
| **Costos y Valor — `/costos-valor` canónico** | FinOps 950 + página costos | 1110 extendido + MB-07 planner; CC solo resumen | Segunda vista FinOps / enlace roto | `test_finops_1110.py`, `test_consumption_planner_mb07.py`, `test_convergencia` + permisos `permissions.ts` | P1 |
| **Costos — aislamiento** | Cross-tenant finops denied | + planner contract por org | Presupuesto org A en B | `test_multitenant_v1::test_cross_tenant_finops_denied`, `test_consumption_planner_mb07` | P0 |
| **Comunicaciones MB-11** | No | Canales, plantillas, envío, contrato CC/Mi Trabajo | SMTP/webhook cross-org | `test_mb11_comunicaciones.py`, `test_mb11_integracion_mi_trabajo.py` | P1 |
| **Mesa de Ayuda MB-12** | No | Casos, SLA, contrato CC/Mi Trabajo | Casos cross-org | `test_mesa_ayuda_mb12.py`, `test_mesa_ayuda_integracion_mi_trabajo.py` | P1 |
| **Oportunidades 1100** | Baseline + multitenant | Estados operativos en CC | KPI CC desalineado | `test_bloque_1100_oportunidades_operativo.py`, `test_convergencia_final_1250` | P2 |
| **Optimización 1290** | No | Simular, aprobar, ejecutar humano | Dedup con Mi Trabajo | `test_optimizacion_1290.py`, `test_gate_post6d::test_g3` | P1 |
| **Integraciones 1330** | No | Conectores, ejecución, trazabilidad | Credenciales cross-org | `test_integraciones_1330.py`, `test_wiring_1330_fase1.py` | P1 |
| **Automatizaciones 810** | Wizard, runs, scheduler | Sin bloque nuevo; alimenta Mi Trabajo | Timeout/fencing roto | `test_automations_810c.py`, `test_automations_810c_adversarial.py` | P1 |
| **Conocimiento 930** | Upload, search, grants, cross-tenant | Descarga auth (delta V1); CC sin módulo dedicado | Descarga sin token (regresión V1) | `test_knowledge_930.py`, `test_docker_database_url` (puente) | P0 |
| **Proveedores IA — gateway V1** | OpenAI/Ollama, fallback, FinOps audit | Base para 1270 | Inferencia sin audit | `test_llm_gateway_v1.py`, `test_integration_v1_final.py` | P1 |
| **Proveedores IA — 1270 multiproveedor** | No | Anthropic/Azure/Gemini, health, observabilidad | Routing incorrecto post-merge | `test_bloque_1270_multiproveedor.py`, CC gaps LLM | P1 |
| **Notificaciones 820** | In-app, rules, adversarial race | MB-11 usa eventos; Mi Trabajo dedup | Doble notificación | `test_notifications_820.py`, `test_notifications_820_adversarial.py`, `test_mb11_integracion_mi_trabajo` | P2 |
| **Trazabilidad — FinOps 1110** | 950 baseline | Costo↔oportunidad en CC cadena | Cadena rota | `test_finops_1110.py`, `test_bloque_1250c` | P2 |
| **Trazabilidad — Auditor→Fábrica** | No | `evidence_json`, `human_decision`, audit log | Pérdida trazas | `test_auditor_factory_cycle::test_authorized_train_and_traceability` | P1 |
| **Trazabilidad — Integraciones** | No | Trazabilidad conector | Ejecución sin log | `test_integraciones_1330.py` | P2 |
| **Config — DATABASE_URL / Docker** | Delta V1 exclusivo | Debe preservarse en merge | Arranque PG roto | `test_docker_database_url.py`, `test_db_startup_805d/805e` | P0 |
| **Config — prod security (JWT/CORS/bootstrap)** | Delta V1 | Debe preservarse | Prod inseguro | `test_security_rbac_v1` (prod guards) | P0 |
| **Config — admin `/api/admin/config`** | Org settings | + planner MB-07, canales MB-11 | Config cross-org | `test_admin_840.py`, `test_consumption_planner_mb07`, `test_mb11_comunicaciones` | P1 |
| **Config — onboarding org** | Slug único, bootstrap | Igual | Org duplicada | `test_prerelease_v1_corrections.py`, `test_multitenant_v1::test_duplicate_slug_rejected` | P1 |
| **Migraciones Alembic** | HEAD `d1e2f3` | HEAD `1341a1b2c3d4e` | Multi-head / drift | `test_migration_control.py`, `validate_migrations` script | P0 |
| **G1 — desviación autorizada** | No | Auditor→Fábrica exige `authorize_deviation` | Ejecución sin decisión humana | `test_gate_post6d::test_g1` | P0 |
| **G2 — sin duplicar obligación Mi Trabajo** | No | Auditor aprobación única | 2 ítems bandeja | `test_gate_post6d::test_g2` | P0 |
| **G3 — dedup 1290 vs oportunidad** | No | Una fila optimización humana | 2 ítems opp+opt | `test_gate_post6d::test_g3` | P1 |
| **G4 — AUTOMÁTICA ≠ autoaprobación** | Parcial | Bloqueo explícito optimización | Auto-ejecución | `test_gate_post6d::test_g4` | P0 |
| **Estados vacíos CC** | Parcial | Mensajes legibles por módulo | Traceback crudo | `test_bloque_1250c` (sin datos), `test_correccion_focal_post6e_p1` (degradación) | P2 |
| **Frontend build / permisos rutas** | Baseline | `ROUTE_PERMISSIONS` ampliado; sin `DashboardPage` | Menú accesible sin permiso backend | `test_convergencia_final_fase2`, `npm run build` | P1 |
| **Identidad / SSO / SCIM (1370/1380)** | No | SSO, SCIM, MFA 1300 | Superficie auth nueva sin gate V1 | `test_identidad_1370.py`, `test_scim_1380.py`, `test_bloque_1300` | P2 |
| **Comercial 1280–1340** | No | Comercial, TCO, implementación, segmentación | CC comercial margen restringido roto | `test_modelo_comercial_1280.py`, `test_cierre_comercial_valor_pre_fase2.py` | P2 |
| **Aprendizaje 1260** | No | Ciclos aprendizaje en CC | Enlace roto | `test_aprendizaje_1260.py` | P3 |
| **Continuidad 1360** | No | Resumen CC salud | Incidentes cross-org | `test_continuidad_1360.py` | P2 |
| **Gobernanza datos 1350** | No | `/gobernanza-datos` | Sin tests focal fuerte | `test_governance_1350.py` | P3 |

---

## 4. PRUEBAS EXISTENTES vs FALTANTES (CONVERGENCIA)

### 4.1 Suites V1 que DEBEN ejecutarse post-integración (no sustituibles)

| Suite | Rol |
|---|---|
| `test_multitenant_v1.py` | Matriz canonical cross-tenant (14 tests) |
| `test_security_rbac_v1.py` | RBAC adversarial + prod config |
| `test_integration_v1_final.py` | Superadmin + LLM finops integration |
| `test_llm_gateway_v1.py` | Gateway V1 |
| `test_p0_precertificacion_v1.py` | Org inactiva, scheduler |
| `test_docker_database_url.py` | DATABASE_URL delta V1 |
| `test_prerelease_v1_corrections.py` | Onboarding org |
| `test_knowledge_930.py` | Conocimiento + tenant |

### 4.2 Suites V2 que DEBEN ejecutarse post-integración (recorridos nuevos)

| Suite | Rol |
|---|---|
| `test_convergencia_final_fase2.py` | Alias CC, KPI orgs, Mi Trabajo viewer |
| `test_gate_post6d_correcciones.py` | G1–G4 + CAS concurrencia |
| `test_auditor_factory_cycle.py` | Ciclo E2E Auditor→Fábrica |
| `test_bandeja_trabajo_humano.py` | Bandeja única |
| `test_centro_control_tramo6e.py` + cableado + 1250c | CC integrado |
| `test_mb11_*`, `test_mesa_ayuda_*` | Comunicaciones + soporte |
| `test_optimizacion_1290.py` | Optimización humana |
| `test_consumption_planner_mb07.py` | Costos/planner |
| `test_integraciones_1330.py` | Integraciones |
| `test_migration_control.py` | Single Alembic head |

### 4.3 Pruebas FALTANTES para convergencia (huecos detectados)

| Hueco | Severidad | Prueba sugerida post-integración |
|---|---|---|
| **E2E único script login→CC→trabajo→directorio→auditor** en una sesión pytest | P1 | Nuevo test integración (1 archivo, no repetir 214) |
| **Cross-tenant simultáneo CC + Mi Trabajo + finops + comms + soporte** en un test | P0 | Parametrizar org A/B en un fixture compartido |
| **RBAC matrix V2 permission codes** (auditor, comms, support, control_center) | P1 | Extender `security_rbac_v1` o suite `rbac_fase2` |
| **PostgreSQL real** — cert docs marcan PENDIENTE | P1 | `DATABASE_URL=postgresql://… pytest` tier mínimo |
| **Merge conflict hotspots** — `conftest.py`, `main.py`, `permissions.ts` | P0 | Smoke post-merge automatizado en CI |
| **SCIM/SSO vs V1 login** coexistencia | P2 | Manual + `test_identidad_1370` spot |
| **Cherry-pick V1 sobre V2** — pérdida POST-V1 models en conftest | P0 | Diff gate: `conftest` imports 1100–1380 models |

---

## 5. RECORRIDOS CRÍTICOS POST-INTEGRAR (ORDEN RECOMENDADO)

1. **Infra:** `test_migration_control` + `test_docker_database_url` + Alembic upgrade head  
2. **Auth/RBAC:** login → token inválido → viewer 403 CC → operator no admin  
3. **Multiempresa:** org A/B — empleados, knowledge, finops, oportunidades (V1) + CC, auditor, mb11, mb12 (V2)  
4. **SUPERADMIN:** `?organization_id=` solo con permiso platform; verificar ctx  
5. **Centro Control:** `/` ≡ `/centro-control`; drill-down 23 enlaces; pestañas 6 secciones  
6. **Mi Trabajo:** una bandeja; fuentes auditor/mesa/1290/comms sin duplicar (G2/G3)  
7. **Auditor→Fábrica:** ciclo completo + carrera adversarial CAS  
8. **Aprobaciones:** factory publish, 1290 humano, G4 no auto  
9. **Costos/Valor:** `/costos-valor` único; planner MB-07 aislado  
10. **Regresión V1:** `multitenant_v1` + `llm_gateway_v1` + `knowledge_930` en verde  

---

## 6. RIESGOS TOP (NO CONFUNDIR MENÚ CON FUNCIÓN)

| # | Riesgo | Por qué el menú engaña |
|---|---|---|
| 1 | Doble ejecución auditor/fábrica | API devuelve 200 en ambos hilos sin CAS |
| 2 | Mi Trabajo duplicado | Menú muestra 1 bandeja pero metadatos crean 2 ítems |
| 3 | CC drill-down 200 pero página 404 | Enlace frontend sin `<Route>` o permiso solo UI |
| 4 | SUPERADMIN ve org B sin `?organization_id=` | Adapter usa `.first()` user (corregido en convergencia — revalidar merge) |
| 5 | V1 security bypass en rutas V2 nuevas | Router V2 sin `require_permission` |
| 6 | Alembic multi-head tras merge | App arranca pero tablas MB-11/auditor ausentes |

---

## 7. NOTIFICACIÓN

```
══════════════════════════════════════════════════════════════
 EIAAX / EMPLEADOS_IA — AUDITORÍA FUNCIONAL PREINTEGRACIÓN
 AGENTE C — SOLO LECTURA
 Matriz: 45 recorridos | P0: 18 | P1: 19 | P2: 7 | P3: 1
 Entregable: INTERCAMBIO/SALIDA/AUDITORIA_C_FUNCIONAL_PREINTEGRACION.md
 Sin ejecución de pruebas en esta tarea (análisis documental)
══════════════════════════════════════════════════════════════
```

Voz: no disponible en entorno cloud. Ausencia no bloquea.

---

*Documento de análisis preintegración. No sustituye inventario maestro EIAAX ni certificación ejecutada post-merge.*
