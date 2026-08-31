# 11 — Recomendación siguiente lote

**Principio rector:** Integrar antes de construir. Solo desarrollar donde la matriz marca REALMENTE AUSENTE con evidencia operativa.

**Base auditada:** SHA `fbfd6a2` — Centro de Negocios cierre integral  
**Agente:** B — Solo recomendación; **no iniciar desarrollo** en este lote

---

## Respuesta a la pregunta de misión

> ¿EIAAX ya puede tomar un cliente contratado y llevarlo de manera continua por CONTRATACIÓN → … → RENOVACIÓN?

**Sí, de forma parcial-operativa:**

| Etapa | ¿Puede hoy? | Nivel |
|-------|-------------|-------|
| Contratación | Sí | OPERATIVA |
| Preparación | Sí | OPERATIVA (readiness, requisitos) |
| Implementación | Sí | OPERATIVA con gaps sub-entidades |
| Puesta en marcha | Sí | OPERATIVA (piloto + go-live) |
| Operación | Sí | OPERATIVA (empleados, auto, FinOps, soporte) |
| Seguimiento | Sí | PARCIAL (éxito cliente, salud) |
| Medición | Sí | PARCIAL (distribuida, sin vista única) |
| Optimización | Sí | PARCIAL (optimización 1290, aprendizaje 1260 — no auto-enlazado) |
| Renovación/ampliación | Parcial | Registro API; sin workflow comercial |

La continuidad **existe en módulos**; falta **hilo conductor integrado** entre ellos.

---

## Lote recomendado (solo integración/evolución)

### Fase 1 — Continuidad contrato→implementación (P0-P1)

**Objetivo:** Que la conversión transfiera compromiso real sin nuevo módulo.

| # | Acción | Tipo | Archivos tocados (estimado) |
|---|--------|------|----------------------------|
| 1.1 | Enriquecer `convert_to_implementacion`: alcance desde perspectivas/supuestos, condiciones desde contrato, `modelo_comercial` en snapshot | EVOLUCIÓN | `negocio_service.py`, `implementacion_service.py` |
| 1.2 | Exponer en tablero/detalle impl: `opportunity_id`, `evaluacion_id`, link contrato/PDF vía JOIN | INTEGRACIÓN | `implementacion_service.tablero_proyecto`, frontend detalle |
| 1.3 | Garantizar `contract_record` en toda ruta ACEPTADA | EVOLUCIÓN | `negocio_service.transition_proposal` o conversión |
| 1.4 | Pasar `condiciones` desde router convertir | INTEGRACIÓN | `centro_negocios.py` |

**No hacer:** nuevo módulo implementación.

### Fase 2 — Completar ciclo vida 1340 (P1)

| # | Acción | Tipo |
|---|--------|------|
| 2.1 | Endpoints: completar tarea, resolver bloqueador, completar requisito | EVOLUCIÓN API existente |
| 2.2 | UI mínima para operaciones anteriores | EVOLUCIÓN frontend existente |
| 2.3 | Validar dependencias en `completar_hito` | EVOLUCIÓN servicio |

**No hacer:** tabla entregables salvo requerimiento explícito (B05 — usar evidencia en hitos).

### Fase 3 — Economía continua (P1)

| # | Acción | Tipo |
|---|--------|------|
| 3.1 | Al contratar: opcional crear `FinOpsBudget` desde `precio_contratado` + `modelo_comercial` | INTEGRACIÓN negocio→finops |
| 3.2 | Tab compromiso vs consumo en detalle negocio/impl | INTEGRACIÓN vista |

**No hacer:** modificar Motor Económico 1600.

### Fase 4 — Compromiso→resultado (P1)

| # | Acción | Tipo |
|---|--------|------|
| 4.1 | Vista cruzada: snapshot impl + objetivos éxito + valoración real oportunidad | INTEGRACIÓN |
| 4.2 | Enlace desde CC a detalle por `proposal_id` | INTEGRACIÓN |

**No hacer:** Inteligencia de Resultados nueva (Agente D).

### Fase 5 — Renovación y expansión (P2)

| # | Acción | Tipo |
|---|--------|------|
| 5.1 | UI renovación/expansión en `ImplementacionDetailPage` | EVOLUCIÓN |
| 5.2 | `create_renovacion` → opcional crear `Opportunity` tipo RENOVACION | INTEGRACIÓN impl→1030 |
| 5.3 | Pipeline negocio desde oportunidad renovación | INTEGRACIÓN |

**No hacer:** CRM nuevo.

### Fase 6 — Gobierno y duplicaciones (P1-P2)

| # | Acción | Tipo | Responsable |
|---|--------|------|-------------|
| 6.1 | Swap `LocalNegocioApprovalAdapter` → Gobierno Operacional | INTEGRACIÓN | Agente A + B |
| 6.2 | Redirect/guard: propuestas activas solo en Centro Negocios | INTEGRACIÓN UI | B |
| 6.3 | Regla incidente: soporte vs continuidad | INTEGRACIÓN | Operaciones |
| 6.4 | Adapter Knowledge en CC | INTEGRACIÓN | B |

### Fase 7 — Offboarding selectivo (P2)

| # | Acción | Tipo |
|---|--------|------|
| 7.1 | Evento `negocio_contract_closure` + checklist retiro coordinado empleados | EVOLUCIÓN/AUSENTE mínimo |
| 7.2 | Workflow cierre proyecto `CERRADO` con gates | EVOLUCIÓN 1340 |

**No hacer:** offboarding org completo en este lote (P3).

---

## Qué NO recomendar (explícitamente)

| Propuesta | Motivo |
|-----------|--------|
| Nuevo módulo Implementación | 1340 operativo |
| Nuevo CRM | 1030 + 1280 + 1700 cubren |
| Nueva facturación | Fuera alcance; FinOps suficiente consumo |
| Reescribir Motor Económico | Restricción misión + 1600 estable |
| PIIAX | Fuera alcance |
| Migraciones arquitectónicas | Misión auditoría prohíbe |
| Merge de ramas | GENERAL integra |

---

## Criterios de aceptación próximo lote

1. Conversión muestra alcance real y links a oportunidad/evaluación/contrato/PDF
2. Operador puede completar tarea y resolver bloqueador sin SQL
3. Presupuesto FinOps opcional al contratar con alerta desviación
4. Vista prometido vs medido accesible desde detalle impl o negocio
5. Renovación crea oportunidad enlazada (configurable)
6. Cero tablas nuevas salvo `contract_closure` si Fase 7.1 aprueba

---

## Dependencias entre agentes

| Agente | Entrega necesaria |
|--------|-------------------|
| A (Gobierno Operacional) | Adapter aprobaciones transversal para B14 |
| D (Resultados) | Ya entregado — solo integrar vistas |
| GENERAL | Merge ramas antes E2E convergencia final |

---

## SHA y trazabilidad de esta auditoría

| Item | Valor |
|------|-------|
| SHA base | `fbfd6a2828d70deee566c412bda3f65c9ca3bc94` |
| Rama auditoría | `cursor/auditoria-continuidad-negocio-3581` |
| Entregables | `INTERCAMBIO/SALIDA/EIAAX_AUDITORIA_CONTINUIDAD_NEGOCIO/` (01-11) |
| Desarrollo | **Ninguno** — documentación únicamente |

---

## Cierre

El siguiente lote debe ser **Integración de Continuidad Comercial** (~6 fases), no un bloque producto nuevo. Construir únicamente: (a) cierre contractual B16 si negocio lo valida, (b) completar API ciclo vida 1340. Todo lo demás es cableado de lo que EIAAX ya tiene.
