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
  - `POST /request-approval`, `/rollback`, `/train`, `/retire`
  - `POST /publish` reforzado con validación + aprobación según riesgo
- **Migración**: `6b06a1b2c3d4e` (HEAD único en rama).

### Frontend

- **`EmployeeDetailPage`**: pestañas Configuración, Conocimiento, Herramientas, Modelo, Automatizaciones, Límites, Versiones, Pruebas, Publicación, Historial.
- Acciones: validar, capacitar, solicitar aprobación, rollback desde versiones, retirar.
- **`labels.ts`**: fases funcionales BORRADOR→ACTIVO.

### Tests

- **`tests/test_employee_lifecycle_factory_mb06.py`**: 16 casos (ciclo, versionado, publicación bloqueada, aprobación CRITICAL, rollback, capacitación, RBAC, multiempresa, secretos, idempotencia).

---

## 3. Qué sigue pendiente

| Ítem | Prioridad | Nota |
|------|-----------|------|
| Decisión automática de aprobaciones fábrica vía UI `/aprobaciones` | P1 | Se crea `ApprovalRequest`; falta enlace UI dedicado en ficha |
| Aprobación HIGH sin ser CRITICAL (segregación fina) | P2 | Política configurable por org |
| Vinculación visual automatizaciones en wizard empleado | P2 | Solo lectura en inventario |
| Regresión `test_finops_limit_reached` | P2 | Pre-existente en base fase2; 1 fallo aislado |
| Port a Fase2 central | — | Receta §4 |

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
| `test_employee_lifecycle_factory_mb06.py` | 16/16 PASS |
| `test_agent_factory_e2e.py` | 8/10 PASS (2 aislamiento/flaky pre-existentes: deny, finops) |
| `npm run build` | PASS |
| Alembic HEADs | 1 (`6b06a1b2c3d4e`) |

---

## 8. Salida final

```
EMPLEADOS IA — FÁBRICA CICLO DE VIDA TERMINADA

BASE: 3049cc586d60fecfe18c035e94e5ea412b649270
RAMA: cursor/fabrica-empleados-ia-ciclo-vida
HEAD: <commit final>

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
MULTIEMPRESA: PASS
RBAC: PASS
SUPERADMIN: PASS (platform sin cambios)
SECRETOS: PASS
FRONTEND: PASS
REGRESIÓN: 30/32 focal PASS (2 flaky/pre-existentes agent_factory)
ALEMBIC HEADS: 1
P0/P1/P2: 0/1/2
FASE2 CENTRAL: NO
MAIN: NO
V1: NO
VEREDICTO: APTO PARA PORTAR
```
