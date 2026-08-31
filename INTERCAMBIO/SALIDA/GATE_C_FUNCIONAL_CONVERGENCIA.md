# EIAAX / EMPLEADOS_IA — GATE FUNCIONAL DE CONVERGENCIA (AGENTE C)

**Proyecto:** EIAAX / EMPLEADOS_IA  
**Agente:** C — Control EIAAX  
**Modo:** SOLO LECTURA — especificación de protección, **sin modificar producto**  
**Estado:** **EN RESERVA** — esperando SHA integrado de GENERAL  
**Fecha preparación:** 2026-08-31  
**Especificación origen:** `INTERCAMBIO/SALIDA/AUDITORIA_C_FUNCIONAL_PREINTEGRACION.md` (45 recorridos → 14 grupos)

---

## 0. PROPÓSITO Y REGLAS

Este documento define **UNA** certificación funcional coherente post-convergencia. Los 18 P0 de la auditoría preintegración **no** se traducen en 18 campañas de corrección independientes: son **criterios de gate** que deben pasar sobre el SHA integrado.

| Regla | Aplicación |
|---|---|
| No modificar código en esta fase | Solo preparación del gate |
| No merge / no tocar V1 ni V2 certificadas | Gate se ejecuta sobre SHA futuro de GENERAL |
| No duplicar PostgreSQL | Dependencia **Agente B** (ver §1) |
| No confundir menú con función | PASS exige API + permiso backend + aislamiento org |
| P0 gate fallido | Bloquea candidato final Fase 2 convergida |

### Dependencia Agente B — PostgreSQL

| Dato | Valor |
|---|---|
| V1 Alembic head | `d1e2f3a4b5c6` |
| V2 Alembic head | `1341a1b2c3d4e` |
| Relación | V2 continúa V1 sin divergencia de heads |
| Estado B | **APTO DATOS PARA CONVERGENCIA** |
| Rol en este gate | B certificará PG real sobre SHA integrado; **C no duplica** |

**Condición PASS gate C (datos):** Agente B reporta APTO sobre el mismo SHA integrado. Si B=PENDIENTE, gate C queda **CONDICIONAL** (no APTO formal).

### Ejecución futura (cuando exista SHA GENERAL)

```text
1. Verificar SHA exacto (gate 0 — abort si no coincide)
2. Agente B: PostgreSQL + migraciones (dependencia)
3. Grupos G01→G14 en orden (paralelizable G04–G12 tras G01–G03)
4. Pruebas nuevas obligatorias NX01–NX05 (§3)
5. Veredicto único APTO / NO APTO
```

---

## 1. MAPA 45 → 14 GRUPOS

| Grupo | Recorridos auditados absorbidos (de 45) |
|---|---|
| **G01** | Login JWT, token expirado, empresa inactiva, prod security JWT/CORS/bootstrap, usuarios CRUD (auth base), onboarding org |
| **G02** | Viewer limitado, operator no admin, inyección org_id, multiempresa empleados/knowledge/automation/ops/finops/opp/audit, CC/Auditor/MB cross-tenant V2 |
| **G03** | SUPERADMIN list/create org, cross-org CC, cross-org Mi Trabajo/finops planner, tenant admin no crea empresas |
| **G04** | CC resumen 6E, alias `/`≡`/centro-control`, drill-down, Mi Trabajo resumen en CC, estados vacíos, frontend build/rutas |
| **G05** | Bandeja única `/trabajo`, contexto usuario, G2 dedup auditor, G3 dedup 1290, integraciones Mi Trabajo (auditor/mb11/mesa) |
| **G06** | Auditor ejecutar/hallazgos, salud, integración Mi Trabajo, trazabilidad auditor |
| **G07** | Directorio/factory E2E, MB-06 lifecycle publish/approve, ciclo Auditor→Fábrica, CAS concurrencia, auto_execution_blocked, G1 |
| **G08** | Aprobaciones oportunidades 1030, 1290 humano, factory publish, G4 no autoaprobación |
| **G09** | Costos/valor canónico, finops 1110, MB-07 planner, aislamiento finops, drill-down, proveedores 1270 (smoke) |
| **G10** | Conocimiento 930 upload/search/grants/cross-tenant, descarga auth V1 |
| **G11** | MB-11 comunicaciones, contrato CC/Mi Trabajo, cross-tenant |
| **G12** | MB-12 mesa ayuda, contrato CC/Mi Trabajo, cross-tenant |
| **G13** | DATABASE_URL/Docker, Alembic single head, db startup, admin config (infra) |
| **G14** | Regresión V1: multitenant, RBAC v1, LLM gateway, integration v1, p0 precert, prerelease, knowledge, automations 810C, notifications 820, agent factory baseline, integraciones 1330 (smoke), optimización 1290 (smoke), oportunidades 1100 (smoke), identidad/SCIM (spot P2) |

---

## 2. GRUPOS DE CERTIFICACIÓN (DETALLE)

### G01 — AUTENTICACIÓN + SEGURIDAD BASE V1

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Login bootstrap; org activa/inactiva bloquea login; token expirado → 401; usuario inactivo rechazado; guards prod (JWT≥32, bootstrap password, CORS no wildcard en prod) |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_shell_830.py`, `tests/test_security_rbac_v1.py` (inactive/expired/prod guards), `tests/test_multitenant_v1.py::test_inactive_company_blocks_login`, `tests/test_p0_precertificacion_v1.py`, `tests/test_prerelease_v1_corrections.py` |
| **PRUEBAS NUEVAS NECESARIAS** | Ninguna obligatoria (cubierto por suites V1). Smoke opcional: login → token en header → `GET /api/centro-control/resumen-ejecutivo` 200 (incluido en **NX01**) |
| **CONDICIÓN PASS** | 100% PASS suites listadas; login admin bootstrap OK; org inactiva no autentica; token expirado 401 en ruta V2 |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G02 — RBAC + MULTIEMPRESA

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Viewer/operator limitados 403; no asignar admin; no inyectar org_id en user create; cross-tenant deny (empleados, knowledge, automation, operations, finops, opportunities, audit); aislamiento V2 (CC, auditor, MB-11, MB-12) |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_multitenant_v1.py` (completo), `tests/test_security_rbac_v1.py`, `tests/test_centro_control_tramo6e.py::test_centro_control_tenant_isolation`, `tests/test_auditor_integracion_mi_trabajo.py`, `tests/test_mb11_comunicaciones.py`, `tests/test_mesa_ayuda_mb12.py`, `tests/test_finops_950_adversarial.py::test_drill_down_cross_tenant_work_plan_404` |
| **PRUEBAS NUEVAS NECESARIAS** | **NX02** — cross-tenant simultáneo org A/B: CC + Mi Trabajo + comunicaciones + soporte en un solo test parametrizado. **NX03** — matriz RBAC V2: `control_center.view`, `auditor_empleados.view`, `communications.view`, `support.view`, `finops.view`, `optimizacion.view` → 403 sin permiso, 200 con permiso |
| **CONDICIÓN PASS** | `multitenant_v1` 14/14 PASS; NX02 PASS (0 fuga A↔B); NX03 PASS (≥6 códigos V2 verificados backend); ningún 200 cross-tenant en recursos ajenos |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G03 — SUPERADMIN CROSS-ORG

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | List/create empresas platform; tenant admin 403; `?organization_id=` explícito en CC; contexto org correcto; KPI CC → `/administracion/empresas`; Mi Trabajo/finops planner con org context |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_multitenant_v1.py` (superadmin, tenant admin), `tests/test_bloque_1250c_centro_control_integrado.py::test_1250c_superadmin_org_context`, `tests/test_centro_control_porque_p1.py::test_cc_superadmin_org_context`, `tests/test_convergencia_final_fase2.py::test_convergencia_kpi_organizaciones_enlace`, `tests/test_convergencia_final_fase2.py::test_convergencia_mi_trabajo_adapter_usa_viewer` |
| **PRUEBAS NUEVAS NECESARIAS** | Extensión en **NX02**: superadmin `GET /api/trabajo/resumen?organization_id={orgB}` devuelve ctx B sin mezclar datos A |
| **CONDICIÓN PASS** | Superadmin crea/lista orgs; tenant admin 403; `?organization_id=orgB` en CC devuelve `organization_id==orgB`; sin `?organization_id` superadmin ve su org por defecto |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G04 — CENTRO DE CONTROL

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Resumen ejecutivo 6E (12 módulos, 6 secciones); alias `/` ≡ `/centro-control` ≡ redirect `/panel`; drill-down enlaces válidos; mi_trabajo resumen sin 2ª bandeja; estados vacíos legibles; salud canónica ES |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_centro_control_tramo6e.py`, `tests/test_centro_control_cableado_ejecutivo_fase2.py`, `tests/test_bloque_1250c_centro_control_integrado.py`, `tests/test_bloque_1230_centro_control.py`, `tests/test_centro_control_1240_gaps_ui.py`, `tests/test_correccion_focal_post6e_p1.py`, `tests/test_convergencia_final_fase2.py`, `tests/test_control_center_datetime_cc_dt.py` |
| **PRUEBAS NUEVAS NECESARIAS** | Ninguna obligatoria adicional (drill-down cubierto). Incluido en **NX01** (CC como paso intermedio) |
| **CONDICIÓN PASS** | Suites CC PASS; alias rutas verificadas; ≥20 enlaces CC con prefijo `/` y ruta frontend registrada; `mi_trabajo.nota` presente; sin traceback en org vacía |
| **SEVERIDAD SI FALLA** | **P1** (P0 si fuga cross-org — delegado a G02/G03) |

---

### G05 — MI TRABAJO + DEDUP G2/G3

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Bandeja única `/api/trabajo/items`; una ruta `/trabajo`; contexto usuario/org; G2 sin duplicar obligación auditor; G3 dedup 1290 vs oportunidad; fuentes auditor/mesa/comms coexisten |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_bandeja_trabajo_humano.py`, `tests/test_gate_post6d_correcciones.py::test_g2`, `test_g3`, `tests/test_auditor_integracion_mi_trabajo.py`, `tests/test_mb11_integracion_mi_trabajo.py`, `tests/test_mesa_ayuda_integracion_mi_trabajo.py`, `tests/test_convergencia_final_fase2.py::test_convergencia_mi_trabajo_adapter_usa_viewer` |
| **PRUEBAS NUEVAS NECESARIAS** | **NX01** — sesión única: login → CC (`mi_trabajo` presente) → `GET /api/trabajo/items` → disparar hallazgo auditor mínimo → verificar ítem en bandeja sin duplicado |
| **CONDICIÓN PASS** | G2/G3 PASS; bandeja ≤1 ítem por obligación causal; integraciones auditor/mb11/mesa PASS; NX01 PASS |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G06 — AUDITOR

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | MVP determinístico; ejecutar auditoría; hallazgos; resumen CC; integración Mi Trabajo; cross-tenant; trazabilidad mejora |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_employee_auditor_mvp.py`, `tests/test_auditor_integracion_mi_trabajo.py`, `tests/test_auditor_factory_cycle.py` (parcial — ciclo completo en G07) |
| **PRUEBAS NUEVAS NECESARIAS** | Cubierto por **NX01** (paso auditor en sesión E2E) |
| **CONDICIÓN PASS** | MVP PASS; hallazgo no visible cross-org; resumen-centro-control 200; ítem auditor en Mi Trabajo con `modulo==auditor_empleados` |
| **SEVERIDAD SI FALLA** | **P1** (P0 si cross-tenant — G02) |

---

### G07 — FÁBRICA / MB-06 + CAS / CONCURRENCIA

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Factory E2E baseline; MB-06 lifecycle publish/approve; ciclo Auditor→Mi Trabajo→Fábrica; CAS `_atomic_claim_trace_execution`; carrera adversarial; auto_execution_blocked; G1 desviación autorizada |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_agent_factory_e2e.py`, `tests/test_employee_lifecycle_factory_mb06.py`, `tests/test_auditor_factory_cycle.py`, `tests/test_gate_post6d_correcciones.py` (-k `concurrency` + `test_g1`), orden adversarial: `test_auditor_factory_cycle.py` → `test_concurrency_auditor_factory_no_double_execution` |
| **PRUEBAS NUEVAS NECESARIAS** | **NX04** — controles CAS explícitos en gate: (a) misma obligación claves distintas ≤1 no-idempotente; (b) carrera post-cycle 5× PASS; (c) estado BD ≤1 aprobación PENDING. Puede ser wrapper pytest que invoca tests existentes + assert BD (sin duplicar lógica producto) |
| **CONDICIÓN PASS** | Ciclo auditor/fábrica 9/9; concurrency suite 10/10; NX04 PASS; `auto_execution_blocked=true` en contrato fábrica; G1 PASS |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G08 — APROBACIONES

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Oportunidades 1030 proactive; 1290 ejecución humana; factory request-approval; G4 AUTOMÁTICA ≠ autoaprobación; operaciones hub approvals |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_oportunidades_proactivas_1030.py`, `tests/test_optimizacion_1290.py`, `tests/test_gate_post6d_correcciones.py::test_g4`, `tests/test_employee_lifecycle_factory_mb06.py`, `tests/test_operations_940.py`, `tests/test_e2e_integral_1020.py` |
| **PRUEBAS NUEVAS NECESARIAS** | Ninguna obligatoria (G4/G2/G3 cubren regresión crítica) |
| **CONDICIÓN PASS** | G4 PASS (400/422 en AUTOMÁTICA); factory publish requiere aprobación; 1290 humano en bandeja sin auto-ejecutar |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G09 — FINOPS / COSTOS

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | `/costos-valor` canónico; finops 1110; MB-07 planner; cross-tenant finops; drill-down; 1270 multiproveedor smoke; CC enlace costos |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_finops_1110.py`, `tests/test_finops_950.py`, `tests/test_finops_950_adversarial.py`, `tests/test_consumption_planner_mb07.py`, `tests/test_bloque_1270_multiproveedor.py` (smoke subset), `tests/test_multitenant_v1.py::test_cross_tenant_finops_denied` |
| **PRUEBAS NUEVAS NECESARIAS** | Ninguna obligatoria; verificar en NX02 que contrato finops/planner org B ≠ org A |
| **CONDICIÓN PASS** | Dashboard `/api/finops/dashboard` 200; cross-tenant finops denied; planner contract aislado; permiso `finops.view` requerido |
| **SEVERIDAD SI FALLA** | **P0** (aislamiento) / **P1** (KPI/enlace) |

---

### G10 — CONOCIMIENTO / AUTH

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Upload/search/grants; cross-tenant knowledge; **descarga autenticada V1** (no `window.open` sin token); salud↔conocimiento bridge |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_knowledge_930.py`, `tests/test_salud_conocimiento_971.py`, `tests/test_capabilities_850.py`, `tests/test_multitenant_v1.py::test_cross_tenant_knowledge_denied` |
| **PRUEBAS NUEVAS NECESARIAS** | **NX05** — protección knowledge auth V1: verificar endpoint descarga exige `Authorization` (401/403 sin token); reutilizar aserciones de `test_knowledge_930` + grep contrato API (sin cambiar producto) |
| **CONDICIÓN PASS** | `knowledge_930` PASS; NX05 PASS; cross-tenant denied; sin regresión descarga pública |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G11 — COMUNICACIONES / MB-11

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Canales/plantillas/envío; contrato centro-control; integración Mi Trabajo; cross-tenant; permiso `communications.view` |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_mb11_comunicaciones.py`, `tests/test_mb11_integracion_mi_trabajo.py` |
| **PRUEBAS NUEVAS NECESARIAS** | Incluido en **NX02** (comunicaciones org A vs B) |
| **CONDICIÓN PASS** | MB-11 suite PASS; contrato CC 200; NX02 sin fuga mensajes/canales |
| **SEVERIDAD SI FALLA** | **P1** (P0 si cross-tenant) |

---

### G12 — SOPORTE / MB-12

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Casos SLA; contrato centro-control; integración Mi Trabajo; cross-tenant; permisos support |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_mesa_ayuda_mb12.py`, `tests/test_mesa_ayuda_integracion_mi_trabajo.py` |
| **PRUEBAS NUEVAS NECESARIAS** | Incluido en **NX02** (soporte org A vs B) |
| **CONDICIÓN PASS** | MB-12 suite PASS; contrato CC 200; NX02 sin fuga casos |
| **SEVERIDAD SI FALLA** | **P1** (P0 si cross-tenant) |

---

### G13 — DATABASE_URL / DESPLIEGUE

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | DATABASE_URL precedencia V1; contraseñas especiales Docker; Alembic single head `1341a1b2c3d4e`; db startup; validate_migrations; admin config smoke |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_docker_database_url.py`, `tests/test_db_startup_805d.py`, `tests/test_db_startup_805e.py`, `tests/test_migration_control.py`, `backend/scripts/validate_migrations.py` (via gate test), `tests/test_admin_840.py` (config) |
| **PRUEBAS NUEVAS NECESARIAS** | **NX06** — smoke post-merge: `conftest.py` importa modelos 1100–1380 + MB (grep/assert en CI, no producto). **Protección DATABASE_URL V1** reutiliza `test_docker_database_url.py` íntegro |
| **CONDICIÓN PASS** | `docker_database_url` PASS; `migration_control` PASS; Alembic heads==1; validate_migrations exit 0; NX06 PASS |
| **SEVERIDAD SI FALLA** | **P0** |

---

### G14 — REGRESIÓN FUNCIONAL V1

| Campo | Contenido |
|---|---|
| **RECORRIDOS CUBIERTOS** | Suite V1 canonical; automations 810C; notifications 820; LLM gateway; integration v1; integraciones 1330 smoke; optimización 1290 smoke; oportunidades 1100 smoke; identidad/SCIM spot (P2) |
| **PRUEBAS EXISTENTES REUTILIZABLES** | `tests/test_multitenant_v1.py`, `tests/test_security_rbac_v1.py`, `tests/test_integration_v1_final.py`, `tests/test_llm_gateway_v1.py`, `tests/test_p0_precertificacion_v1.py`, `tests/test_prerelease_v1_corrections.py`, `tests/test_automations_810c.py`, `tests/test_automations_810c_adversarial.py`, `tests/test_notifications_820.py`, `tests/test_agent_factory_e2e.py`, `tests/test_integraciones_1330.py`, `tests/test_optimizacion_1290.py`, `tests/test_bloque_1100_oportunidades_operativo.py`, `tests/test_identidad_1370.py` (spot), `tests/test_scim_1380.py` (spot) |
| **PRUEBAS NUEVAS NECESARIAS** | Ninguna obligatoria — este grupo **consolida** regresión V1 sin re-ejecutar 214 tests duplicados si G01–G13 ya PASS |
| **CONDICIÓN PASS** | Tier V1 mínimo 0 FAIL: multitenant_v1 + security_rbac_v1 + llm_gateway_v1 + integration_v1_final + knowledge_930 + docker_database_url |
| **SEVERIDAD SI FALLA** | **P0** |

---

## 3. PRUEBAS NUEVAS OBLIGATORIAS (CONSOLIDADAS)

| ID | Descripción | Grupos | Severidad si falla | Estado |
|---|---|---|---|---|
| **NX01** | E2E sesión única: login → CC → Mi Trabajo → Auditor (mismo token, asserts encadenados) | G04, G05, G06 | P0 | **Por crear** (1 archivo pytest) |
| **NX02** | Cross-tenant simultáneo org A/B: CC + Mi Trabajo + comunicaciones + soporte (+ superadmin ctx) | G02, G03, G11, G12, G09 | P0 | **Por crear** (1 archivo pytest) |
| **NX03** | Matriz RBAC V2 ampliada (≥6 permisos nuevos, 403 backend sin permiso) | G02 | P0 | **Por crear** (1 archivo pytest) |
| **NX04** | Wrapper CAS/concurrencia gate (reusa tests existentes + assert BD ≤1 aprobación) | G07 | P0 | **Por crear** (1 archivo pytest delgado) |
| **NX05** | Protección knowledge auth V1 (descarga sin token denegada) | G10 | P0 | **Por crear** o extensión mínima `test_knowledge_930` |
| **NX06** | Smoke conftest/modelos post-merge (grep CI) | G13 | P0 | **Por crear** (script CI, no producto) |

**Nota:** NX01–NX06 se implementan **después** de SHA GENERAL, en rama de tests de gate, sin modificar central certificada.

---

## 4. COMANDO ÚNICO DE EJECUCIÓN (REFERENCIA FUTURA)

Cuando exista SHA integrado, ejecutar **una invocación** por tiers (evitar 45 comandos sueltos):

```bash
# Tier 0 — infra (G13)
pytest tests/test_docker_database_url.py tests/test_migration_control.py \
  tests/test_db_startup_805d.py tests/test_db_startup_805e.py -q

# Tier 1 — V1 base (G01, G14 subset)
pytest tests/test_security_rbac_v1.py tests/test_multitenant_v1.py \
  tests/test_integration_v1_final.py tests/test_llm_gateway_v1.py \
  tests/test_knowledge_930.py tests/test_p0_precertificacion_v1.py -q

# Tier 2 — V2 gate (G02–G12)
pytest tests/test_convergencia_final_fase2.py tests/test_gate_post6d_correcciones.py \
  tests/test_auditor_factory_cycle.py tests/test_bandeja_trabajo_humano.py \
  tests/test_centro_control_tramo6e.py tests/test_centro_control_cableado_ejecutivo_fase2.py \
  tests/test_bloque_1250c_centro_control_integrado.py \
  tests/test_mb11_comunicaciones.py tests/test_mb11_integracion_mi_trabajo.py \
  tests/test_mesa_ayuda_mb12.py tests/test_mesa_ayuda_integracion_mi_trabajo.py \
  tests/test_finops_1110.py tests/test_consumption_planner_mb07.py \
  tests/test_employee_lifecycle_factory_mb06.py tests/test_employee_auditor_mvp.py \
  tests/test_auditor_integracion_mi_trabajo.py -q

# Tier 3 — nuevas obligatorias (cuando existan)
pytest tests/test_convergencia_gate_nx01_e2e_session.py \
  tests/test_convergencia_gate_nx02_cross_tenant_simultaneous.py \
  tests/test_convergencia_gate_nx03_rbac_fase2_matrix.py \
  tests/test_convergencia_gate_nx04_cas_wrapper.py \
  tests/test_convergencia_gate_nx05_knowledge_auth.py -q

# Frontend
cd frontend && npm run build
```

**Estimación:** ~180–200 tests reutilizados + 6 nuevos ≈ **UNA** certificación (~190–210 ejecuciones), no 45 intervenciones.

---

## 5. VEREDICTO FORMAL (PLANTILLA — PENDIENTE SHA)

| Campo | Valor |
|---|---|
| SHA integrado GENERAL | _pendiente_ |
| Coincidencia gate 0 | _pendiente_ |
| Agente B PostgreSQL | _dependencia — no duplicar_ |
| Grupos G01–G14 | _pendiente ejecución_ |
| NX01–NX06 | _pendiente implementación tests gate_ |
| **VEREDICTO** | **EN RESERVA** |

**Cierre APTO** requiere: todos los grupos P0 PASS + B=APTO PG + 0 FAIL P0/P1 en tiers 1–3.

---

## 6. ESTADO AGENTE C

```
══════════════════════════════════════════════════════════════
 EIAAX — GATE FUNCIONAL DE CONVERGENCIA PREPARADO
 Agente C — EN RESERVA esperando SHA integrado de GENERAL
 14 grupos | 6 pruebas nuevas NX01–NX06 especificadas
 Referencia: AUDITORIA_C_FUNCIONAL_PREINTEGRACION.md
 PostgreSQL: dependencia Agente B (no duplicar)
══════════════════════════════════════════════════════════════
```

Voz: no disponible en entorno cloud. Ausencia no bloquea.

---

*Especificación de gate. No ejecutado contra SHA de convergencia (aún inexistente). Sin modificación de producto.*
