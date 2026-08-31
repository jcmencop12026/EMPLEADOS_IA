# 02 — Modelo canónico Empleado IA

## Entidad principal: `AIEmployee`

Campos MB-06 añadidos (migración `1430a1b2c3d4e`):

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `source_type` | string | MANUAL, ARQUITECTO, OPORTUNIDAD, PROCESO, OPERACIONAL, PLANTILLA_CLON |
| `source_ref` | uuid | Referencia al origen (requerimiento_id, employee_id fuente, etc.) |
| `requerimiento_id` | uuid | FK lógica a `EmpleadoIARequerimiento` |
| `dossier_id` | uuid | FK lógica a `DossierEmpresarial` |
| `autonomy_level` | string | ASISTIDO, SUPERVISADO, AUTONOMO_LIMITADO |
| `is_template` | bool | Plantilla vs instancia operativa |

## Campos existentes que cubren el modelo canónico

| Concepto | Campo / relación |
|----------|------------------|
| Organización | `organization_id` |
| Nombre | `name`, `code` |
| Propósito / objetivo | `objective`, `EmployeeInstructions.objective_text` |
| Responsabilidades | `role`, `EmployeeInstructions.role_text` |
| Entradas / salidas | `EmployeeInstructions.context_notes` (JSON) |
| Instrucciones / políticas | `EmployeeInstructions.*`, `operating_rules`, `constraints_text` |
| Conocimiento | `EmployeeKnowledgeSource` |
| Herramientas técnicas | `EmployeeToolGrant` → `Tool` |
| Capacidades empresariales | `EmployeeBusinessCapability` (nuevo) |
| Frecuencia / activación | `EmployeeLimits`, metadata en instrucciones |
| Límites | `EmployeeLimits` (costo, concurrencia, timeout) |
| Autonomía | `autonomy_level` |
| Supervisión | `shadow_mode`, aprobaciones |
| Riesgos | `risk_level` |
| Indicadores | `EmployeeMetric`, FinOps |
| Responsable humano | `owner_id`, `created_by_id` |
| Estado | `lifecycle_status`, `status` |
| Versión | `version`, `EmployeeVersion` |
| Modelo IA | `EmployeeModelPolicy`, `model_provider`, `model_name` |

## Capacidades empresariales (`EmployeeBusinessCapability`)

Códigos: `CONSULTAR_DATOS`, `OBTENER_DOCUMENTO`, `ENVIAR_INFORMACION`, `NOTIFICAR`, `ACTUALIZAR_REGISTRO`, `EJECUTAR_PROCESO`, `ANALIZAR`, `GENERAR_INFORME`.

Clasificación operacional: `LECTURA`, `ANALISIS`, `PROPUESTA`, `EJECUCION`.

Compatible con abstracción de capacidades externas (GENERAL / PIIAX futuro).

## Orígenes soportados

- **A** Manual/guidada: `POST /employees`, wizard
- **B** Arquitecto: `POST /employees/from-requerimiento/{id}`
- **C–E** OPORTUNIDAD, PROCESO, OPERACIONAL: campos `source_type` preparados; UI manual asignable
