# 03 — Implementación existente

**Módulo:** 1340 Implementación y Éxito del Cliente  
**Evidencia base:** `implementacion_models.py`, `implementacion_service.py`, `implementacion.py`, `test_implementacion_1340.py`

## Respuesta directa

EIAAX **ya puede** gestionar implementación post-contratación en el camino crítico: proyecto, preparación, piloto, go-live, adopción, medición de valor y salud. Sub-capacidades de planificación diaria (tareas, fases, entregables) existen en modelo pero con **ciclo de vida incompleto**.

---

## Capacidades evaluadas

| Capacidad | ¿Existe? | Clasificación | Evidencia |
|-----------|----------|---------------|-----------|
| Plan (proyecto) | Sí | OPERATIVA | `ImplementacionProyecto`, CRUD parcial |
| Fases | Sí | PARCIAL | `impl_fases`; solo `POST /fases`; sin update/complete |
| Hitos | Sí | OPERATIVA | create + `completar_hito`; recalcula `avance_pct` |
| Responsables | Sí | PARCIAL | `responsable_id` en proyecto; `ResponsabilidadTipo` en fases/hitos; sin asignación masiva |
| Tareas | Sí | PARCIAL | `impl_tareas`; solo create; sin complete/update API |
| Dependencias | Sí | ESTRUCTURAL | `dependencias_json` en fases/hitos; no validadas |
| Entregables | No | AUSENTE | Sin tabla; proxy: `evidencia` en hitos/tareas |
| Fechas | Sí | OPERATIVA | `fecha_inicio`, `fecha_objetivo`, fechas en hitos |
| Riesgos | Sí | PARCIAL | create + nivel auto + alerta; sin cerrar/resolver |
| Avance | Sí | OPERATIVA | % por hitos completados |
| Evidencias | Sí | PARCIAL | Campo en hitos/tareas/capacitaciones |
| Aprobación | Sí | OPERATIVA | Piloto→producción, go-live con gates |
| Puesta en marcha | Sí | OPERATIVA | `aprobar_go_live` — 11 ítems checklist + validaciones |

---

## Modelo de datos (21 tablas)

**Migración:** `1340a1b2c3d4e_implementacion_exito_cliente_1340.py`

### Núcleo implementación
- `impl_proyectos`, `impl_fases`, `impl_hitos`, `impl_tareas`
- `impl_requisitos`, `impl_readiness`, `impl_bloqueadores`, `impl_riesgos`
- `impl_pilotos`, `impl_adopcion`, `impl_plan_adopcion`, `impl_capacitaciones`
- `impl_alertas`, `impl_auditoria`

### Éxito del cliente
- `exito_planes`, `exito_objetivos`, `exito_revisiones`, `exito_planes_accion`
- `exito_renovaciones`, `exito_expansiones`, `exito_salud`

### FKs externas
- `organizations`, `users`, `commercial_proposals`, `commercial_plans`, `tco_proveedores_aliados`, `opportunities`

---

## API REST (27 endpoints)

**Prefijo:** `/api/implementacion`  
**Permisos:** `implementacion.view`, `implementacion.manage`, `implementacion.approve_go_live`, `exito_cliente.*`

### Camino crítico cubierto

| Fase | Endpoints |
|------|-----------|
| Crear/listar proyecto | `GET/POST /proyectos`, `GET/PATCH /proyectos/{id}` |
| Preparación | `/fases`, `/hitos`, `/requisitos`, `/readiness`, `/bloqueadores`, `/riesgos` |
| Piloto | `/pilotos`, `/pilotos/{id}/resultado`, `/pilotos/{id}/aprobar-produccion` |
| Go-live | `POST /proyectos/{id}/go-live` |
| Adopción | `/adopcion`, `/plan-adopcion`, `/capacitaciones` |
| Valor | `/exito/planes`, `/objetivos`, `/objetivos/{id}/medir`, `/acciones`, `/revisiones` |
| Salud | `POST /proyectos/{id}/salud` |
| Tablero | `GET /proyectos/{id}/tablero` |

### Gaps API
- Sin GET list dedicados para sub-entidades individuales (salvo detalle agregado)
- Sin PATCH/DELETE en fases, tareas, requisitos, bloqueadores, riesgos
- Sin endpoint resolver bloqueador / completar requisito / completar tarea

---

## Gates de go-live (OPERATIVA)

**Evidencia:** `aprobar_go_live` L439-469

Bloquea si:
1. Bloqueadores críticos en estado `ABIERTO`
2. Requisitos `bloqueante` no `COMPLETADO`
3. Checklist incompleto (11 ítems `GO_LIVE_ITEMS`)
4. Piloto sin `aprobado_produccion=True`

Éxito → `estado = EN_PRODUCCION`, persiste checklist y observaciones.

**Tests:** `test_go_live_requiere_aprobaciones`, `test_go_live_aprobacion_completa`

---

## Readiness (OPERATIVA)

8 dimensiones: `DATOS`, `TECNOLOGIA`, `INTEGRACIONES`, `PERSONAL`, `GOBIERNO`, `SEGURIDAD`, `PROCESOS`, `APROBACIONES`

Resultado: `LISTO` / `LISTO_CON_OBSERVACIONES` / `NO_LISTO`

**Test:** `test_requisito_bloqueante_y_readiness`

---

## Plan de éxito y medición (OPERATIVA)

- `create_plan_exito` → objetivos con `valor_esperado`
- `medir_objetivo` → calcula desviación, estado valor, plan acción automático si desviación
- `create_revision` → revisiones periódicas
- `calcular_salud` → score ponderado (adopción 25%, valor 25%, hitos 15%, bloqueos 15%, riesgos 10%, uso 10%)

**Tests:** `test_plan_exito_valor_desviacion_accion`, `test_salud_saludable_y_riesgo`

---

## Integraciones existentes

| Módulo | Uso |
|--------|-----|
| 1280 Comercial | FK `proposal_id`, snapshot `valor_compromiso_json` |
| 1320 TCO | `proveedor_id` en hitos; TCO en tablero |
| 1700 Negocio | `convert_to_implementacion` crea proyecto |
| 1250C CC | `ImplementacionAdapter` expone resumen ejecutivo |

---

## Frontend

| Archivo | Cobertura |
|---------|-----------|
| `ImplementacionPage.tsx` | Listado, crear, tablero inline |
| `ImplementacionDetailPage.tsx` | 7 tabs: resumen, hitos, preparación, piloto, adopción, éxito, salud |
| `ImplementationCycleBar.tsx` | Barra ciclo visual |
| `CentroNegociosDetailPage.tsx` | Botón convertir a implementación |
| `ComercialPropuestaDetailPage.tsx` | Link a implementación si existe |

**Clasificación UI:** PARCIAL — orientada a demostración del camino crítico; sin gestión rica de fases/tareas/riesgos.

---

## Estados del proyecto

**Enum `EstadoImplementacion`:** `PLANIFICACION`, `EN_PREPARACION`, `READINESS`, `PILOTO`, `VALIDACION`, `EN_PRODUCCION`, `ADOPCION`, `EXITO_CLIENTE`, `RENOVACION`, `EXPANSION`, `CERRADO` (11 estados)

Transiciones principales cubiertas por servicio; no todas expuestas en UI.

---

## Matriz final implementación

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Proyecto + tablero | ✓ | TCO/propuesta en UI detalle negocio | — | — |
| Hitos + go-live | ✓ | — | Validación dependencias JSON | — |
| Readiness + piloto | ✓ | — | — | — |
| Plan éxito + salud | ✓ | Enlace valoración 1210 / línea base 1200 | — | — |
| Fases/tareas/requisitos | — | — | ✓ ciclo de vida API + UI | — |
| Entregables formales | — | — | — | ✓ entidad dedicada |
| Auto-plan post-contrato | — | — | — | ✓ |

---

## Conclusión

**No construir módulo de implementación nuevo.** El bloque 1340 es operativo para el recorrido contractual→producción→valor. Evolución recomendada solo donde hay evidencia de brecha real (entregables, cierre de tareas/bloqueadores, enriquecimiento de conversión).
