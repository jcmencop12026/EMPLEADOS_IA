# EMPLEADOS IA — Control visual y navegación preconvergencia

**Alcance:** auditoría UX sobre ramas de vistas terminadas (sin merge entre ellas, sin tocar Centro de Control ni Fase2 central).

---

## A. Mapa de navegación esperado (post-convergencia)

Estructura única reutilizando `AppShell.tsx` actual:

| Sección | Ítems |
|---------|--------|
| **Inicio** | Centro de Control (`/`) |
| **Operaciones** | Centro de operaciones, Nueva solicitud, Ejecuciones, Aprobaciones, Automatizaciones |
| **Salud** | Diagnóstico IPS |
| **Empleados IA** | Directorio, Crear empleado, Capacidades, Herramientas, Conocimiento, Laboratorio |
| **Análisis y control** | Líneas base, Oportunidades, Señales, Diagnósticos, Inteligencia externa, Continuidad, Integraciones, Costos y valor, Gobierno de datos, Mi seguridad, Notificaciones, Auditoría |
| **Comercial** *(rama comercial)* | Comercial y valor, TCO y aliados, Implementación, Segmentación y planes |
| **Aprendizaje** *(rama aprendizaje)* | Aprendizaje, Optimización |
| **Administración** | Empresas, Usuarios, Roles y permisos, Organización, Configuración, Proveedores IA, Seguridad, Identidad empresarial |

**Principio:** un concepto → una ruta → un nombre en español. Subvistas por tabs (detalle usuario, integración, oportunidad) sin duplicar menú lateral.

---

## B. Matriz de rutas (rama identidad — referencia más completa)

| Menú | Submenú | Ruta | Vista | Permiso(s) | Estado |
|------|---------|------|-------|------------|--------|
| Inicio | Centro de Control | `/` | CentroControlPage | `control_center.view` | OK |
| Operaciones | Centro de operaciones | `/operaciones` | OperationsHubPage | `operations.view` | OK |
| Operaciones | Nueva solicitud | `/operaciones/solicitud` | OperationsCenterPage | `operations.execute` | OK |
| Operaciones | Ejecuciones | `/ejecuciones` | ExecutionsPage | `operations.view` | OK |
| Operaciones | Aprobaciones | `/aprobaciones` | ApprovalsPage | `operations.view` / `approve` | OK |
| Operaciones | Automatizaciones | `/automatizaciones` | AutomationsPage | `automation.view` | OK |
| Salud | Diagnóstico IPS | `/salud/diagnostico` | DiagnosticoIpsPage | `salud.consultar_diagnostico` | OK |
| Empleados IA | Directorio | `/directorio` | DirectoryPage | `employee.view` | OK |
| Empleados IA | Crear empleado | `/empleados/nuevo` | EmployeeWizardPage | `employee.create` | OK |
| Empleados IA | Capacidades | `/capacidades` | CapabilitiesPage | `capability.view` | OK |
| Empleados IA | Herramientas | `/herramientas` | ToolsPage | `tool.view` | OK |
| Empleados IA | Conocimiento | `/conocimiento` | KnowledgePage | `knowledge.view` | OK |
| Empleados IA | Laboratorio | `/test-lab` | TestLabPage | `test_lab.view` | OK |
| Análisis | Líneas base | `/lineas-base` | LineasBasePage | `linea_base.view` | OK |
| Análisis | Oportunidades | `/oportunidades` | OportunidadesPage | `oportunidades.view` | OK |
| Análisis | Señales | `/senales` | SenalesPage | `oportunidades.view` | OK |
| Análisis | Diagnósticos | `/diagnosticos` | DiagnosticosPage | `diagnosticos.view` | OK |
| Análisis | Inteligencia externa | `/inteligencia-externa` | InteligenciaExternaPage | `inteligencia_externa.view` | OK |
| Análisis | Continuidad | `/continuidad` | ContinuidadPage | `continuidad.view` | OK |
| Análisis | Integraciones | `/integraciones` | IntegracionesPage | `integraciones.view` | OK |
| Análisis | Costos y valor | `/costos-valor` | CostosValorPage | `finops.view` | OK |
| Análisis | Gobierno de datos | `/gobernanza-datos` | GobernanzaDatosPage | `datos.view` | OK |
| Análisis | Mi seguridad | `/mi-seguridad` | MiSeguridadPage | (autenticado) | OK |
| Análisis | Notificaciones | `/notificaciones` | NotificationsPage | `notification.view` | OK |
| Análisis | Auditoría | `/auditoria` | AuditPage | `audit.view` | OK |
| Admin | Usuarios | `/administracion/usuarios` | AdminUsersPage | `admin.user.view` | OK |
| Admin | Detalle usuario | `/administracion/usuarios/:id` | AdminUserDetailPage | `admin.user.view` | OK |
| Admin | Roles | `/administracion/roles` | AdminRolesPage | `admin.role.view` | OK |
| Admin | Seguridad | `/administracion/seguridad` | AdminSecurityPage | `admin.security.view` / `seguridad.view` | OK |
| Admin | Identidad | `/administracion/identidad` | AdminIdentidadPage | `identidad.view` | OK |
| Admin | Proveedores IA | `/administracion/proveedores-ia` | AdminLlmProvidersPage | `llm.view` | OK |
| Redirect | Organización legacy | `/organizacion` → `/administracion/organizacion` | — | — | OK |

Rutas hijas (detalle empleado, integración, oportunidad, etc.) accesibles desde grillas; no duplican menú lateral.

**Ramas adicionales (sin convergir aún):**

| Rama | Rutas extra en menú |
|------|---------------------|
| `vistas-comercial-valor-pre-fase2-dec7` | `/comercial`, `/tco`, `/implementacion`, `/comercial/segmentacion` |
| `vistas-aprendizaje-optimizacion-multiproveedor-dec7` | `/aprendizaje`, `/optimizacion` |

---

## C. Inconsistencias encontradas

| # | Tipo | Detalle |
|---|------|---------|
| 1 | Terminología | Uso de **tenant** en textos de administración (7 archivos) |
| 2 | Terminología | **Backups**, **restore**, **metadata**, **Preflight**, **Circuit breaker** en UI continuidad/integraciones |
| 3 | Terminología | **NO CALCULABLE** crudo en valoración de oportunidades |
| 4 | Terminología | Login MFA: título genérico "Verificación MFA" (no se encontró "Máster en Bellas Artes" en código actual) |
| 5 | Código huérfano | Import `DashboardPage` sin ruta en `App.tsx` (varias ramas) |
| 6 | Consistencia botones | `AdminSecurityPage`: acciones sin clase `btn` |
| 7 | Menú divergente | Cada rama de vistas añade ítems distintos en "Análisis" (esperado pre-convergencia) |
| 8 | Solapamiento conceptual | Comercial y valor vs Costos y valor (comercial branch) — unificar etiquetas en convergencia |
| 9 | Página huérfana | `OrganizationPage.tsx` sin ruta (solo redirect a admin) — limpieza post-convergencia |
| 10 | Grillas | Comercial/aprendizaje: algunas vistas sin columnas configurables (infra existe en integraciones/identidad) |

**Rutas rotas:** ninguna detectada en revisión estática + build.

**Exposición de secretos:** no se observaron tokens/TOTP/API keys en vistas de detalle revisadas.

---

## D. Correcciones realizadas

Portable vía `frontend/src/lib/uiTerms.ts` + ajustes de texto:

- `tenant` → **organización** en administración
- **Respaldos fallidos**, **privacidad y restauración**, eventos de continuidad en español
- **Validación previa** (antes Preflight), **cortacircuitos** (antes Circuit breaker)
- **Autenticación multifactor (MFA)** en pantalla de login
- **No calculable** (antes NO CALCULABLE) en retorno y periodo de recuperación
- Botones de seguridad admin con clase `btn` / `btn primary`
- Eliminación import huérfano `DashboardPage`

---

## E. Commits exactos por rama

| Rama base | Rama corrección | Commit |
|-----------|-----------------|--------|
| `cursor/vistas-identidad-seguridad-accesos` | `cursor/control-visual-navegacion-3581` | `b96e68355c1fa42321b4dcafa30e4e9fd4fb7920` |
| `cursor/vistas-integraciones-gobierno-continuidad` | `cursor/control-visual-navegacion-integraciones-3581` | `c045bd1a79af78d078a2c196c91a62160ac9ab44` |
| `cursor/vistas-comercial-valor-pre-fase2-dec7` | `cursor/control-visual-navegacion-comercial-3581` | `42712f80a8155d14f829112976080f23c217b1fb` |
| `cursor/vistas-aprendizaje-optimizacion-multiproveedor-dec7` | `cursor/control-visual-navegacion-aprendizaje-3581` | `a9ea000071c133dce9de6468cdcadd4e332056d5` |

`cursor/vistas-identidad-seguridad-accesos` incluye fast-forward a `b96e683` (mismo contenido que control-visual identidad).

---

## F. Pendientes solo resolvibles tras convergencia

1. **Unificar `AppShell` MENU** con ítems de comercial + aprendizaje + integraciones + identidad en una sola lista ordenada.
2. **Unificar `ROUTE_PERMISSIONS`** con rutas comerciales y de aprendizaje.
3. **Eliminar** `OrganizationPage.tsx` y `DashboardPage.tsx` si no se usan.
4. **Replicar grilla configurable** (columnas/filtros) en vistas comercial/aprendizaje donde falte.
5. **Resolver solapamiento** Comercial y valor ↔ Costos y valor (nombres y entrada de menú única).
6. **Menú aprendizaje:** reincorporar Continuidad, Integraciones, Gobierno, Identidad, Mi seguridad cuando converja con cadena completa.

---

## G. Recorrido visual final propuesto (humano, post-convergencia)

1. **Login** — `/login`
2. **Centro de Control** — `/` *(sin modificar página)*
3. **Inteligencia externa** — `/inteligencia-externa`
4. **Oportunidades** — `/oportunidades` → detalle
5. **Integraciones** — `/integraciones` → detalle → trazabilidad
6. **Gobierno de datos** — `/gobernanza-datos`
7. **Continuidad** — `/continuidad`
8. **Aprendizaje** — `/aprendizaje` → detalle
9. **Optimización / recomendaciones** — `/optimizacion`
10. **Proveedores IA** — `/administracion/proveedores-ia`
11. **Costos IA** — `/costos-valor`
12. **Comercial** — `/comercial` → propuesta/plan
13. **Valor / TCO** — `/tco`, `/implementacion`
14. **Usuarios** — `/administracion/usuarios` → detalle identidad
15. **Identidad empresarial** — `/administracion/identidad`
16. **Seguridad** — `/administracion/seguridad`
17. **Auditoría** — `/auditoria`

---

## Pruebas

| Rama | `npm run build` |
|------|-----------------|
| control-visual-navegacion-3581 (identidad) | PASS |
| control-visual-navegacion-integraciones-3581 | PASS (mismo commit tree) |
| control-visual-navegacion-comercial-3581 | PASS |
| control-visual-navegacion-aprendizaje-3581 | PASS |

---

## Archivos clave portable

- `frontend/src/lib/uiTerms.ts` — helpers de etiquetas UI
- `frontend/src/pages/integrationLabels.ts` — etapas wiring en español
- Textos en admin, continuidad, integraciones, login, oportunidades
