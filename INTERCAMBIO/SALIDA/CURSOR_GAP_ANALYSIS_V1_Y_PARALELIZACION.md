# CURSOR — GAP ANALYSIS V1 + MAPA DE PARALELIZACIÓN — EMPLEADOS_IA

**Fecha/hora UTC:** 2026-08-28 15:24:00 UTC  
**Proyecto:** EMPLEADOS_IA  
**Git root:** `/workspace` (equivalente `D:\EMPLEADOS_IA`)  
**Tipo:** auditoría rápida — **sin desarrollo, sin ramas, sin PR, sin modificación de código**

---

## 1. SHA AUDITADO

| Campo | Valor |
|-------|-------|
| **HEAD / origin/main** | `b2703e6696812055f953b12d9cfc2ffb4f17c2b3` |
| **Tag certificado ciclo cerrado** | `empleados-ia-cierre-ciclo-1030` → `421364e7ed34cfe0f704a706b11f4f1913447db3` |
| **Alembic head** | `1030a1b2c3d4e` (único) |
| **Ciclo 810C–1030** | CERRADO — no reabierto en este análisis |

---

## 2. RESUMEN EJECUTIVO

EMPLEADOS_IA es hoy una **plataforma de orquestación empresarial funcional y certificada** (810C–1030) que opera principalmente como motor **determinístico** (RULE/PYTHON/TOOL). La arquitectura **anticipa** proveedores LLM (campos `model_provider`, `EmployeeModelPolicy`, tarifas FinOps por proveedor) pero **no existe capa de inferencia real** conectada.

Para V1 instalable y entregable a un cliente real se identifican **6 bloqueantes reales** y **4 importantes no bloqueantes**. El ciclo cerrado aporta ~85% de la funcionalidad operativa; los gaps concentran en **provisión multi-empresa**, **IA real**, **producción/ops** y **hardening**.

**Estimación cualitativa global V1:** **GRANDE** (varios paquetes en paralelo, 1 bloqueante arquitectónico central: inferencia IA).

---

## 3. INVENTARIO DE CAPACIDADES

Leyenda: **COMPLETO** | **PARCIAL** | **AUSENTE** | **EXISTE NO INTEGRADO** | **NO REQUERIDO V1**

### A. EMPRESAS / TENANTS

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Alta empresa (multi-tenant) | **AUSENTE** | `bootstrap()` crea 1 org (`backend/app/seed.py`); sin `POST /organizations` |
| Configuración empresa | **COMPLETO** | `PUT /api/admin/organization`, `AdminOrganizationPage.tsx` |
| Activación/desactivación org | **PARCIAL** | Campo `status` en modelo; sin UI dedicada de ciclo de vida org |
| Usuarios | **COMPLETO** | `admin.py` CRUD + `AdminUsersPage.tsx` (sin formulario edición UI) |
| Roles | **COMPLETO** | `admin.py` + `AdminRolesPage.tsx` + matriz permisos |
| Permisos | **COMPLETO** | `permissions.py` (~60 códigos), deny-by-default |
| Límites por tenant | **PARCIAL** | `EmployeeLimits` por empleado; sin límites globales org |
| Aislamiento tenant | **COMPLETO** | Filtrado `organization_id` en servicios; tests cross-tenant PASS |

### B. EMPLEADOS IA

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Crear / editar | **COMPLETO** | `agent_factory.py` + `EmployeeWizardPage.tsx` |
| Configurar especialidad/capacidad | **COMPLETO** | Asignaciones capabilities/tools/knowledge |
| Asignar herramientas/conocimiento | **COMPLETO** | Wizard + `EmployeeDetailPage.tsx` |
| Permisos empleado (tool grants) | **COMPLETO** | `authorization.py` ALLOW/DENY/APPROVAL |
| Modelo IA / instrucciones | **PARCIAL** | Campos texto en wizard; sin ejecución LLM real |
| Activar/desactivar/pausar | **PARCIAL** | API pause existe; UI pause **ausente** |
| Probar | **COMPLETO** | Test cases + `TestLabPage.tsx` |
| Versionar | **COMPLETO** | `EmployeeVersion` + tab versiones (display) |
| Auditar / trazabilidad | **COMPLETO** | `audit.py` + `WorkEvent` + `AuditPage.tsx` |

### C. PROVEEDORES Y MODELOS IA

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Proveedor configurable | **PARCIAL** | String `model_provider` por empleado; sin tabla `AIProvider` |
| Modelo configurable | **PARCIAL** | `EmployeeModelPolicy.allowed_models_json` |
| Credenciales / secretos | **AUSENTE** | No en `config.py`; no vault; no UI |
| Múltiples proveedores | **AUSENTE** | Sin gateway ni registry |
| Cambio de proveedor / fallback | **AUSENTE** | — |
| Timeouts / límites llamada | **AUSENTE** | — |
| Tokens/consumo/costos LLM | **PARCIAL** | FinOps registra consumo; sin llamadas LLM reales |
| Auditoría de llamadas IA | **AUSENTE** | — |
| Errores proveedor | **AUSENTE** | — |

> Scripts Ollama en `scripts/ENCENDER_OLLAMA.bat` — **EXISTE NO INTEGRADO** (fuera del backend).

### D. HERRAMIENTAS / CAPACIDADES

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Catálogo | **COMPLETO** | `capabilities.py`, `tools.py` + UI |
| Asignación | **COMPLETO** | Grants por empleado |
| Permisos ejecución | **COMPLETO** | `authorization.py` |
| Ejecución | **COMPLETO** | `coordinator.py` + `docint.py`, `rips.py`, `salud_analytics.py` |
| Test / auditoría | **COMPLETO** | Test lab + audit trail |

### E. CONOCIMIENTO

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Fuentes / carga | **COMPLETO** | Upload archivo en `KnowledgePage.tsx` |
| Consulta / búsqueda | **PARCIAL** | API `/search`, `/retrieve`; **sin UI** |
| Aislamiento tenant | **COMPLETO** | Tests + grants |
| Actualización / eliminación | **COMPLETO** | Reprocess + delete en UI |
| Trazabilidad | **COMPLETO** | `KnowledgeActivity` |

### F. ORQUESTACIÓN

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Plan / empleados / herramientas | **COMPLETO** | `coordinator.py`, `operations.py` |
| Aprobación | **COMPLETO** | `ApprovalsPage.tsx` + `ApprovalRequest` |
| Ejecución / validación / resultado | **COMPLETO** | Operations hub + execution detail |
| Aprendizaje | **PARCIAL** | `experience.py` API; **sin UI** |

### G. AUTOMATIZACIONES (810C)

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Programación / ejecución / reintentos | **COMPLETO** | `automation_scheduler.py`, wizard 7 pasos |
| Estado / alertas / idempotencia | **COMPLETO** | Tests adversarial PASS |

### H. NOTIFICACIONES (820)

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Internas (in-app) | **COMPLETO** | `InAppChannel`, `NotificationsPage.tsx` |
| Email | **AUSENTE** | Solo protocolo `NotificationChannel`; sin SMTP |
| Configuración / plantillas | **PARCIAL** | Alert rules API; **sin UI** reglas |
| Eventos / trazabilidad | **COMPLETO** | 14+ tipos de evento |

### I. FINOPS (950)

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Consumo / costos | **COMPLETO** backend | `finops_service.py` |
| Por empresa/empleado/operación | **COMPLETO** backend | Drill-down API |
| Presupuesto / límites / alertas | **COMPLETO** backend | `FinOpsBudget` + evento `FINOPS_LIMIT_REACHED` |
| UI administración tarifas/presupuestos | **PARCIAL** | Solo dashboard en `CostosValorPage.tsx` |

### J. ADMINISTRACIÓN (840B)

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Panel empresa / usuarios / roles | **COMPLETO** | 5 páginas admin |
| Configuración / auditoría | **COMPLETO** | Config + security summary + audit |
| Logs operaciones | **PARCIAL** | Work events; sin agregador logs HTTP |

### K. PRODUCCIÓN

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| DEV/TEST/PROD config | **PARCIAL** | `.env.example` mínimo (2 vars); default SQLite |
| PostgreSQL | **PARCIAL** | Soportado vía `DATABASE_URL`; CI usa PG efímero |
| Secretos / env | **PARCIAL** | JWT + DB; default secret inseguro en dev |
| Migraciones | **COMPLETO** | 18 revisiones + ledger + preflight startup |
| Backup / restore operativo | **AUSENTE** | Solo interno en `schema_repair.py` |
| Logging estructurado | **PARCIAL** | Loggers por módulo; sin middleware access log |
| Health checks | **PARCIAL** | `GET /health` superficial; sin ping DB |
| Observabilidad | **AUSENTE** | Sin métricas/tracing |
| Docker / deploy | **AUSENTE** | Sin Dockerfile ni workflow deploy |

### L. SEGURIDAD

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Autenticación JWT | **COMPLETO** | `security.py`, `LoginPage.tsx` |
| Autorización RBAC | **PARCIAL** | Mayoría routers; gaps: `audit.py`, `assistant.py`, `coordinator/route` |
| Tenant isolation | **COMPLETO** | Servicios + tests |
| Secretos | **PARCIAL** | Sin gestión centralizada |
| Rate limiting | **AUSENTE** | — |
| Auditoría | **COMPLETO** | `write_audit()` transversal |
| Hardening prod | **PARCIAL** | CORS configurable; sin MFA/refresh tokens |

### M. INSTALACIÓN / RELEASE

| Capacidad | Estado | Evidencia |
|-----------|--------|-----------|
| Instalación limpia Windows | **COMPLETO** | `CREAR_ENTORNO.bat`, `INICIAR_EMPLEADOS_IA.bat` |
| Inicialización BD | **COMPLETO** | `db_startup.py` + Alembic + bootstrap |
| Superadmin bootstrap | **COMPLETO** | `seed.py` + env vars |
| Upgrade | **COMPLETO** | Alembic upgrade head |
| Rollback migraciones | **PARCIAL** | Alembic downgrade posible; sin guía ops |
| Backup/restore manual | **AUSENTE** | — |
| Manuales instalación cliente | **PARCIAL** | README mínimo; DOCS extensos pero no guía V1 |
| Versionado release | **PARCIAL** | Tag ciclo; sin semver release pipeline |

### N. VERTICALES FUTURAS (NO V1 por defecto)

| Capacidad | Estado | Nota |
|-----------|--------|------|
| CONNECTOR independiente | **NO REQUERIDO V1** | — |
| Citas/agendamiento | **NO REQUERIDO V1** | — |
| SALUD IPS completo | **COMPLETO** pero vertical | Entregable como demo; no bloquea V1 genérico |
| Marketplace / white-label | **NO REQUERIDO V1** | — |

---

## 4. FLUJO V1 E2E — PASO A PASO

Flujo solicitado evaluado contra código actual (`main` @ `b2703e6`):

| # | Paso | Estado | Detalle |
|---|------|--------|---------|
| 1 | CREAR EMPRESA | **NO EXISTE** | Solo bootstrap 1 org; sin API/UI alta tenant |
| 2 | CREAR ADMINISTRADOR | **FUNCIONA** | Bootstrap + `AdminUsersPage` |
| 3 | CONFIGURAR IA | **PARCIAL** | Campos texto empleado; sin gateway ni credenciales |
| 4 | CREAR EMPLEADO IA | **FUNCIONA** | Wizard 5 pasos completo |
| 5 | DARLE CONOCIMIENTO | **FUNCIONA** | Upload + grants |
| 6 | DARLE HERRAMIENTAS | **FUNCIONA** | Catálogo + asignación |
| 7 | ASIGNAR PERMISOS | **FUNCIONA** | Roles usuario + grants empleado |
| 8 | PROBAR | **FUNCIONA** | Test lab + casos empleado |
| 9 | ACTIVAR | **FUNCIONA** | Lifecycle certify/publish/activate |
| 10 | RECIBIR SOLICITUD/EVENTO | **FUNCIONA** | Operations, automations, oportunidades |
| 11 | ORQUESTAR | **FUNCIONA** | Coordinator + selección 1010 |
| 12 | APROBAR SI APLICA | **FUNCIONA** | Flujo aprobación completo |
| 13 | EJECUTAR | **FUNCIONA** | Tools RULE/PYTHON (no LLM) |
| 14 | OBTENER RESULTADO | **FUNCIONA** | Work plans + resultados en UI |
| 15 | MEDIR COSTO/VALOR | **PARCIAL** | FinOps backend OK; UI limitada; costos LLM N/A |
| 16 | AUDITAR | **FUNCIONA** | Audit log + trazas oportunidades |
| 17 | APRENDER | **PARCIAL** | API experiencia; sin UI aprendizaje |

**Conclusión flujo:** operable end-to-end para **un tenant demo con motor determinístico**. **No operable** como SaaS multi-empresa ni como plataforma IA con inferencia real sin gaps GAP-001/002/003.

---

## 5. GAP REALES (BLOQUEANTES E IMPORTANTES)

### Bloqueantes V1 (Prioridad 1–2)

| ID | GAP | Estado actual | Bloquea V1 |
|----|-----|---------------|------------|
| **GAP-001** | Capa inferencia LLM / ejecución real proveedores IA | AUSENTE | **SÍ** — cliente espera empleados IA que llamen modelos |
| **GAP-002** | Alta y provisión multi-empresa (tenant) | AUSENTE | **SÍ** — si V1 = SaaS multi-cliente |
| **GAP-003** | Administración proveedores IA (credenciales, secretos, registry) | AUSENTE | **SÍ** — depende de GAP-001 |
| **GAP-004** | Despliegue producción (Docker, env completo, guía install) | AUSENTE/PARCIAL | **SÍ** — entrega cliente real |
| **GAP-005** | Backup / restore operativo | AUSENTE | **SÍ** — operación producción |
| **GAP-006** | Health checks profundos (DB, schedulers, dependencias) | PARCIAL | **SÍ** — ops/monitoring cliente |

### Importantes no bloqueantes V1 (Prioridad 3)

| ID | GAP | Estado | Bloquea V1 |
|----|-----|--------|------------|
| **GAP-007** | RBAC UI (menú por permisos) + cerrar holes backend | PARCIAL | No (riesgo seguridad) |
| **GAP-008** | UI FinOps completa (tarifas, presupuestos, drill-down) | PARCIAL | No |
| **GAP-009** | UI reglas alertas + notificaciones email | PARCIAL/AUSENTE | No |
| **GAP-010** | Corrección proxy Vite (8000) vs backend (8010) | PARCIAL | No (dev UX) |

### V1.1 / V2 (Prioridad 4) — no inflar V1

| ID | GAP | Nota |
|----|-----|------|
| GAP-011 | Experience/aprendizaje UI | API existe |
| GAP-012 | Pipeline proactivo UI (señales/priorizar) | Backend 1030 completo |
| GAP-013 | Rate limiting / MFA / refresh tokens | Hardening avanzado |
| GAP-014 | Observabilidad (métricas, tracing) | Post-V1 ops |
| GAP-015 | Aislamiento tests PostgreSQL | Deuda técnica; no defecto producto |

---

## 6. GAP APARENTES DESCARTADOS (YA EXISTEN)

| Área aparentemente faltante | Realidad en código | Evidencia |
|----------------------------|-------------------|-----------|
| Automatizaciones | **COMPLETO** | PR #6, 36+ tests, scheduler + idempotencia |
| Notificaciones in-app | **COMPLETO** | PR #7, centro notificaciones UI |
| RBAC usuarios/roles | **COMPLETO** | PR #9, 50 tests admin |
| Conocimiento | **COMPLETO** | PR #11, upload/chunk/search API |
| Centro operaciones | **COMPLETO** | PR #13, hub + detalle operaciones |
| FinOps consumo | **COMPLETO** backend | PR #16, tarifas/budgets API |
| Motor analítico | **COMPLETO** | PR #21 |
| Orquestador experiencia | **COMPLETO** | PR #22 |
| E2E integral | **COMPLETO** | PR #23/#25 |
| Oportunidades proactivas | **COMPLETO** | PR #25, cert V2 R2 12/12 |
| Salud IPS | **COMPLETO** | Vertical demo; no requerido V1 genérico |
| Migraciones gobernadas | **COMPLETO** | PR #20, ledger + preflight |
| CI certificación | **COMPLETO** | `.github/workflows/qa.yml` 4/4 |

---

## 7. PR #17 — `integracion-salud-workplan-002`

| Campo | Valor |
|-------|-------|
| Estado PR | OPEN |
| Commits exclusivos vs main | **1** (`6728b11` — solo documentación) |
| Archivos diferentes | `INTERCAMBIO/SALIDA/CURSOR_INTEGRACION_SALUD_WORKPLAN_002.md` |
| Código funcional | **Ya en main** vía PR #19 (`salud_workplan_bridge.py`, tests, migración `970a1`) |
| Necesario para V1 | **NO** |
| Obsoleto como merge | **SÍ** — puntero histórico; cero delta funcional |
| **Recomendación** | Cerrar sin merge (o merge doc-only opcional). **No integrar código.** |

---

## 8. PR #1 — `setup-dev-environment-808c`

| Campo | Valor |
|-------|-------|
| Estado PR | OPEN |
| Commits exclusivos | **2** |
| Archivos | `.cursor/environment.json`, `.cursor/install.sh`, `.gitignore` |
| Contenido | Bootstrap Cloud Agent (venv, npm, puertos 8010/5180) |
| Necesario para V1 producto | **NO** — solo DX desarrolladores |
| Obsoleto | **NO** — sigue siendo útil |
| **Recomendación** | Merge independiente opcional cuando convenga DX. **No bloquea V1.** |

---

## 9. DEUDA POSTGRESQL — 7 FALLOS

### Clasificación

| Causa | Tests afectados | Tipo |
|-------|-----------------|------|
| Username global hardcoded (`viewer830`) | `test_shell_830` | **Aislamiento tests** |
| Tarifas FinOps residuales en tabla compartida | `test_finops_950::test_registrar_consumo_con_tarifa` | **Contaminación datos** |
| Employee lookup sin filtro tenant | `test_salud_conocimiento_971` (3) | **Fixtures/contaminación** |
| Nombres empleado duplicados en org | `test_salud_workplan_bridge` | **Contaminación datos** |
| Pool DOCINT no controlado en test | `test_agent_factory_e2e` | **Contaminación datos** |

**Veredicto:** **7/7 = problema exclusivamente de aislamiento de tests** en PostgreSQL compartido persistente. **0/7 = defecto funcional.** En BD limpia: **7/7 PASS** reproducido.

### Corrección mínima propuesta (no implementada)

1. **Test-only (~20 LOC):** usernames únicos con UUID (patrón ya en `test_shell_830b.py`); scope tenant en `_radicacion_employee_id()`; nombres responsable únicos en bridge tests.
2. **Harness sistémico (preferido):** fixture `autouse` en `conftest.py` para PostgreSQL — savepoint rollback por test o TRUNCATE + bootstrap (semántica CI).

**No tocar producto:** `resolve_unique_employee`, `find_active_rate`, unicidad `username` son correctos.

---

## 10. MAPA DE DEPENDENCIAS

| ID | CAPACIDAD | ESTADO | BACKEND | FRONTEND | BD/MIGR | TESTS | DEPENDENCIAS | RIESGO | ESFUERZO | BLOQUEA V1 |
|----|-----------|--------|---------|----------|---------|-------|--------------|--------|----------|------------|
| GAP-001 | Inferencia LLM | AUSENTE | Nuevo `llm_service` + integración coordinator | Config empleado ampliada | Posible tabla `ai_provider_configs` | Suite llamadas mock | GAP-003 | Alto | **GRANDE** | **SÍ** |
| GAP-002 | Multi-tenant provisioning | AUSENTE | `POST /admin/organizations` + seed multi | Wizard alta empresa | Sin cambio schema (org existe) | Tests tenant CRUD | — | Medio | **MEDIO** | **SÍ** (SaaS) |
| GAP-003 | Admin proveedores IA | AUSENTE | Router + vault env/DB | Página admin proveedores | Migración credenciales cifradas | Tests secretos | GAP-001 | Alto | **MEDIO** | **SÍ** |
| GAP-004 | Deploy producción | PARCIAL | Dockerfile, compose, env template | Build estático nginx | — | Smoke deploy | — | Medio | **MEDIO** | **SÍ** |
| GAP-005 | Backup/restore | AUSENTE | Scripts CLI pg_dump/restore | — | — | Test restore | GAP-004 | Medio | **PEQUEÑO** | **SÍ** |
| GAP-006 | Health profundo | PARCIAL | `/health/ready` con DB+schedulers | — | — | Test health | GAP-004 | Bajo | **PEQUEÑO** | **SÍ** |
| GAP-007 | RBAC UI + holes | PARCIAL | Permisos audit/assistant/route | Menu filtrado permisos | — | Tests RBAC | — | Bajo | **PEQUEÑO** | No |
| GAP-008 | UI FinOps admin | PARCIAL | Ya existe API | Páginas tarifas/budgets | — | Reusar tests | — | Bajo | **PEQUEÑO** | No |
| GAP-009 | Alert rules UI + email | PARCIAL | SMTP channel opcional | Página reglas | — | Tests canal | — | Bajo | **MEDIO** | No |
| GAP-010 | Proxy Vite puerto | PARCIAL | — | `vite.config.ts` → 8010 | — | — | — | Bajo | **PEQUEÑO** | No |
| GAP-015 | Tests PG isolation | Deuda | — | — | — | conftest fixture | — | Bajo | **PEQUEÑO** | No |

---

## 11. PAQUETES PARALELIZABLES

### PAQUETE A — Infraestructura / Producción / PostgreSQL

| Campo | Detalle |
|-------|---------|
| GAPs | GAP-004, GAP-005, GAP-006, GAP-010 |
| Módulos | `Dockerfile`, `docker-compose.yml`, `.env.example`, `backend/app/main.py` (health), `backend/scripts/`, `frontend/vite.config.ts` |
| Migraciones | Ninguna |
| Pruebas | Smoke deploy, health ready, backup restore dry-run |
| **Paralelo** | **SÍ** — independiente de B y C |
| **No paralelo con** | — |
| Esfuerzo | **MEDIO** |

### PAQUETE B — Proveedores IA / Modelos / Consumo

| Campo | Detalle |
|-------|---------|
| GAPs | GAP-001, GAP-003 |
| Módulos | Nuevo `backend/app/services/llm_service.py`, `backend/app/routers/ai_providers.py`, `coordinator.py` (executor LLM), `finops_service.py` (costos reales), `frontend` admin proveedores |
| Migraciones | `ai_provider_configs`, posible `llm_call_log` |
| Pruebas | Mock OpenAI/Ollama, tests costo FinOps, tests timeout/fallback |
| **Paralelo** | **SÍ** con A y D; **parcial** con C (admin UI) |
| **No paralelo con** | Integración final en coordinator hasta B estable |
| Esfuerzo | **GRANDE** |

### PAQUETE C — Multi-empresa / Administración / Experiencia

| Campo | Detalle |
|-------|---------|
| GAPs | GAP-002, GAP-007, GAP-008 (UI) |
| Módulos | `admin.py`, `admin_service.py`, `seed.py`, páginas admin, `AppShell.tsx` (RBAC menu), `CostosValorPage.tsx` ampliada |
| Migraciones | Mínimas (posible `organization` campos extra) |
| Pruebas | Tenant CRUD, RBAC menu, FinOps UI |
| **Paralelo** | **SÍ** con A y D; **cuidado** con B en admin UI |
| **No paralelo con** | B si ambos tocan misma página configuración IA |
| Esfuerzo | **MEDIO** |

### PAQUETE D — Seguridad / Hardening

| Campo | Detalle |
|-------|---------|
| GAPs | GAP-007 (backend holes), GAP-013 (rate limit opcional V1.1) |
| Módulos | `audit.py`, `assistant.py`, `agent_factory.py`, middleware rate limit |
| Migraciones | Ninguna |
| Pruebas | Tests 403 en endpoints antes abiertos |
| **Paralelo** | **SÍ** con A, B, C |
| Esfuerzo | **PEQUEÑO** |

### PAQUETE E — Release / Instalación / Documentación

| Campo | Detalle |
|-------|---------|
| GAPs | Manuales V1, guía upgrade, checklist entrega |
| Módulos | `README.md`, `DOCS/GUIA_INSTALACION_V1.md`, `INTERCAMBIO/SALIDA/` |
| **Paralelo** | **SÍ** — puede avanzar desde día 1 con A |
| Depende de | A (para documentar deploy real) |
| Esfuerzo | **PEQUEÑO** |

### PAQUETE F — Calidad PostgreSQL (deuda)

| Campo | Detalle |
|-------|---------|
| GAPs | GAP-015 |
| Módulos | `tests/conftest.py`, tests afectados |
| **Paralelo** | **SÍ** — totalmente independiente |
| Bloquea V1 producto | **NO** |
| Esfuerzo | **PEQUEÑO** |

---

## 12. ORDEN DE INTEGRACIÓN RECOMENDADO

```
Fase 0 (paralelo inmediato):
  ├── PAQUETE A (infra/deploy)
  ├── PAQUETE D (seguridad holes)
  ├── PAQUETE E (docs — borrador)
  └── PAQUETE F (tests PG — deuda)

Fase 1 (paralelo):
  ├── PAQUETE B (LLM) ← camino crítico
  └── PAQUETE C (multi-tenant) ← si V1 = SaaS

Fase 2 (integración):
  B → coordinator + FinOps costos reales
  C → admin UI (si no chocó con B)
  A → validar deploy con B+C integrados

Fase 3 (cierre V1):
  D → hardening final
  E → manuales definitivos
  Smoke E2E flujo §4 completo en entorno PROD-like
```

**Restricción crítica:** PAQUETE B (inferencia IA) es el **camino largo** y no puede omitirse si V1 implica empleados que usan modelos reales. PAQUETE A puede avanzar en paralelo desde el día 1.

---

## 13. ESTIMACIÓN CUALITATIVA POR PAQUETE

| Paquete | Esfuerzo | Prioridad |
|---------|----------|-----------|
| A — Infra/Prod | **MEDIO** | P1 |
| B — Proveedores IA | **GRANDE** | P1 |
| C — Multi-empresa/Admin | **MEDIO** | P1 (SaaS) / P2 (single-tenant) |
| D — Seguridad | **PEQUEÑO** | P2 |
| E — Release/Docs | **PEQUEÑO** | P2 |
| F — Tests PG | **PEQUEÑO** | P3 |

**Total V1 mínimo viable (single-tenant on-prem + IA real):** A + B + D + E = **GRANDE**  
**Total V1 SaaS multi-cliente:** A + B + C + D + E = **GRANDE+**

---

## 14. RECOMENDACIÓN EXACTA PARA LLEGAR A V1

### Escenario recomendado: V1 single-tenant on-prem con IA real

1. **No reabrir ciclo 810C–1030** — base sólida certificada.
2. **Ejecutar en paralelo:**
   - **Paquete A:** Docker + PostgreSQL prod + backup/restore + health ready + alinear proxy Vite.
   - **Paquete B:** Capa LLM (OpenAI + Ollama mínimo) + admin credenciales + integración coordinator + costos FinOps reales.
   - **Paquete D:** Cerrar holes RBAC backend.
   - **Paquete F:** Aislamiento tests PG (calidad, no bloqueante).
3. **Post B:** Validar flujo E2E §4 pasos 3, 13, 15 con inferencia real.
4. **Paquete E:** Entregar guía instalación V1 + checklist operación.
5. **Diferir a V1.1:** multi-tenant (GAP-002) si primer cliente es single-tenant; email notifications; UI FinOps completa; experience UI.
6. **PR #17:** cerrar sin merge (obsoleto).
7. **PR #1:** merge opcional independiente (DX).

### Criterio de aceptación V1

- Instalación limpia en servidor cliente (Docker o Windows) con PostgreSQL.
- Superadmin bootstrap + 1 empresa operativa.
- Empleado IA con proveedor configurado ejecuta solicitud real vía LLM o tool.
- Orquestación + aprobación + resultado + auditoría + costo registrado.
- Backup/restore documentado y probado.
- Health check operativo para monitoring.

---

## 15. VEREDICTO FINAL

### **EMPLEADOS_IA — GAP ANALYSIS V1 TERMINADO**

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existen desarrollos pendientes del ciclo 810C–1030? | **NO** |
| ¿Existen gaps para V1 cliente real? | **SÍ** — principalmente inferencia IA + producción |
| ¿El producto actual es demostrable? | **SÍ** — flujo E2E determinístico completo |
| ¿Es entregable V1 sin trabajo adicional? | **NO** |

### Desarrollo funcional pendiente identificado (fuera ciclo cerrado)

| Gap | Bloquea V1 |
|-----|------------|
| GAP-001 Inferencia LLM | **SÍ** |
| GAP-003 Admin proveedores | **SÍ** |
| GAP-004 Deploy producción | **SÍ** |
| GAP-005 Backup/restore | **SÍ** |
| GAP-006 Health profundo | **SÍ** |
| GAP-002 Multi-tenant | **SÍ** solo si SaaS |

---

*Auditoría completada sin modificación de código, ramas ni PRs.*
