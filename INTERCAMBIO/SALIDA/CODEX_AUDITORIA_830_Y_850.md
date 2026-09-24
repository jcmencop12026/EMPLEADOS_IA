# CODEX — Doble auditoría independiente PR #8 y PR #10

Fecha: 2026-08-24

No se realizó merge, corrección, push, rebase ni cherry-pick. Cada PR fue evaluado en un checkout separado y detached.

## PR #8 — CURSOR-830 — Shell / Auth / Dashboard / Navegación

### Identidad y aislamiento

- HEAD MAIN: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- HEAD PR: `8498adf071f67d06b7a66ebe3b5e64172d5ee6be`
- Merge-base: coincide con HEAD MAIN.
- DIFF: 22 archivos, 1.381 inserciones, 280 eliminaciones.
- SCOPE: predominantemente shell/auth/dashboard/navegación, pero incluye cambios funcionales del wizard de empleados y una nueva superficie de decisiones de aprobación.
- No incorpora commits de 810, 820, 840, 850 ni cambios de infraestructura 805.
- `git diff --check`: PASS.

### Resultado por área

- AUTH: PASS parcial. Sin token, token inválido y expirado redirigen al login; `/api/auth/me` valida la sesión.
- SESSION: PASS por código y pruebas. Token válido persiste; 401 limpia token/cache y redirige.
- LOGOUT: PASS por código; elimina token y vuelve a login.
- ERROR HANDLING: PASS parcial. Cliente traduce network/401/403/404/409/422/5xx a mensajes comprensibles; no se reprodujo matriz visual autenticada completa.
- DASHBOARD: PASS estático/por pruebas. KPIs provienen de APIs reales y existen loading/data/empty/error/retry; actividad reciente no está completamente traducida.
- ORGANIZATION: PASS estático/por pruebas. Estados loading/error/empty terminales; no spinner infinito identificado.
- MENU: jerárquico y colapsable; rutas reales. `/aprobaciones` se muestra a todos los roles sin filtrar permisos.
- APPROVALS: reutiliza `ApprovalRequest`, pero FAIL de autorización: viewer puede decidir.
- SPANISH: FAIL parcial; acciones/eventos backend quedan crudos en dashboard, aprobaciones, auditoría y detalle de ejecución.
- DIRECTORY / EXECUTIONS / OPERATIONS: protegidos y conectados a datos reales; rutas y estados async existen.
- ASYNC STATE: no se encontró request nuevo con spinner inevitable; todas las cargas revisadas tienen salida terminal.
- VISUAL: login y redirecciones se probaron en navegador real. No se completó recorrido autenticado por conflicto de puerto explicado abajo.
- CONSOLE: sin error concluyente observado en la cobertura ejecutada.
- NETWORK: redirección sin token verificada; matriz autenticada incompleta.

### Tabla de rutas

| Ruta | Estado | Menú | Auth | Resultado |
|---|---|---|---|---|
| `/login` | Funcional | No | Pública | Formulario en español |
| `/` | Funcional | Inicio | Sí | Dashboard; sin token → login |
| `/operaciones` | Funcional | Operaciones | Sí | Sin token → login |
| `/ejecuciones` | Funcional | Ejecuciones | Sí | Sin token → login |
| `/ejecuciones/:planId` | Funcional | Contextual | Sí | Detalle protegido |
| `/aprobaciones` | Funcional con defecto RBAC | Aprobaciones | Sólo autenticación | Viewer puede aprobar/rechazar |
| `/directorio` | Funcional | Directorio | Sí | Sin token → login |
| `/empleados/nuevo` | Funcional con pérdida de datos | Contextual | Sí | Wizard protegido |
| `/empleados/:employeeId` | Funcional | Contextual | Sí | Detalle protegido |
| `/organizacion` | Funcional | Organización | Sí | Estados async presentes |
| `/auditoria` | Funcional | Auditoría | Sí | Acciones internas sin traducir |
| `*` | Redirección | No | N/A | Sin token → `/login`; con token → `/` |

### Defectos bloqueantes

1. **P1 — Viewer puede aprobar o rechazar solicitudes.** `frontend/src/pages/ApprovalsPage.tsx:73-77` ofrece ambas acciones a cualquier usuario autenticado y `frontend/src/AppShell.tsx:24-27` publica el menú para todos. La ruta backend `backend/app/routers/operations.py:94-108` exige autenticación, pero no un permiso de decisión. `viewer` está definido como sólo lectura en `backend/app/permissions.py:24`.
2. **P1 funcional — El wizard descarta capacidades, tools y modelo en el flujo normal.** `frontend/src/pages/EmployeeWizardPage.tsx:49-59` crea sólo identidad. La configuración vive en PATCH `:61-69`, pero `finish()` `:83-86` navega inmediatamente después del create y nunca ejecuta ese PATCH para un empleado nuevo.

### Otros defectos

- Dashboard `DashboardPage.tsx:71,103`, Aprobaciones `ApprovalsPage.tsx:65`, Auditoría `AuditPage.tsx:48` y detalle de ejecución muestran `event_type`/`action` técnicos sin traducción.
- La debilidad de autorización del endpoint de aprobación preexistía, pero 830 la convierte en una ruta visible y operable para todos los roles.

### Pruebas y build

- TESTS PASSED: 53
- TESTS FAILED: 0
- TESTS SKIPPED: 0
- Advertencias: 1 (deprecación Starlette/httpx)
- Duración: 74,22 s
- `npm ci`: PASS
- `npm audit`: 0 vulnerabilidades
- `npm run build`: PASS, 58 módulos; JS 271,26 kB / 83,85 kB gzip; CSS 7,39 kB / 2,05 kB gzip
- GIT: PASS

### Control visual y limitaciones

Navegador real contra el frontend exacto en `http://127.0.0.1:15180`: login correcto y todas las rutas protegidas auditadas redirigieron a `/login` sin token. El proxy Vite está fijado al backend `:8010`, ya ocupado por un proceso ajeno; el backend detached no pudo enlazarse sin desplazar ese proceso o modificar configuración. Por aislamiento y regla de no modificar, no se realizó el recorrido autenticado completo ni una certificación visual responsive exhaustiva.

### Pendientes

- A: autorización backend de decisiones de aprobación; persistencia completa del wizard.
- B: traducción de acciones/eventos y control de visibilidad del menú por permisos.
- C: recorrido autenticado visual desktop/ancho reducido y matriz visual de errores 401/403/404/422/500.

### Veredicto PR #8

**NO APTO PARA MERGE**

## PR #10 — CURSOR-850 — Capacidades / Tools / Knowledge / Test Lab

### Identidad y aislamiento

- HEAD MAIN: `b887a2e77c646a5b0c82d47837dfaaaed9c491ce`
- HEAD PR: `218ed08ad8c51498a6e2fc1e5c0a732ddfe3c0b0`
- Merge-base: coincide con HEAD MAIN.
- DIFF: 30 archivos, 3.734 inserciones, 54 eliminaciones.
- SCOPE: catálogos 850, autorización, coordinator, Test Lab, migración, frontend y tests. No incorpora commits 810/820/830/840/805.
- AppShell añade rutas 850 directamente sobre el shell anterior; el cambio es acotado pero genera conflicto conceptual y regresión respecto de 830 (errores/auth y navegación divergentes).
- GIT: FAIL por whitespace en el informe Cursor, líneas 3-5 y 141-142.

### Resultado por área

- DUPLICATION: PASS. Reutiliza Capability, Tool, Employee*, WorkPlan, EmployeeTask, ApprovalRequest, AuditLog y FinOpsRecord; no crea segundo motor.
- AUTHORIZATION: FAIL.
- CAPABILITIES: CRUD/asignación/tenant presentes; FAIL porque `requires_approval` no se aplica.
- TOOLS: CRUD/asignación presente; FAIL por permiso arbitrario tratado como allow.
- TOOL POLICY: FAIL; decisión no está cerrada al enum ALLOW/DENY/REQUIRES_APPROVAL.
- APPROVAL: FAIL crítico; la herramienta corre antes de crear ApprovalRequest.
- KNOWLEDGE: parcial. Catálogo/asignación/tenant existen; ingesta real es mínima o no implementada según tipo.
- INGESTION: TEXT parcial; FILE no implementa carga/parseo real desde UI; URL/DB/API pueden quedar COMPLETED con conector no implementado.
- TEST LAB E2E: reutiliza coordinator y IDs reales, pero FAIL en semántica de aprobación.
- CERTIFICATION: FAIL parcial; un Test Lab completado puede contar como evidencia PASSED genérica para certificación.
- TENANT: PASS para helpers y casos cubiertos; búsquedas filtran organización.
- PERMISSIONS: RBAC de endpoints presente, pero assignment de grant permite inyección de decisión.
- AUDIT: parcial; faltan `tool.denied` en tool inactiva y estados blocked/waiting se registran como `test_lab.failed`.
- FINOPS: PASS de reutilización; no crea contador paralelo y UI usa No disponible cuando corresponde.
- UI: FAIL parcial; CRUD incompleto, errores raw, estados técnicos y JSON visible.
- MIGRATION: PASS en SQLite temporal, upgrade → downgrade → upgrade.

### Defectos A bloqueantes

1. **P0 — La herramienta se ejecuta antes de la aprobación.** `backend/app/services/coordinator.py:434-447` llama `_run_tool` en `:436`; sólo después calcula `requires_approval` y crea `ApprovalRequest` en `:455-466`. Aprobar `:653-669` acepta el output ya producido; rechazar `:670-680` no puede revertir efectos externos.
2. **P1 — Permission injection produce ALLOW implícito.** `backend/app/schemas_850.py:48-51` define `permission` como string libre y `backend/app/services/tools_service.py:195-217` lo persiste. `backend/app/services/authorization.py:106-133` sólo bloquea el literal `DENY`; coordinator sólo trata exactamente `REQUIRES_APPROVAL`. Valores como `ADMIN` o un typo terminan permitidos.
3. **P1 — `Capability.requires_approval` se ignora.** El campo existe en `backend/app/orchestration_models.py:18-34`, pero la decisión en `backend/app/services/coordinator.py:441-445` sólo consulta tool/grant/confidence. Una capacidad marcada para aprobación puede ejecutar sin ella.

### Otros defectos

- `frontend/src/api.ts:28-41` expone `detail` crudo. Navegador real mostró `Token inválido` y `Not Found` en lugar de limpiar sesión/login o mostrar error amigable.
- Capabilities/Tools/Knowledge sólo permiten crear y activar/desactivar; no editar ni ver detalle.
- `KnowledgePage.tsx:113-115` habilita ingesta únicamente para TEXT. No hay upload real TXT/Markdown/PDF.
- `knowledge_service.py:317-335` marca URL/DB/API como COMPLETED aunque el conector no está implementado.
- Test Lab y detalle de empleado muestran enums crudos y JSON técnico.
- `test_lab_service.py:200-212` crea `EmployeeTestRun PASSED` para cualquier ejecución completada; certificación cuenta cualquier PASSED en `agent_factory.py:469-489`.
- Tool inactiva se rechaza antes de escribir el evento obligatorio `tool.denied`.

### Casos críticos

| Caso | Resultado |
|---|---|
| Capability/tool asignada y activa | PASS |
| Sin capability | DENY |
| Sin tool | DENY |
| Tool desactivada | DENY, auditoría incompleta |
| Tool requiere approval | FAIL: ejecuta antes de WAITING_APPROVAL |
| Knowledge asignado | Acceso/catálogo parcial |
| Knowledge no asignado | DENY |
| Cross-tenant | DENY en casos cubiertos |
| Permission arbitrario | FAIL: ALLOW implícito |
| Capability requiere approval | FAIL: ignorado |

### Pruebas, migración y build

- TESTS PASSED: 62
- TESTS FAILED: 0
- TESTS SKIPPED: 0
- Advertencias: 5
- Duración: 93,05 s
- Migración SQLite: upgrade/downgrade/upgrade PASS; `down_revision=5b2eb2437398`
- `npm ci`: PASS
- `npm audit`: 0 vulnerabilidades
- `npm run build`: PASS, 58 módulos; bundle 279,21 kB / 83,96 kB gzip
- Secretos: no se encontraron credenciales productivas nuevas
- `git diff --check`: FAIL por whitespace en informe Cursor

### Control visual y limitaciones

Se comprobó en navegador real a ancho desktop y 768 px. Las rutas nuevas renderizan, las cargas terminan y no hubo overflow horizontal (`scrollWidth=innerWidth=768`) ni errores de consola capturados. El puerto backend `8000` estaba ocupado por otro proceso y el proxy está fijado a él, por lo que no se certificaron acciones/datos contra el backend detached exacto. Sí se reprodujo la fuga de errores crudos.

### Pendientes

- A: approval pre-ejecución real; enum cerrado para permiso; enforcement de `Capability.requires_approval`.
- B: ingesta y CRUD UI incompletos; regresión auth/error; evidencia de certificación demasiado amplia.
- C: traducciones/JSON técnico, auditoría semántica y whitespace.

### Veredicto PR #10

**NO APTO PARA MERGE**

## Resumen consolidado

### PR #8 CURSOR-830: NO APTO

Bloqueantes: viewer puede decidir aprobaciones; wizard pierde capacidades/tools/modelo.

### PR #10 CURSOR-850: NO APTO

Bloqueantes: tool ejecuta antes de aprobación; permission arbitrario se interpreta como allow; capability approval se ignora.

**NO MERGE REALIZADO.**
