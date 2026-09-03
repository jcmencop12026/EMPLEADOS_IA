# Empleado IA 2.0 — Evolución aislada (Agente D)

**Rama:** `cursor/empleado-ia-2-evolucion-9a85`  
**Base:** `main` (sin modificar V1 estable ni scripts Windows)

## Inventario existente (auditoría)

| Área | Estado | Ubicación principal |
|------|--------|---------------------|
| Employee / fábrica | Existe | `agent_factory.py`, `AIEmployee`, wizard/detalle UI |
| Roles RBAC humanos | Existe | `permissions.py` — `employee.*` |
| Capabilities / tools / knowledge | Existe | routers 850, grants por empleado |
| Orchestrator / planning | Existe | `coordinator.py`, `WorkPlan`, `EmployeeTask` |
| Execution / approvals | Existe | `ApprovalRequest`, `evaluate_tool_execution` |
| Metrics / audit / costs | Existe | `FinOpsRecord`, `audit.py`, métricas fábrica |
| Versions / sandbox | Existe | `EmployeeVersion`, `TestLabRun` |
| Evaluaciones negocio | Existe (separado) | `evaluacion_models` — no mezclar con empleado |
| Ciclo vida API | Existe | `EmployeeLifecycleStatus` (11 estados) |
| Modo sombra | Parcial | `shadow_mode` en tests, no en coordinator prod |
| Aprendizaje empleado | Parcial | `EmployeeTraining` básico; 1260 es oportunidades |
| Ficha laboral completa | Gap | Campos dispersos en `AIEmployee` + instructions |
| Supervisión estructurada | Gap | Eventos work sin modelo dedicado |
| Autonomía explícita | Gap | Solo maturity/shadow implícitos |

## Qué reutilizó (no reconstruyó)

- `AIEmployee`, `agent_factory`, grants capabilities/tools/knowledge
- `coordinator` + `authorization` (precedencia DENY > APPROVAL > ALLOW)
- `ApprovalRequest`, `FinOpsRecord`, `EmployeeVersion`
- UI `EmployeeDetailPage` + tab nueva (extensión mínima)

## Qué construyó

- `employee_20_models.py` — ficha, supervisión, indicadores, aprendizaje, contrato resultados
- `employee_20_service.py` — ficha laboral, evaluación, aprendizaje controlado
- `employee_20_autonomy.py` — RECOMIENDA / PREPARA / EJECUTA_CON_APROBACION / EJECUTA_DENTRO_LIMITES
- Hook mínimo en `coordinator.py` (autonomía + shadow en producción)
- `employee_20_cc_adapter.py` — señales CC sin modificar CC estable
- API `/api/empleados-ia-20/*`
- Migración `1510a1b2c3d4e`
- UI tab **Ficha 2.0**
- Tests `test_employee_ia_20_evolution.py`

## Adapters / dependencias integración

| Componente | Contrato | Estado |
|------------|----------|--------|
| Centro Control | `employee_20_cc_signals_v1` | Señales listas, `integrado: false` |
| Motor economía B | `valor_economico_ref` en `employee_result_links` | Referencia, no duplicado |
| Gateway EIAAX/PIIAX | Conectores vía `authorization` existente | Sin llamadas arbitrarias |
| Aprendizaje 1260 | Oportunidades separadas | Bridge futuro vía `employee_id` |

## Ciclo de vida — mapeo misión

| Misión | Implementación |
|--------|----------------|
| BORRADOR | `DRAFT` |
| CONFIGURACION | `CONFIGURING` |
| PRUEBAS | `TESTING` / fase `SANDBOX` |
| SANDBOX | Concepto derivado (TestLab + TESTING) |
| MODO_SOMBRA | `shadow_mode` + fase derivada |
| APROBADO | `CERTIFIED` / `PUBLISHED` |
| ACTIVO | `ACTIVE` |
| SUSPENDIDO | `PAUSED` |
| RETIRADO | `RETIRED` |

## Pruebas

Ver `tests/test_employee_ia_20_evolution.py` + regresión `test_agent_factory_e2e.py`

## P0/P1

- **P0:** Ficha, autonomía en coordinator, aprendizaje sin autoedit, multitenant — cerrados
- **P1:** Cableado CC real, bridge aprendizaje 1260, promoción versión post-aprobación learning
