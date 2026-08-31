# Mapa final de plataforma — Fase 2

HEAD: ver `CURSOR_FASE2_CONVERGENCIA_FINAL.md`

## Inicio y control

| Nombre visible | Ruta | Módulo | Estado | Permisos principales | Fuente backend | Drill-down |
|---|---|---|---|---|---|---|
| Centro de Control | `/`, `/centro-control`, `/panel`→`/` | Centro de Control | Activo | `control_center.view` | `GET /api/centro-control/resumen-ejecutivo` | Pestañas Resumen/Valor/Operación/IA/Salud |

## Operaciones

| Nombre visible | Ruta | Módulo | Estado | Permisos | Fuente | Drill-down |
|---|---|---|---|---|---|---|
| Mi trabajo | `/trabajo` | Bandeja unificada | Activo | operations/notification/oportunidades/… | `GET /api/trabajo/*` | Detalle ítem |
| Centro de operaciones | `/operaciones` | Operaciones | Activo | `operations.view` | operations_center | `/operaciones/:id` |
| Nueva solicitud | `/operaciones/solicitud` | Operaciones | Activo | `operations.execute` | operations | — |
| Ejecuciones | `/ejecuciones` | Orquestación | Activo | `operations.view` | work plans | `/ejecuciones/:planId` |
| Aprobaciones | `/aprobaciones` | Gobierno | Activo | `operations.view` | approvals | — |
| Automatizaciones | `/automatizaciones` | Automatización | Activo | `automation.view` | automations | wizard, runs |

## Empleados IA

| Nombre visible | Ruta | Módulo | Estado | Permisos | Fuente | Drill-down |
|---|---|---|---|---|---|---|
| Directorio | `/directorio` | Empleados | Activo | `employee.view` | employees | `/empleados/:id` |
| Auditoría empleados | `/empleados/auditoria` | Auditor | Activo | `auditor_empleados.view` | empleados-auditor | hallazgos |
| Crear empleado | `/empleados/nuevo` | Fábrica | Activo | `employee.create` | factory | wizard |
| Capacidades / Herramientas / Conocimiento / Lab | rutas propias | IA | Activo | capability/tool/knowledge/test_lab | respectivos routers | detalle |

## Análisis y valor

| Nombre visible | Ruta | Módulo | Estado | Permisos | Fuente | Drill-down |
|---|---|---|---|---|---|---|
| Líneas base e impacto | `/lineas-base` | 1200 | Activo | `linea_base.view` | baseline | detail |
| Comercial y valor | `/comercial` | 1280 | Activo | `comercial.view` | commercial | planes, propuestas |
| TCO y aliados | `/tco` | 1320 | Activo | `tco.view` | tco | — |
| Implementación | `/implementacion` | 1340 | Activo | `implementacion.view` | implementation | proyecto |
| Centro de oportunidades | `/oportunidades` | 1100 | Activo | `oportunidades.view` | opportunities | detail |
| Señales / Diagnósticos / Inteligencia externa | rutas propias | 1120/1220/1240 | Activo | respectivos | respectivos | detail |
| Continuidad | `/continuidad` | 1360 | Activo | `continuidad.view` | continuidad | — |
| Mesa de Ayuda | `/soporte` | MB-12 | Activo | support.* | soporte | caso |
| Integraciones | `/integraciones` | 1330 | Activo | `integraciones.view` | integraciones | conector, trazabilidad |
| Aprendizaje / Optimización | rutas propias | 1260/1290 | Activo | respectivos | respectivos | detail |
| Costos y valor (FinOps) | `/costos-valor` | 1110/MB-07 | Activo | `finops.view` | finops | único FinOps |
| Gobierno de datos | `/gobernanza-datos` | Datos | Activo | `datos.view` | governance | — |
| Comunicaciones | `/comunicaciones` | MB-11 | Activo | `communications.view` | comunicaciones | — |
| Notificaciones / Auditoría / Mi seguridad | rutas propias | transversal | Activo | respectivos | respectivos | — |

## Administración

| Nombre visible | Ruta | Módulo | Estado | Permisos | Fuente | Drill-down |
|---|---|---|---|---|---|---|
| Empresas | `/administracion/empresas` | Plataforma | Activo | `platform.organization.view` | admin orgs | — |
| Usuarios / Roles / Organización / Config | rutas admin | Identidad/RBAC | Activo | admin.* | admin routers | user detail |
| Proveedores IA | `/administracion/proveedores-ia` | 1270 | Activo | `llm.view` | llm | — |
| Seguridad / Identidad empresarial | rutas admin | SSO/SCIM | Activo | seguridad/identidad | admin | — |

## Duplicidades resueltas en convergencia

- **Centro de Control:** una página, rutas `/` y `/centro-control` equivalentes.
- **Mi Trabajo:** una bandeja `/trabajo`; menú sin duplicado.
- **FinOps:** canónico en `/costos-valor`; CC solo resumen con enlace.
- **DashboardPage:** sin ruta (eliminado import muerto).

## Rutas alias / redirect

| Alias | Destino |
|---|---|
| `/panel` | `/` |
| `/organizacion` | `/administracion/organizacion` |
