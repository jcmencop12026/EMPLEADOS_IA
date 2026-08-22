# CURSOR-801 — Orquestador E2E Real

**Fecha:** 2026-08-22  
**Repositorio:** jcmencop12026/EMPLEADOS_IA  
**Rama:** cursor/orquestador-e2e-12b6  
**HEAD base:** bea0058

## Objetivo

Cerrar el primer circuito real:

`USUARIO → ORQUESTADOR → PLAN → EmployeeTask → EMPLEADO/CAPABILITY → TOOL → EJECUCIÓN → VALIDACIÓN → APROBACIÓN → RESULTADO → TRAZABILIDAD`

## Implementado

### Backend
- `coordinator.route_task` — enrutamiento por reglas a DOCINT/RIPS
- `POST /api/agent-factory/coordinator/route`
- `POST /api/assistant/ask` — entrada desde Centro de Operaciones
- Modelos: `WorkPlan`, `EmployeeTask`, `AIEmployee`, `Capability`, `Tool`, `ApprovalRequest`, `WorkEvent`, `FinOpsRecord`
- Event bus in-process con persistencia en `work_events` y auditoría
- Herramientas reales: `tools/docint.py`, `tools/rips.py` (RULE/PYTHON, sin mocks)
- Aprobación humana vía `POST /api/operations/approvals/{id}/decide`
- Migración Alembic: `4355c73adcb8_orchestration_work_plans_tasks`

### Frontend
- Centro de Operaciones (`/operaciones`) — campo «¿Qué necesita hacer hoy?»
- Ejecuciones (`/ejecuciones`) con drill-down (`/ejecuciones/:planId`)
- Directorio Operacional (`/directorio`)
- Sidebar colapsable, estilos compactos empresariales

### E2E Salud
- Caso: «Analiza estos documentos/RIPS y dime qué problemas existen»
- RIPS → validación estructural + hallazgos + aprobación cuando aplica
- DOCINT → validación documental + hallazgos

## Pruebas

```
10 passed — tests/test_orchestrator_e2e.py
```

Cubre: routing, plan, EmployeeTask, execute, tool, validation, approval (accept/reject), tenant isolation, permission denied, DOCINT/RIPS E2E, traceability.

## Build

```
npm run build — OK
```

## Verificación visual

Navegador: Inicio, Centro Operaciones, Ejecuciones, Directorio, sidebar colapsable — PASS.

## Cómo probar

```bash
# Backend
cd backend && pip install -r requirements.txt
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8010

# Frontend
cd frontend && npm ci && npm run dev

# Login: admin / Admin2026*
# Ir a Centro de Operaciones → Ejecutar análisis RIPS o DOCINT
```

## CURSOR-801

**PASS**
