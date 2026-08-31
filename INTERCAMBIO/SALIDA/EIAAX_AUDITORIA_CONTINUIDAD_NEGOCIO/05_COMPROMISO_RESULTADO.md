# 05 — Compromiso comercial → resultado

**Objetivo:** Verificar trazabilidad diagnóstico → propuesto → aprobado → contratado → implementado → operado → medido  
**Restricción:** No construir Inteligencia de Resultados (Agente D ya entregó capacidades distribuidas)

---

## Cadena de trazabilidad existente

```
Señales 1120 / Diagnóstico 1220
        ↓
Evaluación 1405 (expediente)
        ↓ evaluacion_id
Oportunidad 1030
        ↓ opportunity_id
Valoración 1210 (esperado / escenarios / real)
        ↓
Propuesta comercial 1280 + Extensión Negocio 1700
        ↓ economic_recommendation_id
Motor Económico 1600 (precio, margen privado)
        ↓ versiones + aprobaciones + PDF
Contratación (negocio_contract_records)
        ↓ proposal_id
Implementación 1340 (valor_compromiso_json snapshot)
        ↓ go-live
Operación (empleados, FinOps, ejecuciones)
        ↓
Medición (éxito cliente, valoración real, línea base, oportunidad resultado)
```

---

## Evidencia por eslabón

### 1. Diagnosticado
| Artefacto | Campo/enlace | Archivo |
|-----------|--------------|---------|
| Expediente evaluación | `EvaluacionExpediente` | `evaluacion_models.py` |
| Hallazgos | `EvaluacionHallazgo` | idem |
| Vínculo oportunidad | `EvaluacionOportunidadLink` | idem |
| En propuesta | `ext.evaluacion_id`, `proposal.diagnostic_id` | `negocio_models.py`, creación desde expediente |

### 2. Propuesto
| Artefacto | Campo | Archivo |
|-----------|-------|---------|
| Valores propuesta | `CommercialProposalValue` con `naturaleza` | `commercial_models.py` |
| Perspectivas | `perspectivas_json` | `negocio_proposal_extensions` |
| Trazabilidad | `proposal.traceability_json` | `negocio_service.py` L352 |
| Versiones | `negocio_proposal_versions.snapshot_json` | `negocio_models.py` |

### 3. Aprobado
| Artefacto | Campo | Archivo |
|-----------|-------|---------|
| Aprobaciones multinivel | `negocio_approval_records` | migración 1710 |
| Política org | `negocio_approval_policies` | idem |
| Fases precio APROBADO/PRESENTADO | `negocio_price_phase_records` | idem |

### 4. Contratado
| Artefacto | Campo | Archivo |
|-----------|-------|---------|
| Registro contrato | `negocio_contract_records` | `precio_contratado`, `document_id`, `condiciones` |
| Estado propuesta | `ACEPTADA` | `commercial_proposals.estado` |
| Fase precio CONTRATADO | `negocio_price_phase_records` | `negocio_service.contract_proposal` |

### 5. Implementado
| Artefacto | Campo | Archivo |
|-----------|-------|---------|
| Proyecto | `impl_proyectos` | `proposal_id` |
| Snapshot compromiso | `valor_compromiso_json` | `implementacion_service._snapshot_valor_compromiso` |
| Tablero trazabilidad | `que_vendimos`, `que_prometimos` | `tablero_proyecto` L741-747 |
| Auditoría | `impl_auditoria` | acciones go-live, hitos, etc. |

### 6. Operado
| Artefacto | Campo | Archivo |
|-----------|-------|---------|
| Empleados activos | `AIEmployee.lifecycle_status=ACTIVE` | `orchestration_models.py` |
| Ejecuciones | `WorkPlan`, runs | `operations.py` |
| Consumo | `FinOpsRecord`, `LlmInferenceLog` | `finops_models.py`, `llm_models.py` |

### 7. Medido
| Artefacto | Métrica | Archivo |
|-----------|---------|---------|
| Objetivos éxito | `valor_esperado` vs `valor_medido` | `ExitoClienteObjetivo` |
| Valoración real | `OpportunityValuationReal` | `valuation_models.py` |
| Línea base | `LineaBaseImpacto` | `baseline_models.py` |
| Oportunidad cerrada | `register_result` | `oportunidades.py` L306 |
| Centro Control | `valor_realizado` agregado | `control_center_adapters.py` — semántica VERIFICADO+ESTIMADO |

---

## Indicador prometido vs proyectado vs real

### Prometido (comercial)
- **Fuente:** `CommercialProposal` — `valor_total_esperado`, `roi_pct`, `payback_meses`, líneas `CommercialProposalValue`
- **Naturalezas:** VERIFICADO, ESTIMADO, POTENCIAL (`commercial_enums.ValueNature`)
- **Regla:** POTENCIAL no cuenta en realizado (`negocio_service.POTENCIAL_NOTE`, `economic_motor_service` L39)

### Proyectado (valoración / escenarios)
- **Fuente:** `OpportunityValuationExpected`, `OpportunityValuationScenario`
- **Servicio:** `valuation_service.py`
- **UI:** `OportunidadDetailPage`, `CostosValorPage`

### Real (medición)
| Fuente | Tipo real | Clasificación |
|--------|-----------|---------------|
| `OpportunityValuationReal` | Valor atribuido medido | OPERATIVA |
| `ExitoClienteObjetivo.valor_medido` | Por proyecto impl | OPERATIVA |
| `LineaBaseMedicion` / `LineaBaseImpacto` | Impacto operativo | OPERATIVA |
| FinOps `valor_realizado` | Consumo/valor FinOps | OPERATIVA |
| Motor económico `sum_values_by_nature` | Agregación por naturaleza | OPERATIVA |

### Comparación automática prometido↔real

| Comparación | ¿Automática? | Evidencia |
|-------------|--------------|-----------|
| Snapshot impl vs objetivos éxito | Parcial | `medir_objetivo` compara esperado/medido del plan éxito, no siempre vs snapshot |
| Propuesta vs valoración real oportunidad | Manual | Requiere mismo `opportunity_id` |
| Contrato vs consumo FinOps | Manual | Sin vínculo `contract_id` → presupuesto |
| CC ejecutivo | Agregado org | No por cliente/contrato |

**Clasificación global trazabilidad:** PARCIAL — datos existen en grafos separados; **no hay vista única** prometido→proyectado→real por contrato sin integración.

---

## Semántica de valor (crítica para auditoría)

```46:52:backend/app/services/control_center_adapters.py
SEMANTICA_VALOR = {
    "VERIFICADO": "HECHO",
    "ESTIMADO": "INFERENCIA",
    "POTENCIAL": "INFERENCIA",
    ...
    "nota_potencial": "POTENCIAL no se suma al valor realizado ni entra en ROI/payback realizado",
}
```

Tests: `test_potencial_not_in_realizado` (`test_economic_motor_1600.py`)

---

## Qué NO replicar (Agente D)

Capacidades ya distribuidas que cubren "resultados":
- Línea base 1200
- Valoración 1210
- Éxito cliente 1340
- Motor analítico 1000
- Centro de Control indicadores
- Comunicaciones ejecutivas MB-11

**No construir** módulo nuevo "Inteligencia de Resultados".

---

## Matriz compromiso→resultado

| Eslabón | YA EXISTE Y NO TOCAR | EXISTE PERO REQUIERE INTEGRACIÓN | EXISTE PARCIAL Y REQUIERE EVOLUCIÓN | REALMENTE AUSENTE |
|---------|---------------------|----------------------------------|-------------------------------------|-------------------|
| Diagnóstico→propuesta | ✓ expediente + create desde eval | Vista unificada en impl | — | — |
| Propuesta→contrato | ✓ versiones + PDF + contrato | — | — | — |
| Contrato→impl snapshot | ✓ valor_compromiso_json | Ampliar campos snapshot | Alcance real en snapshot | — |
| Impl→medición valor | ✓ plan éxito | Enlace valoración 1210 | Comparación auto vs prometido | — |
| Operación→real | ✓ FinOps + valoración | Contrato→presupuesto | Dashboard por cliente | — |
| Vista única prometido/real | — | CC + tabs cruzados | ✓ | Módulo IR nuevo |

---

## Conclusión

La trazabilidad **existe en datos** a lo largo de 8+ módulos. La brecha es de **integración y presentación**, no de ausencia de modelos. El siguiente lote debe cablear vistas y comparaciones usando artefactos existentes.
