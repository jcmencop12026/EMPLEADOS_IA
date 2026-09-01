# 01 — Inventario y reutilización

## Qué ya existía (reutilizado sin duplicar)

| Capacidad | Ubicación | Uso MB-06 |
|-----------|-----------|-----------|
| Modelo `AIEmployee` + versiones | `orchestration_models.py` | Base canónica evolucionada |
| Ciclo de vida | `employee_lifecycle_service.py` | DRAFT→CONFIGURING→TESTING→CERTIFIED→PUBLISHED→ACTIVE |
| Fábrica / wizard | `agent_factory.py`, `EmployeeWizardPage.tsx` | Creación guiada |
| Directorio empleados | `DirectoryPage.tsx` → Biblioteca | Catálogo interno |
| Detalle operacional | `EmployeeDetailPage.tsx` | Prueba, aprobación, publicación |
| Plantillas | `EmployeeTemplate`, `/templates` | analista, asistente-operativo, etc. |
| Coordinator | `coordinator/route` | Orquestación existente |
| Gateway LLM | `llm_models.LlmProviderConfig` | Validación proveedor |
| Capacidades técnicas | `Capability`, `EmployeeCapability` | Herramientas reales |
| Knowledge | `EmployeeKnowledgeSource`, `KnowledgeSource` | Asociación fuentes |
| RBAC | `check_permission`, roles | employee.create/view/test/publish |
| Organizaciones | `Organization` | Aislamiento tenant |
| Auditoría | `write_audit`, `AuditLog` | Publicación y cambios |
| Aprobaciones | `EmployeeFactoryApproval`, `ApprovalRequest` | Sin motor paralelo |
| FinOps | `consumption_planner_service`, `FinOpsRecord` | Estimación costo |
| Arquitecto Transformación | `transformacion_models`, `transformacion_service` | Origen requerimientos |
| Centro de Control | Vistas existentes de métricas/health | Reutilizado vía `/health`, `/metrics` |

## Qué se construyó en MB-06

| Componente | Descripción |
|------------|-------------|
| `factory_bridge_service.py` | Puente Arquitecto→Fábrica, biblioteca, clon, FinOps wrap |
| Migración `1430a1b2c3d4e` | Trazabilidad origen, capacidades empresariales |
| `EmployeeBusinessCapability` | Contrato capacidades (CONSULTAR_DATOS, etc.) |
| Endpoints `/biblioteca`, `/from-requerimiento`, `/clone`, `/estimate-capacity`, `/validate-provider`, `/gobierno-operacional/boundary` |
| UI puente en `ArquitectoTransformacionPage` | Crear borrador desde requerimiento |
| Tests `test_fabrica_mb06_bridge.py` | 4 casos runtime + gobierno |

## Qué NO se construyó (por diseño)

- PIIAX, marketplace, FinOps nuevo, Knowledge nuevo, gateway nuevo
- Gobierno Operacional paralelo (solo adaptador frontera)
- Centro de Control duplicado
- Inteligencia de Resultados completa (frontera documentada)

## Corrección reutilizada

- `employee_lifecycle_service.validate_configuration`: alineación `LlmProviderConfig.provider_type` / `is_enabled` (antes referenciaba campos inexistentes).
