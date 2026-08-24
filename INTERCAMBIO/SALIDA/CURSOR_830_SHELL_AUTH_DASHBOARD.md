# CURSOR-830 — Shell / Auth / Dashboard / Navegación / Idioma

## Identificación

| Campo | Valor |
|-------|-------|
| **HEAD INICIAL** | `b887a2e` (Merge PR #5 sqlite-alembic-repair-805) |
| **HEAD FINAL** | `efa4803` |
| **RAMA** | `cursor/shell-auth-dashboard-830` |
| **PR** | _(draft, sin merge)_ |
| **BASE** | `main` |
| **RESULTADO** | **CURSOR-830 PASS** |

---

## Inventario de rutas frontend

| Ruta | Pantalla | Endpoint(s) | Permiso | Estado | Menú |
|------|----------|-------------|---------|--------|------|
| `/login` | LoginPage | `POST /api/auth/login`, `GET /api/auth/me` | Público | FUNCIONAL | — |
| `/` | DashboardPage | Agregación: employees, executions, approvals, events, audit | Autenticado | FUNCIONAL | Inicio → Panel de control |
| `/operaciones` | OperationsCenterPage | `POST /api/assistant/ask` | Autenticado | FUNCIONAL | Operaciones → Centro de operaciones |
| `/ejecuciones` | ExecutionsPage | `GET /api/operations/executions` | Autenticado | FUNCIONAL | Operaciones → Ejecuciones |
| `/ejecuciones/:planId` | ExecutionDetailPage | executions, events, approvals | Autenticado | FUNCIONAL | NO EXPUESTA (acceso desde listado) |
| `/aprobaciones` | ApprovalsPage | `GET/POST /api/operations/approvals/*` | Autenticado | FUNCIONAL | Operaciones → Aprobaciones |
| `/directorio` | DirectoryPage | `GET /api/operations/employees` | Autenticado | FUNCIONAL | Empleados IA → Directorio |
| `/empleados/nuevo` | EmployeeWizardPage | agent-factory templates/capabilities/tools/employees | Autenticado (rol) | FUNCIONAL | Empleados IA → Crear empleado |
| `/empleados/:employeeId` | EmployeeDetailPage | agent-factory employee CRUD lifecycle | Autenticado (rol) | PARCIAL | NO EXPUESTA (acceso desde directorio) |
| `/organizacion` | OrganizationPage | `GET /api/organization` | Autenticado | FUNCIONAL | Administración → Organización |
| `/auditoria` | AuditPage | `GET /api/audit/logs` | Autenticado | FUNCIONAL | Análisis y control → Auditoría |
| `*` | Redirect | — | — | FUNCIONAL | → `/login` |

### Resumen inventario

| Categoría | Cantidad |
|-----------|----------|
| **RUTAS INVENTARIADAS** | 12 (+ wildcard) |
| **RUTAS FUNCIONALES** | 10 |
| **RUTAS PARCIALES** | 1 (`/empleados/:employeeId` — JSON técnico en pestañas prueba/certificación) |
| **RUTAS ROTAS** | 0 (corregidas en 830) |
| **RUTAS SIN MENÚ** | 2 (`/ejecuciones/:planId`, `/empleados/:employeeId` — navegación contextual) |

### Backend sin UI (documentado, no improvisado)

| Endpoint | Notas |
|----------|-------|
| `GET /api/agent-factory/capabilities` | Usado en wizard; sin pantalla dedicada |
| `GET /api/agent-factory/tools` | Usado en wizard; sin pantalla dedicada |
| `GET /api/operations/finops/{plan_id}` | FinOps por plan; sin dashboard FinOps en main |
| Automatizaciones (PR #6) | No integrado en main — slot menú "Próximamente" |
| Notificaciones (PR #7) | No integrado en main — slot menú "Próximamente" |
| Usuarios / Roles / Config / Seguridad | Sin pantallas admin en main |
| Knowledge / Integraciones | Sin pantallas shell en main |
| Test Lab | Sin ruta dedicada (pruebas desde detalle empleado) |

---

## Correcciones implementadas

### AUTH / LOGIN / SESSION

- `RequireAuth` valida token contra `GET /api/auth/me` antes de renderizar shell.
- Sin token o sesión inválida → `/login`.
- Token inválido/expirado (401) → limpia token y sesión → `/login?expired=1` con mensaje en español.
- Logout limpia token + `sessionStorage` → `/login`.
- Refresh con sesión válida mantiene acceso (token en `localStorage`, revalidación en mount).
- Ruta protegida directa en URL sin sesión → login.

### API client central (`frontend/src/api.ts`)

- Clase `ApiError` con mensajes en español para 401/403/404/409/422/500 y errores de red.
- Prohibido mostrar JSON crudo (`{"detail":"Token inválido"}`) al usuario.
- Detalle técnico en `console.error`.

### DASHBOARD

- `DashboardPage` reemplaza `HomePage` con KPIs reales: empleados, activos, ejecuciones, en curso, fallidas, aprobaciones pendientes, actividad y auditoría reciente.
- Estados: loading / success / empty / error.
- Slots preparados para Automatizaciones y Notificaciones (PR #6/#7).

### ORGANIZATION

- Causa raíz: `catch` silencioso dejaba `org=null` sin `loading=false` ni error → spinner infinito.
- Corregido con `LoadingState` / `ErrorState` / `EmptyState`.

### MENÚ

- Jerárquico colapsable por sección y menú completo colapsable.
- Persistencia en `localStorage`.
- Solo rutas existentes; sección "Próximamente" sin links rotos.

### ESPAÑOL

- `frontend/src/lib/labels.ts`: DRAFT→Borrador, ACTIVE→Activo, CERTIFIED→Certificado, etc.
- Login, errores, estados async y columnas en español.

### COMPONENTES COMUNES

- `LoadingState`, `EmptyState`, `ErrorState` en `frontend/src/components/AsyncState.tsx`.

---

## Pruebas

| Área | Resultado |
|------|-----------|
| SIN TOKEN → 401 en endpoints protegidos | PASS |
| TOKEN INVÁLIDO → 401 | PASS |
| TOKEN EXPIRADO → 401 | PASS |
| LOGIN CORRECTO → token + /me | PASS |
| ORGANIZACIÓN con sesión | PASS |
| DIRECTORIO / EJECUCIONES con sesión | PASS |
| 403 viewer sin permiso crear empleado | PASS |
| Suite completa `pytest tests/` | **53 passed** |
| `npm run build` | **OK** |
| `git diff --check` | **OK** |

### Tests nuevos

- `tests/test_shell_830.py` (7 casos)

---

## Defectos corregidos (evidencia usuario)

1. Entró sin login → RequireAuth valida `/api/auth/me`.
2. Directorio/Ejecuciones `Token inválido` JSON → ApiError + redirect login.
3. Inicio "Cargando..." infinito → Dashboard con estados definidos.
4. Organización loading infinito → error/empty/data.
5. Menú plano → jerárquico colapsable.
6. Mezcla ES/EN → labels español.
7. Estados ACTIVE/DRAFT/etc. en inglés → traducidos en UI.
8. Errores backend crudos → mensajes controlados.

## Defectos fuera de alcance

- Integración Automatizaciones (PR #6) y Notificaciones (PR #7).
- Conflictos Alembic 810/820.
- Pantallas admin (usuarios, roles, config, seguridad).
- Dashboard FinOps (sin datos agregados en main).
- Test Lab como ruta independiente.
- JSON técnico en pestañas Pruebas/Certificación del detalle empleado (datos de API).

## Pendientes

| ID | Descripción |
|----|-------------|
| **A** | Integrar Automatizaciones y Notificaciones cuando PR #6/#7 estén en main |
| **B** | Pantallas Capacidades/Herramientas, FinOps dashboard, Test Lab dedicado |
| **C** | Admin usuarios/roles/config/seguridad |

---

**NO MERGE** — entrega en rama `cursor/shell-auth-dashboard-830` para revisión.
