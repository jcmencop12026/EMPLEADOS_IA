# 07 — Cambios de alcance, renovación y expansión

**Restricción:** No construir CRM  
**Base:** SHA `fbfd6a2`

---

## A. Cambios de alcance

### Capacidades existentes

| Escenario | Mecanismo | Evidencia | Clasificación |
|-----------|-----------|-----------|---------------|
| Cambio en negociación pre-contrato | `register_negotiation` + nueva versión | `negocio_service.py` L560-567 | OPERATIVA |
| Nueva versión propuesta | `create_version_snapshot` triggers | `ProposalVersionTrigger` enum | OPERATIVA |
| Reset aprobaciones post-negociación | `get_approval_adapter().reset_for_version` | `negocio_approval_adapter.py` | OPERATIVA |
| Decisión precio modificada | `negocio_price_decisions` | `apply_price_recommendation` | OPERATIVA |
| Transición estado propuesta | `transition_proposal` | máquina estados 1280 | OPERATIVA |
| Cambio post-contrato en implementación | Update proyecto alcance/objetivos | `update_proyecto` — campos limitados | PARCIAL |
| Change request formal | — | — | **AUSENTE** |
| Impacto económico cambio | Motor recalcula con nuevo scope | manual, `recommend_price` | PARCIAL |
| Nueva versión acuerdo post-firma | Versionado negocio en propuesta ACEPTADA | posible vía negociación pero sin entidad "amendment" | PARCIAL |
| Implementación adicional | Nuevo proyecto impl con mismo `proposal_id` o nueva propuesta | técnicamente posible; no guiado | PARCIAL |

### Representación actual de "cambio solicitado"

**Pre-contrato:** `NegocioNegotiationEntry` — campos `solicitud_cliente`, `respuesta`, `impacto_precio`, `crear_nueva_version`

**Post-contrato:** No hay entidad dedicada. Opciones de facto:
1. Nueva propuesta comercial + extensión negocio (ciclo comercial completo)
2. `ExitoClienteExpansion` con `tipo` y `descripcion` (registro interno, no contractual)
3. Negociación en propuesta ya ACEPTADA (no bloqueado en código, pero sin workflow amendment)

### Impacto económico y aprobación

| Fase | Impacto económico | Aprobación |
|------|-------------------|------------|
| Pre-presentación | Motor 1600 + `negocio_price_decisions` | `negocio_approval_records` |
| Post-contrato | Manual vía nueva propuesta | Mismo flujo comercial |
| Post-go-live | FinOps presupuesto manual | `employee.rollback` / aprobaciones operación |

**Clasificación cambios de alcance:** PARCIAL — fuerte pre-contrato; débil post-contrato formal.

---

## B. Renovación

### Capacidades existentes

| Capa | Detalle |
|------|---------|
| Modelo | `ExitoClienteRenovacion` — `proyecto_id`, `plan_id`, `fecha_renovacion`, `estado` |
| Enum | `EstadoRenovacion` — PENDIENTE, EN_NEGOCIACION, RENOVADO, NO_RENOVADO, etc. |
| API | `POST /api/implementacion/exito/renovaciones` |
| Servicio | `create_renovacion` — create-only |
| Tablero | Muestra última renovación (`tablero_proyecto` L712, L738) |
| Test | `test_renovacion_expansion` |
| UI | **AUSENTE** |
| Workflow | **AUSENTE** — no transiciones de estado vía API |
| Enlace comercial | **AUSENTE** — no crea oportunidad/propuesta automática |

**Clasificación:** PARCIAL — registro estructural sin operación comercial.

---

## C. Expansión / upsell / cross-sell

### Capacidades existentes

| Capa | Detalle |
|------|---------|
| Modelo | `ExitoClienteExpansion` — `tipo`, `descripcion`, `recomendacion` |
| API | `POST /api/implementacion/exito/expansiones` |
| Test | `test_renovacion_expansion` |
| UI | **AUSENTE** |

### Equivalentes en otros módulos (no auto-enlazados)

| Módulo | Capacidad | Relación |
|--------|-----------|----------|
| Oportunidades 1030 | Nueva oportunidad desde señal o manual | No desde expansión impl |
| Comercial 1280 | Nueva propuesta | Manual |
| Centro Negocios | Pipeline desde expediente/oportunidad | Manual |
| Segmentación 1310 | Planes verticales | Catálogo, no trigger expansión |

**Término "upsell/cross-sell":** No existe como módulo. Funcionalidad más cercana: `ExitoClienteExpansion.tipo` + pipeline oportunidades manual.

**Clasificación:** PARCIAL (registro) + AUSENTE (workflow comercial automático).

**Restricción respetada:** No construir CRM — usar oportunidades 1030 + negocio 1700 existentes para cablear expansión.

---

## D. Nuevos Empleados IA / procesos / capacidades post-expansión

| Capacidad | Estado |
|-----------|--------|
| Nuevo Empleado IA | OPERATIVA — fábrica completa |
| Nuevo proceso/automatización | OPERATIVA — `AutomationsPage` |
| Nueva capacidad/herramienta | OPERATIVA — `CapabilitiesPage`, `ToolsPage` |
| Certificación antes producción | OPERATIVA — ciclo de vida MB-06 |
| Vínculo expansión → fábrica | AUSENTE — manual |

---

## E. Nuevas oportunidades desde cliente existente

**OPERATIVA** vía:
- `POST /api/oportunidades` (creación manual)
- Señales proactivas 1120
- Evaluación → oportunidad link

**Gap:** Sin botón "crear oportunidad desde renovación/expansión" ni desde salud cliente baja.

---

## Matriz cambios / renovación / expansión

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Negociación pre-contrato | ✓ | — | — | — |
| Versionado + aprobaciones | ✓ | — | — | — |
| Change request post-contrato | — | — | ✓ vía nueva propuesta | Entidad amendment |
| Renovación | — | Oportunidad + negocio | ✓ API sin workflow/UI | — |
| Expansión/upsell | — | Pipeline oportunidades | ✓ registro impl | CRM nuevo |
| Nuevos empleados IA | ✓ | Desde ia_consumo contrato | — | — |

---

## Conclusión

EIAAX **no necesita CRM nuevo** para renovación/expansión: tiene oportunidades, comercial y negocio. La brecha es **cablear** `ExitoClienteRenovacion`/`Expansion` → oportunidad/propuesta y completar workflow/UI. Cambios de alcance post-firma requieren evolución de "amendment" o reutilizar versionado negocio con reglas explícitas.
