# 10 — Brechas priorizadas

**Metodología:** Solo brechas con evidencia en código/docs; clasificadas en matriz final  
**Base:** SHA `fbfd6a2`

---

## Matriz maestra

| ID | Brecha | Evidencia | Prioridad | Matriz |
|----|--------|-----------|-----------|--------|
| B01 | Conversión no transfiere alcance/condiciones/modelo comercial al proyecto | `negocio_service.convert_to_implementacion` L594-601; `alcance` plantilla | **P0** | EXISTE PARCIAL → EVOLUCIÓN |
| B02 | `opportunity_id`/`evaluacion_id` no en `impl_proyectos` | Modelo L23-51 `implementacion_models.py` | **P1** | REQUIERE INTEGRACIÓN |
| B03 | `contract_id` nulo si ACEPTADA sin `/contratar` | `negocio_service.py` L585-591 | **P1** | EXISTE PARCIAL → EVOLUCIÓN |
| B04 | Sub-entidades impl sin complete/resolve API | `implementacion.py` — solo POST create | **P1** | EXISTE PARCIAL → EVOLUCIÓN |
| B05 | Entregables formales ausentes | Sin tabla en migración 1340 | **P2** | REALMENTE AUSENTE |
| B06 | Contrato → presupuesto FinOps no automático | Sin código en `contract_proposal` | **P1** | REQUIERE INTEGRACIÓN |
| B07 | Renovación/expansión sin UI ni workflow | API create-only; sin frontend | **P2** | EXISTE PARCIAL → EVOLUCIÓN |
| B08 | Renovación/expansión no crea oportunidad | Sin enlace en `create_renovacion` | **P2** | REQUIERE INTEGRACIÓN |
| B09 | Vista única prometido→real por contrato | Datos en 5+ módulos | **P1** | REQUIERE INTEGRACIÓN |
| B10 | Change request post-contrato formal | Sin entidad | **P2** | REALMENTE AUSENTE (o reutilizar versionado) |
| B11 | Provisión empleados IA desde `ia_consumo_json` | Campo en extensión; sin bridge fábrica | **P2** | REQUIERE INTEGRACIÓN |
| B12 | Soporte vs incidentes duplicados | MB-12 + Continuidad 1360 | **P2** | REQUIERE INTEGRACIÓN |
| B13 | Comercial vs Centro Negocios dual UI | Dos rutas misma entidad | **P1** | REQUIERE INTEGRACIÓN |
| B14 | Aprobaciones negocio adapter local | `LocalNegocioApprovalAdapter` | **P1** | REQUIERE INTEGRACIÓN (Agente A) |
| B15 | Knowledge pendiente en CC | `control_center_service.py` | **P3** | REQUIERE INTEGRACIÓN |
| B16 | Cierre contractual / offboarding cliente | Sin registro fin contrato | **P2** | REALMENTE AUSENTE |
| B17 | Offboarding organización | Sin API baja tenant | **P3** | REALMENTE AUSENTE |
| B18 | Facturación SaaS | No módulo | **P3** | REALMENTE AUSENTE (fuera alcance) |
| B19 | Dependencias hitos/fases no validadas | JSON estructural | **P3** | EXISTE PARCIAL → EVOLUCIÓN |
| B20 | Router conversión no pasa `condiciones` | `centro_negocios.py` L416-426 | **P2** | REQUIERE INTEGRACIÓN (bug menor) |

---

## Por matriz final

### YA EXISTE Y NO TOCAR (no abrir brechas artificiales)

| Capacidad | Evidencia |
|-----------|-----------|
| Flujo contratar + convertir | Endpoints operativos + 14 tests negocio |
| Módulo implementación 1340 completo | 21 tablas, go-live, piloto, éxito cliente |
| Motor económico 1600 | 9 tests, facade estable |
| Empleados IA + automatizaciones + FinOps | Operativos con tests |
| Oportunidades, evaluación, valoración | Cadenas FK existentes |
| Centro de Control | 15+ adaptadores |
| Retiro empleado IA | `retire_employee` testado |

### EXISTE PERO REQUIERE INTEGRACIÓN (prioridad integración)

| ID | Integración | Esfuerzo técnico |
|----|-------------|------------------|
| B02 | Denormalizar o resolver refs en vista impl/tablero | Bajo — lectura JOIN |
| B06 | Crear budget FinOps al contratar (opcional por modalidad) | Medio |
| B08 | Botón renovación → oportunidad 1030 | Medio |
| B09 | Tab "compromiso vs real" en detalle impl o negocio | Medio |
| B12 | Regla enrutamiento incidente soporte↔continuidad | Medio |
| B13 | Redirect comercial → centro negocios para propuestas activas | Bajo |
| B14 | Swap `ApprovalPort` a Gobierno Operacional | Medio — contrato listo |
| B15 | Activar adapter Knowledge en CC | Bajo |
| B20 | Pasar `condiciones` en router | Trivial |

### EXISTE PARCIAL Y REQUIERE EVOLUCIÓN

| ID | Evolución | Notas |
|----|-----------|-------|
| B01 | Enriquecer `create_proyecto` en conversión | Copiar perspectivas, condiciones, modelo |
| B03 | Forzar `/contratar` o crear contract record en transición ACEPTADA | Consistencia |
| B04 | Endpoints PATCH complete tarea/bloqueador/requisito | Completar 1340 |
| B07 | UI renovación/expansión + transiciones estado | Sobre API existente |
| B19 | Validar dependencias en `completar_hito` | Lógica servicio |

### REALMENTE AUSENTE (solo construir con evidencia)

| ID | Ausencia | ¿Construir? |
|----|----------|-------------|
| B05 | Entregables | Solo si operación lo exige; proxy actual = evidencia en hitos |
| B10 | Change request post-contrato | Evaluar reutilizar `NegocioNegotiationEntry` + versión |
| B16 | Cierre contractual | Sí — tabla/evento fin contrato |
| B17 | Offboarding org | Bajo prioridad V1 |
| B18 | Facturación | No — fuera alcance EIAAX actual |

---

## Priorización ejecutiva

### P0 — Bloquea continuidad operativa inmediata
- **B01** Alcance vacío en conversión

### P1 — Integración alto valor / riesgo medio-alto
- B02, B03, B04, B06, B09, B13, B14

### P2 — Mejora ciclo vida completo
- B07, B08, B10, B11, B12, B16, B20

### P3 — Deuda o fuera alcance
- B15, B17, B18, B19

---

## Lo que NO es brecha (falsos positivos evitados)

| Supuesto externo | Realidad en fbfd6a2 |
|------------------|---------------------|
| "Falta módulo implementación" | Existe 1340 completo |
| "Falta CRM renovación" | Existen oportunidades + negocio |
| "Falta medición resultados" | Valoración + línea base + éxito cliente + CC |
| "Falta motor económico" | 1600 operativo |
| "Falta go-live" | Gates + tests + UI |
| "Falta operación IA" | Fábrica + automatizaciones + ejecuciones |

---

## Conclusión

**11 brechas P0-P1** de integración/evolución sobre capacidades existentes. **5 ausencias reales** (B05, B10, B16, B17, B18) — solo 2-3 justifican construcción (B10 vía reutilización, B16 cierre contrato). El resto es cableado.
