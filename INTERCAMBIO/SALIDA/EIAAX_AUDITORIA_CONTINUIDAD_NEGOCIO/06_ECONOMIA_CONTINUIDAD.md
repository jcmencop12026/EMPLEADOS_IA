# 06 — Economía y continuidad

**Restricción:** No modificar Motor Económico (1600)  
**Base:** SHA `fbfd6a2`

---

## Cadena económica comercial → operación

```
Valoración 1210 (esperado)
        ↓
Motor Económico 1600 (recomendación precio, economía privada operador)
        ↓
Centro Negocios (decisión precio, fases RECOMENDADO→APROBADO→PRESENTADO→CONTRATADO)
        ↓
Contrato (precio_contratado, modelo_comercial)
        ↓
Snapshot impl (valor_compromiso_json — subconjunto económico)
        ↓
Operación FinOps + MB-07 (consumo real, presupuestos)
        ↓
Renovación/expansión (registro interno 1340)
```

---

## Artefactos por dimensión económica

| Dimensión | Dónde vive | Evidencia |
|-----------|------------|-----------|
| Precio contratado | `negocio_contract_records.precio_contratado`, `ext.precio_contratado` | `negocio_service.contract_proposal` |
| Modalidad comercial | `ext.modelo_comercial`, `contract.modelo_comercial` | `negocio_enums.ModeloComercial` — 6 modalidades |
| Precio recomendado/aprobado | `economic_price_recommendations`, `negocio_price_decisions` | `negocio_service.apply_price_recommendation` |
| Fases precio | `negocio_price_phase_records` | RECOMENDADO, APROBADO, PRESENTADO, CONTRATADO |
| Economía privada operador | `economic_private_economy` | margen, costo real estimado — **no en vista entidad** |
| Consumo incluido | Planificador MB-07 `ConsumptionPlannerOrgConfig` | `consumption_planner_service.py` |
| Consumo adicional / real | FinOps + `aggregate_real_consumption()` | `economic_motor_service.py` L363-419 |
| Costos reales | `EconomicCostEntry` + `FinOpsRecord` | test `test_register_cost_real_creates_finops_and_motor_entry` |
| Valor generado | `EconomicValueEntry`, FinOps value, éxito cliente | múltiples fuentes |
| Margen | Motor privado + TCO tablero impl | `calcular_tco` en tablero |
| Renovación/ampliación | `ExitoClienteRenovacion`, `ExitoClienteExpansion` | solo registro; sin precio automático |

---

## Modalidades comerciales soportadas

**Enum `ModeloComercial`** (`negocio_enums.py`):
- `IMPLEMENTACION_MENSUALIDAD`
- `PROYECTO_FIJO`
- `SUSCRIPCION`
- `VARIABLE_CONSUMO`
- `EXITO_RESULTADOS`
- `HIBRIDO`

**Clasificación:** OPERATIVA en negocio; **PARCIAL** en continuidad post-contrato (no gobierna presupuesto FinOps automáticamente).

---

## Continuidad precio contratado → consumo real

### Lo que funciona
1. Precio contratado persistido en contrato y extensión
2. Motor económico registra costos REAL → FinOps (`economic_motor_service.register_cost`)
3. Planificador MB-07 simula y agrega consumo por clase
4. Tablero impl muestra TCO con `proposal_id` (`tablero_proyecto` L715-718)
5. CC FinOps adapter expone presupuestos y alertas

### Brechas de continuidad

| Brecha | Detalle | Clasificación |
|--------|---------|---------------|
| Contrato → presupuesto FinOps | No se crea budget desde `precio_contratado` | INTEGRACIÓN |
| Modelo comercial → reglas consumo | `VARIABLE_CONSUMO` no activa límites automáticos | EVOLUCIÓN |
| Consumo incluido en contrato | No hay campo en contrato; solo config org MB-07 | PARCIAL |
| Margen contrato vs real | Margen en economía privada; no dashboard por contrato | INTEGRACIÓN |
| Renovación con precio | `ExitoClienteRenovacion` sin monto ni vínculo motor | PARCIAL |
| Facturación | **AUSENTE** — sin invoicing SaaS | AUSENTE |

---

## Duplicidad FinOps vs Motor Económico

| Capa | Rol |
|------|-----|
| FinOps 950/1110 | Registro operativo consumo, presupuestos, alertas |
| Motor 1600 | Facade unificada, economía privada, recomendaciones, agregación |
| Centro Negocios | Consume motor vía `recommend_price(scope_id=proposal_id)` |

**Clasificación:** DUPLICADA en API (`/api/finops` vs `/api/motor-economico`) pero **vigente** — motor es capa superior, no reemplazo.

**Acción:** NO TOCAR motor; integrar vistas que lean ambos sin duplicar lógica.

---

## Privacidad económica

Documentado en `INTERCAMBIO/SALIDA/EIAAX_MOTOR_ECONOMICO/05_PRIVACIDAD_RBAC.md`:
- Vista Entidad: valor cliente, ROI, payback
- Vista Operador: costos, margen, riesgo comercial

Centro Negocios respeta separación (`negocio_service.POTENCIAL_NOTE`, `include_internal` flag).

---

## Semántica POTENCIAL (crítica para economía continua)

> POTENCIAL no cuenta como beneficio realizado ni en ROI/payback realizado.

Aplica en: negocio, motor económico, centro de control adapters.

Riesgo: si renovación usa solo POTENCIAL sin reclasificar, métricas de valor serán inconsistentes.

---

## Matriz economía

| | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|--|---------------------|----------------------------------|-------------------------------------|-------------------|
| Motor económico 1600 | ✓ | — | — | — |
| Fases precio negocio | ✓ | — | — | — |
| FinOps + MB-07 | ✓ | Vincular a contrato/proyecto | Alertas por modalidad | — |
| TCO en tablero impl | ✓ | — | — | — |
| Renovación económica | — | Motor en renovación | ✓ registro sin precio | Facturación |
| Margen por contrato | — | ✓ vista cruzada | — | — |

---

## Conclusión

La **economía operativa** (costos, consumo, presupuestos) es madura. La **economía contractual** (precio acordado, modalidad, consumo incluido) vive en Negocio y **no se propaga** automáticamente a FinOps ni renovación. Integración, no nuevo motor.
