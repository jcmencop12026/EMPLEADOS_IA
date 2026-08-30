# EMPLEADOS_IA — Corrección de interfaz pre-release

**Agente:** C  
**Base:** `4c03cbe0ba0ff8537452ec58f7aaca7ce18bede4` (`4c03cbe`)  
**Rama:** `cursor/v1-fix-interfaz-prerelease`  
**NO merge** · **NO tocar** `cursor/v1-integracion-final` / PR #32

---

## Cambios realizados

### 1. Descarga autenticada de Conocimiento (P1)

- Nueva función `downloadKnowledgeDocument()` en `frontend/src/api.ts`
- Flujo: `fetch` con `Authorization: Bearer` → `blob` → `URL.createObjectURL` → anchor download → `revokeObjectURL`
- Sin token en query string
- `KnowledgePage.tsx`: reemplazado `window.open` por botón que invoca la API autenticada

### 2. Español visible (14 hallazgos auditoría)

| Hallazgo | Resolución |
|----------|------------|
| Enterprise AI OS | → Sistema empresarial de IA (login, sidebar) |
| Orquestador E2E · Workspace Salud | → Centro de operaciones · Módulo Salud |
| Capabilities (wizard) | → Capacidades |
| Test Lab | → Laboratorio de pruebas |
| Agent Factory | → Fábrica de Empleados IA |
| FinOps (pestaña oportunidades) | → Costos y consumo |
| WorkPlan | → Plan de trabajo |
| ROI | → Retorno de inversión |
| PR #6 / #7 (dashboard) | Eliminado bloque visible |
| Códigos auditoría inglés | `formatAuditAction()` en Audit, Dashboard, Seguridad |
| event_type inglés | Mapa `EVENT_TYPE` en Dashboard |
| OpenAI / Ollama | Sin cambio (nombres de producto) |
| RIPS / DOCINT | Sin cambio (acrónimos de dominio) |

### 3. Navegación operaciones

- Añadido ítem de menú **«Nueva solicitud»** → `/operaciones/solicitud`
- Permiso: `operations.execute` (ya definido en `ROUTE_PERMISSIONS`)
- Coherente con botón existente en Centro de operaciones

---

## Pruebas ejecutadas

```
tests/test_knowledge_930.py     20 passed (incl. 4 nuevas descarga)
tests/test_security_rbac_v1.py   9 passed
tests/test_multitenant_v1.py    14 passed
Total focal:                     45 passed, 0 failed
```

### Nuevos tests descarga

| Test | Resultado |
|------|-----------|
| `test_download_and_delete` | PASS — autorizado |
| `test_download_without_token_rejected` | PASS — 401 |
| `test_download_cross_tenant_denied` | PASS — 404 |
| `test_download_without_knowledge_view_permission_denied` | PASS — 403 |
| `test_download_with_invalid_token_rejected` | PASS — 401 |

### Frontend build

```
npm run build — PASS
```

---

## Verificación P1 descarga

| Criterio | Estado |
|----------|--------|
| Usuario autorizado descarga | PASS |
| Sin permiso knowledge.view | PASS (403) |
| Documento otra empresa | PASS (404) |
| Token inválido / sin token | PASS (401) |
| Sin token en URL | PASS |

---

## Archivos modificados

- `frontend/src/api.ts`
- `frontend/src/lib/labels.ts`
- `frontend/src/AppShell.tsx`
- `frontend/src/pages/KnowledgePage.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/EmployeeWizardPage.tsx`
- `frontend/src/pages/DirectoryPage.tsx`
- `frontend/src/pages/TestLabPage.tsx`
- `frontend/src/pages/EmployeeDetailPage.tsx`
- `frontend/src/pages/OportunidadDetailPage.tsx`
- `frontend/src/pages/OperationsCenterPage.tsx`
- `frontend/src/pages/CostosValorPage.tsx`
- `frontend/src/pages/AutomationRunsPage.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/AuditPage.tsx`
- `frontend/src/pages/admin/AdminSecurityPage.tsx`
- `frontend/src/pages/DiagnosticoIpsPage.tsx`
- `tests/test_knowledge_930.py`

**Backend:** 0 cambios · **Migraciones:** 0

---

## Veredicto

**APTO** para pre-release interfaz V1.

- P0: 0
- P1: 0 (descarga corregida)
- P2 residual: nombres producto/dominio (OpenAI, Ollama, RIPS, DOCINT) — aceptado

---

*Sin merge. Rama independiente lista para integración selectiva.*
