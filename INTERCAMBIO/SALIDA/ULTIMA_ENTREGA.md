# CURSOR-802 — Agent Factory Real + Publicación Empleados IA

**Fecha:** 2026-08-22  
**Repositorio:** jcmencop12026/EMPLEADOS_IA  
**Rama:** cursor/agent-factory-802-12b6  
**HEAD base:** 3b2913c (post CURSOR-801)

## Objetivo

Evolucionar CURSOR-801 con Agent Factory real:

`CREAR → CONFIGURAR → PROBAR → CERTIFICAR → PUBLICAR → ACTIVAR → ORQUESTADOR SELECCIONA → EJECUTAR`

## Implementado

### Backend (reutiliza AIEmployee, Capability, Tool — sin duplicar)
- Ciclo de vida: DRAFT → CONFIGURING → TESTING → CERTIFIED → PUBLISHED → ACTIVE
- Modelos: EmployeeVersion, EmployeeToolGrant, EmployeeKnowledgeSource, EmployeeModelPolicy, EmployeeLimits, EmployeeInstructions, EmployeeTestCase, EmployeeTestRun, EmployeeCertification, EmployeeTemplate
- API `/api/agent-factory/employees/*` — list, detail, create, update, test, certify, publish, activate, pause, metrics
- Permisos: employee.view/create/edit/test/certify/publish/activate/admin
- Eventos: employee.created/updated/tested/certified/published/activated/paused/version_changed
- Coordinator filtra empleados ACTIVE/PUBLISHED para route_task
- Empleados Salud existentes (DOCINT/RIPS) migrados a ACTIVE sin duplicar
- Plantillas: analista-documental, auditor-rips, analista-datos, asistente-investigacion
- Migración Alembic: `5b2eb2437398_agent_factory_802`

### Frontend
- Wizard `/empleados/nuevo` (identidad → capabilities → tools → modelo → revisión)
- Detalle `/empleados/:id` con tabs (Resumen, Pruebas, Certificación, Versiones, Actividad)
- Directorio evolucionado con filtros y columnas extendidas
- Centro Operaciones: botón «Crear empleado» operativo

## Pruebas

```
17 passed — test_orchestrator_e2e.py (10) + test_agent_factory_e2e.py (7)
```

Incluye E2E completo: crear → configurar → test → certificar → publicar → activar → orquestador.

## Build

`npm run build` — OK

## CURSOR-802

**PASS**
