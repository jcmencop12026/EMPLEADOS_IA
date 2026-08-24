# CURSOR-850 — Capacidades + Herramientas + Conocimiento + Test Lab V1

**Fecha:** 2026-08-24  
**Rama:** `cursor/capabilities-tools-knowledge-testlab-850`  
**Base:** `main` @ `b887a2e`  
**PR:** (draft, pendiente de creación)

---

## HEAD INICIAL / FINAL

| Campo | Valor |
|-------|-------|
| HEAD INICIAL | `b887a2e` |
| HEAD FINAL | `b1fc7a2` (post-fix rutas) |
| RAMA | `cursor/capabilities-tools-knowledge-testlab-850` |

---

## INVENTARIO PREVIO

| Componente | EXISTE | MODELO | API | UI | ESTADO | REUTILIZAR | FALTA |
|------------|--------|--------|-----|-----|--------|------------|-------|
| Capability | Parcial | `capabilities` | GET list | Wizard | Seed docint/rips | Sí | CRUD, categoría |
| EmployeeCapability | Sí | `employee_capabilities` | PATCH employee | Wizard | Junction | Sí | is_active, UI asignación |
| Tool | Parcial | `tools` | GET list | Wizard | Seed | Sí | CRUD, config, timeout |
| ToolPolicy | Equiv. | `employee_tool_grants` | PATCH | Wizard ALLOW | Coordinator DENY | Sí | Enforcement completo |
| KnowledgeSource | No (org) | — | — | — | — | EmployeeKnowledgeSource | Catálogo org + ingesta |
| Knowledge | Parcial | `employee_knowledge_sources` | PATCH | — | Por empleado | Sí | Catálogo + asignación |
| DataSource | No | — | — | — | — | KnowledgeSource V1 | Conectores futuros |
| Employee | Sí | `ai_employees` | Full CRUD | Directorio | Completo | Sí | Tab asignaciones |
| EmployeeTask / WorkPlan | Sí | orchestration | operations | Ejecuciones | Completo | Sí | Test Lab link |
| Approval | Sí | `approval_requests` | operations | Detalle | Completo | Sí | — |
| Audit | Sí | `audit_logs` | `/api/audit/logs` | Auditoría | Completo | Sí | Eventos 850 |
| FinOps | Sí | `finops_records` | operations | — | Básico | Sí | Mostrar en Test Lab |
| Agent Factory | Sí | — | `/api/agent-factory` | Wizard | Completo | Sí | — |
| Test/Cert | Sí | test_cases/runs | POST test/certify | Detalle | Smoke auto | Sí | Test Lab E2E |

---

## MODELS / MIGRATION

**Migración:** `a850c4d5e6f8` ← `5b2eb2437398`

- `capabilities`: +`category`, +`updated_at`
- `tools`: +`description`, +`config_json`, +`timeout_seconds`, +`updated_at`
- `employee_capabilities`: +`is_active`
- **Nuevo:** `knowledge_sources`, `knowledge_ingestions`, `test_lab_runs`
- `employee_knowledge_sources`: +`knowledge_source_id` FK

---

## CAPABILITIES

- CRUD `/api/capabilities` (listar, buscar, filtrar, crear, editar, activar/desactivar, detalle)
- UI `/capacidades`
- Permisos: `capability.view`, `capability.manage`
- Audit: `capability.created`, `capability.updated`, `capability.assigned`, `capability.removed`

## EMPLOYEE CAPABILITIES

- Asignación `/api/capabilities/employees/{id}/assign/{cap_id}`
- UI pestaña **Asignaciones** en detalle empleado
- Enforcement en coordinator + Test Lab

## TOOLS

- CRUD `/api/tools`
- UI `/herramientas`
- Permisos: `tool.view`, `tool.manage`

## TOOL POLICY / RISK / APPROVAL

- Reutiliza `employee_tool_grants` (ALLOW / DENY / REQUIRES_APPROVAL)
- Enforcement backend en `coordinator._execute_task` + `authorization.py`
- Riesgo LOW/MEDIUM/HIGH/CRITICAL en modelos existentes
- Approval vía `ApprovalRequest` existente → `WAITING_APPROVAL`

## KNOWLEDGE / INGESTION / EMPLOYEE KNOWLEDGE

- CRUD `/api/knowledge`
- Ingesta V1 texto/TXT/Markdown (FILE); URL/DB/API como definición
- UI `/conocimiento`
- Asignación empleado con tenant enforcement

## TEST LAB / ORCHESTRATOR E2E / CERTIFICATION

- UI `/test-lab`
- API `/api/test-lab/run` → `run_controlled_plan` → WorkPlan → EmployeeTask → coordinator real
- Registro `test_lab_runs` + evidencia en `employee_test_runs`
- Certificación existente sin auto-certificar por Test Lab

## TENANT / PERMISSIONS / AUDIT / FINOPS / SECURITY

- Cross-tenant bloqueado (ORG A/B tests)
- Permisos nuevos en `permissions.py`; admin/operator/viewer
- Audit eventos 850 registrados
- FinOps: coste real o "No disponible"
- Sin secretos en frontend/git/responses

## UI / VISUAL

- Rutas: `/capacidades`, `/herramientas`, `/conocimiento`, `/test-lab`
- Menú AppShell actualizado (sin PR #8 shell)
- Estados español, errores amigables (sin JSON crudo)
- Asignaciones en detalle empleado

## TESTS

| Métrica | Valor |
|---------|-------|
| TESTS PASSED | 62 |
| TESTS FAILED | 0 |
| TESTS SKIPPED | 0 |

Archivo: `tests/test_capabilities_850.py` (16 casos 850 + regresión suite completa)

## NPM AUDIT / BUILD

| Métrica | Valor |
|---------|-------|
| NPM AUDIT | 0 vulnerabilidades HIGH/CRITICAL |
| BUILD | OK (`vite build`) |

## GIT DIFF CHECK

- Sin código de PR #6/#7/#8/#9
- Sin modificación infraestructura 805
- Alembic head único desde `5b2eb2437398`

## DEFECTOS DETECTADOS/CORREGIDOS

- Coordinator no validaba capability asignada → enforcement añadido
- Sin catálogo org knowledge → `knowledge_sources` creado reutilizando patrón existente
- Errores cross-tenant 500 → `AuthorizationError` handler 400
- Rutas `/employees/...` capturadas por `/{id}` → reordenadas en routers
- UI mostraba JSON crudo en errores → parser en `api.ts`

## PENDIENTES

**A:** Auditoría externa PR draft  
**B:** Integración menú shell PR #8 cuando merge a main  
**C:** Conectores RAG/OCR/vector DB (fuera de alcance V1)

---

## RESULTADO

**CURSOR-850 PASS**
