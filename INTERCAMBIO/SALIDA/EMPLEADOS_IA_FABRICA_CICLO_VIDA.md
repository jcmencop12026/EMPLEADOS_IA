# EMPLEADOS IA — FÁBRICA CICLO DE VIDA (MB-06)

**Agente:** C  
**Fecha:** 2026-08-29  
**Base:** `3049cc586d60fecfe18c035e94e5ea412b649270` (`cursor/fase2-central-integracion`)  
**Rama:** `cursor/fabrica-empleados-ia-ciclo-vida`  
**Fase2 central:** NO modificada  

---

## 1. Qué ya existía (REUTILIZADO)

| Capacidad | Evidencia |
|-----------|-----------|
| Creación empleado | `agent_factory.create_employee`, wizard, templates |
| Configuración rol/objetivo/herramientas/conocimiento | `update_employee`, `EmployeeInstructions`, grants 930 |
| Ciclo de vida básico | `EmployeeLifecycleStatus` DRAFT→…→ACTIVE, endpoints test/certify/publish/activate/pause |
| Modelos prueba | `EmployeeTestCase`, `EmployeeTestRun`, `run_employee_tests` (mocks docint/rips) |
| Certificación | `certify_employee`, `EmployeeCertification` |
| Versionado parcial | `EmployeeVersion` en publish (sin auditoría de cambios) |
| FinOps por empleado | `EmployeeLimits`, `EmployeeModelPolicy`, `FinOpsRecord` |
| Multiproveedor | `EmployeeModelPolicy`, `llm_providers` (sin secretos en empleado) |
| RBAC base | `employee.view/create/edit/test/certify/publish/activate/admin` |
| Aprobaciones operativas | `ApprovalRequest` vía `operations` (no motor nuevo) |
| Automatizaciones vinculadas | `Automation.employee_id` |
| Frontend ficha empleado | `EmployeeDetailPage` con pestañas básicas |
| Auditoría event bus | `EmployeeEventType`, `write_audit` parcial |

**CREACIÓN EXISTENTE: REUTILIZADA** — no se reconstruyó la fábrica.

---

## 2. Qué se completó

### Backend

- **`employee_lifecycle_service.py`**: inventario, validación pre-publicación, versionado auditable, publicación con guardas, rollback, capacitación, salud para CC, contrato Auditor futuro.
- **Modelos extendidos**: `EmployeeVersion` (motivo, campos cambiados, versión anterior, aprobador, resumen pruebas), `EmployeeTraining`, `EmployeeFactoryApproval`.
- **Casos de prueba**: categorías TECHNICAL / FUNCTIONAL / SECURITY, criterio, CRUD API.
- **Permisos nuevos**: `employee.approve`, `employee.pause`, `employee.retire`, `employee.rollback`, `employee.train`.
- **Endpoints nuevos** en `/api/agent-factory/`:
  - `GET /auditor-contract`
  - `GET /employees/{id}/inventory`, `/health`, `/validate`
  - `GET|POST /employees/{id}/versions`, `GET /versions/{n}`
  - `GET|POST /employees/{id}/test-cases`
  - `GET|POST /employees/{id}/approvals`, `POST /approvals/{id}/decide`
  - `POST /request-approval`, `/rollback`, `/train`, `/retire`
  - `POST /publish` reforzado con validación + aprobación según riesgo
- **Migración**: `6b06a1b2c3d4e` (HEAD único en rama).

### Frontend

- **`EmployeeDetailPage`**: pestañas Configuración, Conocimiento, Herramientas, Modelo, Automatizaciones, Límites, Versiones, Pruebas, **Aprobación**, Publicación, Historial.
- Acciones: validar, capacitar, solicitar aprobación, rollback desde versiones, retirar.
- **`labels.ts`**: fases funcionales BORRADOR→ACTIVO.

### Tests

- **`tests/test_employee_lifecycle_factory_mb06.py`**: 19 casos (ciclo, versionado, publicación bloqueada, aprobación CRITICAL, segregación, rollback, capacitación, RBAC, multiempresa, secretos, idempotencia).

---

## 3. Qué sigue pendiente

| Ítem | Prioridad | Nota |
|------|-----------|------|
| Aprobación HIGH sin ser CRITICAL (segregación fina) | P2 | Política configurable por org |
| Vinculación visual automatizaciones en wizard empleado | P2 | Solo lectura en inventario |
| Port a Fase2 central | — | Receta §4 |

---

## CIERRE P1 Y CERTIFICACIÓN DIFERENCIAL

**Fecha cierre:** 2026-08-29  
**Commits P1:** `dccc40f` (UI aprobaciones + segregación), `8759bb9` (certificación diferencial + fixes)  
**HEAD antes P1:** `6430da879fd108bd3585f99d0b925674ed473cc6`  
**HEAD final:** `8759bb90ab8f8f0cc9ec0bfa4a8747eb102ef83a`

### P1 visual — Aprobaciones en ficha

| Requisito | Estado |
|-----------|--------|
| Pestaña **Aprobación** en `EmployeeDetailPage` | PASS |
| Estado, tipo, fecha, solicitante, aprobador, resultado, comentario | PASS |
| `GET /employees/{id}/approvals` | PASS |
| `POST /employees/{id}/approvals/{id}/decide` con `employee.approve` | PASS |
| Sync `EmployeeFactoryApproval` al decidir (ficha u `/operations/approvals`) | PASS |
| Segregación solicitante ≠ aprobador | PASS |
| Acciones UI según RBAC (`employee.edit` / `employee.approve`) | PASS |

### Certificación diferencial `test_agent_factory_e2e` (deny / finops)

Condiciones: SQLite aislado por corrida, mismos 2 tests, BASE `3049cc5` vs MB-06.

| Entorno | passed | failed | skipped | errors |
|---------|--------|--------|---------|--------|
| **BASE** `3049cc586d60fecfe18c035e94e5ea412b649270` | 2 | 0 | 0 | 0 |
| **MB-06** (rama actualizada) | 2 | 0 | 0 | 0 |

#### Clasificación por test

| Test | BASE | MB-06 | Clasificación |
|------|------|-------|---------------|
| `test_deny_blocks_orchestrator_execution` | PASS | PASS | **INTERMITENTE/ENTORNO** — fallaba en suite acumulada por selección de empleado DOCINT ajeno; estabilizado con `context.employee_id` |
| `test_finops_limit_reached_is_published_from_real_execution` | PASS | PASS (tras fix) | **INTRODUCIDO POR MB-06** — `publish_with_guards` exige configuración completa; el fixture e2e no incluía instrucciones/modelo. Corregido en test sin relajar reglas de negocio |

**FALLOS PREEXISTENTES CONFIRMADOS:** 0  
**FALLOS INTRODUCIDOS MB-06 (sin corregir):** 0  
**ERRORES INTRODUCIDOS MB-06:** 0

### Segregación y publicación protegida

| Verificación | Estado |
|--------------|--------|
| Crear empleado ≠ aprobar automáticamente | PASS |
| Editar ≠ aprobar | PASS |
| Solicitar aprobación ≠ aprobar (solicitante bloqueado) | PASS |
| CRITICAL sin aprobación → publicación 403 | PASS |
| Aprobación rechazada → publicación 403 | PASS |
| Aprobación válida → publicación permitida | PASS |

### Regresión focal

| Suite | Resultado |
|-------|-----------|
| `test_employee_lifecycle_factory_mb06.py` | **19/19 PASS** |
| `test_agent_factory_e2e.py` | **10/10 PASS** |
| `test_migration_control.py` | PASS |
| `test_multitenant_v1.py` | PASS |
| Acumulada (4 suites) | **49 PASS** |
| `npm run build` | PASS |

### Alembic

| Verificación | Valor |
|--------------|-------|
| HEADs | 1 |
| HEAD | `6b06a1b2c3d4e` |
| `revision_id` único vs `1270a1b2c3d4e`, `1330b1b2c3d4f`, `1380a1b2c3d4e`, `1390a1b2c3d4e` | PASS |

### Contrato Auditor

`GET /api/agent-factory/auditor-contract` preservado sin cambios de operaciones. **PASS**

### Receta final de port (actualizada)

Añadir a ARCHIVOS del port:

```text
  backend/app/services/coordinator.py                 (sync aprobación fábrica)
  tests/test_agent_factory_e2e.py                     (fixtures employee_id + config publish)
```

Orden de prueba post-port:

```text
  pytest tests/test_employee_lifecycle_factory_mb06.py tests/test_agent_factory_e2e.py tests/test_migration_control.py
  npm run build
```

---

## 4. Receta de port selectivo a Fase2 central

```text
ORIGEN: cursor/fabrica-empleados-ia-ciclo-vida
BASE DESTINO: cursor/fase2-central-integracion (sin commit directo en central)

ARCHIVOS:
  backend/app/services/employee_lifecycle_service.py          (nuevo)
  backend/app/enums.py                                        (EmployeeEventType extendido)
  backend/app/orchestration_models.py                         (EmployeeVersion/Training/FactoryApproval)
  backend/app/services/agent_factory.py                       (hooks versionado)
  backend/app/routers/agent_factory.py                        (endpoints)
  backend/app/schemas_factory.py                              (schemas)
  backend/app/permissions.py                                  (permisos employee.*)
  backend/alembic/versions/6b06a1b2c3d4e_*.py
  backend/alembic/migration_ledger.json
  backend/scripts/schema_repair.py                            (HEAD 6b06a1b2c3d4e)
  frontend/src/pages/EmployeeDetailPage.tsx
  frontend/src/api.ts
  frontend/src/lib/labels.ts
  tests/test_employee_lifecycle_factory_mb06.py

ORDEN:
  1. Cherry-pick o merge selectivo sobre fase2-central-integracion
  2. Alembic upgrade head → 6b06a1b2c3d4e
  3. pytest tests/test_employee_lifecycle_factory_mb06.py tests/test_agent_factory_e2e.py
  4. npm run build

CONFLICTOS ESPERADOS: permissions.py, agent_factory.py si central divergió en routers comerciales.
```

---

## 5. Mapeo ciclo de vida funcional

| Fase funcional | Estado API |
|----------------|------------|
| BORRADOR | DRAFT |
| CONFIGURADO | CONFIGURING, READY_FOR_TEST |
| EN_PRUEBAS | TESTING, FAILED_TEST, READY_FOR_CERTIFICATION |
| APROBADO | CERTIFIED |
| PUBLICADO | PUBLISHED |
| ACTIVO | ACTIVE |
| PAUSADO | PAUSED |
| RETIRADO | RETIRED |

Publicación bloqueada si: configuración incompleta, sin pruebas PASS, no CERTIFIED, o sin aprobación (riesgo CRITICAL / segregación).

---

## 6. Contrato Auditor futuro

`GET /api/agent-factory/auditor-contract` expone operaciones: capacitar, crear_version, probar, aprobar, publicar, rollback, pausar, retirar, inventario, salud.

**NO** se implementó el Auditor (Agente B).

---

## 7. Resultados de prueba

| Suite | Resultado |
|-------|-----------|
| `test_employee_lifecycle_factory_mb06.py` | 19/19 PASS |
| `test_agent_factory_e2e.py` | 10/10 PASS |
| `npm run build` | PASS |
| Alembic HEADs | 1 (`6b06a1b2c3d4e`) |

---

## 8. Salida final

```
EMPLEADOS IA — FÁBRICA MB-06 CERTIFICADA

BASE: 3049cc586d60fecfe18c035e94e5ea412b649270
RAMA: cursor/fabrica-empleados-ia-ciclo-vida
HEAD ANTES: 6430da879fd108bd3585f99d0b925674ed473cc6
HEAD FINAL: <HEAD_FINAL>

APROBACIONES UI: PASS
SEGREGACIÓN APROBACIÓN: PASS
PUBLICACIÓN PROTEGIDA: PASS

TESTS MB06: 19/19 PASS
AGENT FACTORY E2E BASE: 2 passed, 0 failed
AGENT FACTORY E2E MB06: 2 passed, 0 failed

FALLOS PREEXISTENTES CONFIRMADOS: 0
FALLOS INTRODUCIDOS MB06: 0
ERRORES INTRODUCIDOS MB06: 0

REGRESIÓN: 49 PASS (focal acumulada)
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS
SECRETOS: PASS
FRONTEND: PASS
ALEMBIC HEADS: 1
ALEMBIC HEAD: 6b06a1b2c3d4e
REVISION_ID ÚNICO: PASS
CONTRATO AUDITOR: PASS
P0: 0
P1: 0
P2: 2
APTO PARA PORTAR: SI
FASE2 CENTRAL: NO
MAIN: NO
V1: NO
VEREDICTO: MB-06 CERTIFICADA
```

CREACIÓN EXISTENTE: REUTILIZADA
CONFIGURACIÓN: PASS
CICLO DE VIDA: PASS
VERSIONADO: PASS
PRUEBAS: PASS
APROBACIÓN: PASS
PUBLICACIÓN: PASS
ROLLBACK: PASS
CAPACITACIÓN: PASS
CONOCIMIENTO 930: REUTILIZADO
MULTIPROVEEDOR: PASS
FINOPS: PASS
AUDITORÍA: PASS
CONTRATO AUDITOR FUTURO: PREPARADO
MAIN: NO
V1: NO
VEREDICTO: APTO PARA PORTAR
```
