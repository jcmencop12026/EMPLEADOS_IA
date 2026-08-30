# CERTIFICACIÓN INDEPENDIENTE POST-6E — AGENTE A

**Ámbito:** Centro de Control Ejecutivo / Semántica / Valor  
**Fecha:** 2026-08-30  
**Modo:** Solo lectura / certificación — sin correcciones, sin integración, sin modificación de rama central  
**Rama base declarada:** `cursor/fase2-central-integracion`  
**HEAD certificado:** `3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b`  
**Mensaje:** `feat(tramo6e): Centro de Control Ejecutivo único integrado`  
**Rama origen commit:** `cursor/tramo6e-centro-control-85e4`  
**Worktree de inspección:** `/tmp/cert-post6e-a` (detached HEAD, working tree clean)

---

## Verificación SHA obligatoria

```bash
git -C /tmp/cert-post6e-a status
# HEAD detached at 3a8b7e7... — nothing to commit, working tree clean

git -C /tmp/cert-post6e-a rev-parse HEAD
# 3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b

git -C /tmp/cert-post6e-a show --no-patch --oneline HEAD
# 3a8b7e7 feat(tramo6e): Centro de Control Ejecutivo único integrado
```

**CONFIRMADO:** HEAD corresponde exactamente a `3a8b7e7`.

---

## Resumen ejecutivo

Certificación independiente del **Centro de Control Ejecutivo integrado en Tramo 6E**, concentrada en agregación única, datos reales, semántica, valor empresarial, oportunidades/riesgos, gobierno y no-duplicación. No se realizó auditoría genérica de toda la plataforma.

| Área | Resultado |
|------|-----------|
| Centro de Control único | **CERTIFICADO** |
| Datos reales (sin KPIs inventados) | **CERTIFICADO** |
| Semántica HECHO/INFERENCIA/RECOMENDACIÓN | **CERTIFICADO** |
| VERIFICADO / ESTIMADO / POTENCIAL | **CERTIFICADO** |
| POTENCIAL excluido de realizado | **CERTIFICADO** |
| Gobierno G1–G4 / autoejecución | **PRESERVADO** |
| Oportunidades y riesgos | **CERTIFICADO** |
| Trazabilidad ejecutiva | **CERTIFICADO** |

---

## Salida final obligatoria

```
SHA: 3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b
CENTRO CONTROL ÚNICO: CERTIFICADO — una sola experiencia ejecutiva (UI en /, API /api/centro-control); sin segundo CC, sin Centro Salud independiente, sin segundo FinOps ni segunda bandeja Mi Trabajo.
DATOS REALES: CERTIFICADO — indicadores desde consultas/adaptadores reales; estado "Sin información disponible" cuando no hay fuente; sin constantes KPI ficticias en capa CC.
SEMÁNTICA: CERTIFICADO — contrato HECHO/INFERENCIA/RECOMENDACIÓN/SIN_CLASIFICAR; badges UI; explicaciones 1220 con certeza y nota causal; POTENCIAL mapeado a INFERENCIA.
VERIFICADO/ESTIMADO/POTENCIAL: CERTIFICADO — _sum_valor_por_naturaleza() y adaptadores 1210/1280; UI separa verificado/estimado/potencial/realizado.
POTENCIAL EXCLUIDO: CERTIFICADO — realizado = verificado + estimado; POTENCIAL no entra en ROI/payback/precio sugerido (commercial_service + nota explícita).
G1-G4: PRESERVADO — gate post-6D intacto en auditor_factory_bridge y optimization_service.
AUTOEJECUCIÓN: BLOQUEADA — API CC solo GET; CC observa/navega/recomienda; sin endpoints de ejecución en control_center router.
OPORTUNIDADES: CERTIFICADO — valor_potencial separado de materializado/realizado; adaptador 1100 desde proactive_service y tablas Opportunity.
RIESGOS: CERTIFICADO — riesgos desde implementación, inteligencia externa y diagnóstico con origen/bloque; no scoring ficticio como hecho.
TRAZABILIDAD: CERTIFICADA — indicadores con enlace a módulo fuente; explicaciones con evidencia e identificador; adaptadores declaran bloque/modulo.

PRUEBAS: 76 passed focal (CC 6E + porque P1 + cableado + 1230 + 1250c + gate G1-G4); adversarial valor/API GET-only PASS.

P0: 0
P1: 0
P2: 4

VEREDICTO: APTO PARA CONVERGENCIA FINAL
```

---

## 1. Centro de Control único

### Arquitectura verificada

| Capa | Artefacto | Rol |
|------|-----------|-----|
| UI | `CentroControlPage.tsx` en ruta índice `/` | Única experiencia ejecutiva con 6 pestañas |
| API | `GET /api/centro-control/resumen-ejecutivo` | Solo lectura |
| Servicio | `control_center_service.get_executive_summary()` | Agregador único |
| Adaptadores | `control_center_adapters.py` | Contratos por módulo (1100–1340, MB-07/11/12, Auditor, Mi Trabajo, Continuidad) |

### No duplicación funcional

| Riesgo auditado | Resultado |
|-----------------|-----------|
| Segundo Centro de Control | **NO** — un solo `CentroControlPage`; `/panel` redirige a `/` |
| Centro Salud independiente | **NO** — `/salud/diagnostico` es módulo IPS separado; sección "Salud" en CC usa `build_health_report()` de plataforma |
| Segundo FinOps | **NO** — `/costos-valor` es detalle operativo; CC integra resumen vía `FinOpsExtendidoAdapter` y MB-07 |
| Segunda bandeja Mi Trabajo | **NO** — `MiTrabajoAdapter` expone `trabajo_service.resumen()` (conteos), no `collect_items()` |
| Rutas API mutantes en CC | **NO** — router `control_center.py` exclusivamente `GET` |

**Nota P2:** la URL documentada `/centro-control` no existe como ruta frontend; la experiencia única está en `/` con API bajo `/api/centro-control`. No hay duplicación funcional.

---

## 2. Semántica

### Contrato backend

`control_center_service.SEMANTICA_CONTRATO`:

- `HECHO` — dato observado o verificado en fuente primaria
- `INFERENCIA` — derivado de cálculo/estimación/correlación
- `RECOMENDACIÓN` — acción sugerida; requiere decisión humana
- `SIN_CLASIFICAR` — sin clasificación disponible

### Mapeo valor → semántica

`SEMANTICA_VALOR` en adaptadores:

| Naturaleza valor | Semántica |
|------------------|-----------|
| VERIFICADO | HECHO |
| ESTIMADO | INFERENCIA |
| POTENCIAL | INFERENCIA |

### UI

`CentroControlPage.tsx` — componente `SemanticBadge` diferencia HECHO / INFERENCIA / RECOMENDACIÓN en paneles de valor y explicación.

### Explicaciones 1220 (POR QUÉ)

`DiagnosticoExplicacionAdapter` → `diagnostic_service.build_executive_explanations()`:

- Elementos con `tipo_contenido`, `certeza`, `certeza_codigo` (PROBABLE, HIPÓTESIS)
- `nota_causalidad`: correlaciones no implican causalidad demostrada
- Tests `test_centro_control_porque_p1.py` — PASS

**Conclusión:** hechos no se presentan como inferencias en la capa explicativa auditada; recomendaciones diferenciadas; ausencia de dato → mensaje explícito, no maquillaje.

---

## 3. Valor — VERIFICADO / ESTIMADO / POTENCIAL

### Separación en agregación

`_sum_valor_por_naturaleza()` (`control_center_adapters.py`):

```python
realizado = verificado + estimado  # POTENCIAL excluido
```

### Fuentes reales

| Adaptador | Fuente |
|-----------|--------|
| ValorRetornoAdapter (1210) | `OpportunityValuationReal.value_nature`, costos ejecución |
| ComercialResumenAdapter (1280) | `CommercialProposalValue.naturaleza` |
| Oportunidades | `proactive_service.business_summary()` — `valor_potencial_total` / `valor_materializado_total` separados |

### Exclusión POTENCIAL — casos adversariales

| Caso | Resultado |
|------|-----------|
| `_sum_valor_por_naturaleza(VERIFICADO=100, ESTIMADO=50, POTENCIAL=9999)` | `valor_realizado=150`, `valor_potencial=9999` |
| `_aggregate_values_by_nature` comercial (VERIFICADO=100, POTENCIAL=5000) | `valor_atribuible_precio=100` |
| `commercial_service.suggest_price` | Documenta: POTENCIAL no entra al precio sugerido |
| UI valor | Potencial con clase `potential-excluded`; nota `nota_potencial` en API |

### ROI / payback

- `ValorRetornoAdapter.retorno_porcentaje` calculado desde `valor_atribuible` (registros `OpportunityValuationReal`) y costos — no desde `valor_potencial` de oportunidades abiertas.
- `ComercialResumenAdapter.roi_promedio` / `payback_promedio_meses` desde propuestas cuyo `valor_atribuible_total` excluye POTENCIAL en motor comercial.

**CRÍTICO verificado:** POTENCIAL no se suma al valor realizado ni entra en precio sugerido basado en valor realizado.

---

## 4. Datos reales

### Indicadores ejecutivos

`_build_indicators()` — cada indicador toma `ctx[id]` de consultas reales (conteos SQL, `finops_service`, `proactive_service`, adaptadores). Si `valor is None` → `disponible: false`, `estado: "Sin información disponible"`.

### Sin hardcode como KPI

- No se encontraron constantes numéricas presentadas como resultados en `control_center_service` ni adaptadores auditados.
- Adaptadores sin datos retornan `_no_disponible()` con mensaje explícito (ej. "Sin valoraciones registradas", "Sin proyectos de implementación").
- Módulo Salud IPS (`/salud/diagnostico`, fixtures demo) **no** alimenta el Centro de Control ejecutivo.

### Señales sintéticas

`SenalesAdapter` expone desglose `por_modo_ingesta` (REAL / SINTETICO / PRUEBA) — no oculta origen.

---

## 5. Gobierno — G1–G4 y autoejecución

Centro de Control **no ejecuta** acciones de Fábrica ni optimización:

- Router CC: solo `GET`
- Adaptadores: consultas read-only
- Enlaces de atención requerida navegan a módulos con gobierno propio (`/aprobaciones`, `/trabajo`, `/empleados/auditoria`)

**Gate post-6D preservado** (verificación en mismo SHA):

- `auditor_factory_bridge._validate_human_factory_decision()` — presente
- `auto_execution_blocked: True` — presente
- `optimization_service` rechaza AUTOMATICA sobre `PENDIENTE_APROBACION`
- Tests `test_gate_post6d_correcciones.py` — PASS en suite focal

CC observa, recomienda y navega; no es mecanismo oculto de ejecución.

---

## 6. Oportunidades y riesgos

### Oportunidades

- `OportunidadesAdapter` — estados operativos reales desde `Opportunity`
- `valor_potencial` ≠ `valor_materializado` ≠ `valor_realizado` en `valor_consolidado`
- Optimización (1290) en CC: conteos y enlaces; ejecución solo en módulo `/optimizacion`

### Riesgos

- `ImplementacionAdapter` — `hitos_en_riesgo`, `riesgos_abiertos` desde tablas implementación
- `InteligenciaExternaAdapter` — `riesgos_abiertos`, fuentes activas, señales con clasificación
- `DiagnosticoAdapter` — riesgos desde hallazgos 1220
- Certeza PROBABLE/HIPÓTESIS etiquetada; no presentada como hecho demostrado

---

## 7. Trazabilidad

Muestras verificadas:

| Indicador / elemento | Rastreo a fuente |
|---------------------|------------------|
| Empleados activos | `AIEmployee` count por org |
| Consumo IA | `finops_service` dashboard |
| Valor verificado | `OpportunityValuationReal.value_nature=VERIFICADO` |
| Explicación causal | `DiagnosticProbableCause` + evidencia JSON |
| MB-07 consumo | `consumption_planner_service.centro_control_contract` |
| Auditor empleados | `EmployeeAuditFinding` / assessments |
| Cada indicador UI | campo `enlace` a módulo detalle |

Adaptadores declaran `modulo`, `bloque`, `enlace` en respuesta API.

---

## 8. Pruebas ejecutadas (independientes)

```bash
export DATABASE_URL="sqlite:////tmp/cert-post6e-a-tests.db"
export JWT_SECRET="cert-post6e-a-secret"
rm -f /tmp/cert-post6e-a-tests.db

cd /tmp/cert-post6e-a
python -m pytest \
  tests/test_centro_control_tramo6e.py \
  tests/test_centro_control_porque_p1.py \
  tests/test_centro_control_cableado_ejecutivo_fase2.py \
  tests/test_bloque_1250c_centro_control_integrado.py \
  tests/test_bloque_1230_centro_control.py \
  tests/test_gate_post6d_correcciones.py \
  -q
```

**Resultado:** `76 passed, 0 failed` (~25 s)

### Verificación adversarial adicional

- Exclusión POTENCIAL en agregación valor — PASS
- Exclusión POTENCIAL en precio comercial — PASS
- API Centro de Control solo métodos GET — PASS

---

## 9. Clasificación de hallazgos

### P0 — 0

Sin fuga tenant, ejecución no autorizada vía CC, ni valor materialmente falso en rutas auditadas.

### P1 — 0

Sin métrica ejecutiva falsa material, semántica incorrecta grave, POTENCIAL contabilizado como realizado, duplicación funcional grave ni gobierno roto en el ámbito CC/valor/semántica.

### P2 — 4 (no bloqueantes)

1. **URL frontend** — experiencia en `/` no en `/centro-control` (API sí usa prefijo correcto).
2. **MiTrabajoAdapter** — resumen usa primer usuario de la org, no el autenticado; puede imprecisar conteos en orgs multi-usuario (no fuga cross-tenant).
3. **DashboardPage** — import residual en `App.tsx` sin ruta activa (código muerto, no segundo dashboard).
4. **ROI/payback comercial promedio** — agregación a nivel propuesta sin desglose por naturaleza en UI CC (motor subyacente sí excluye POTENCIAL del precio).

---

## 10. VEREDICTO

**APTO PARA CONVERGENCIA FINAL**

- Centro de Control Ejecutivo único integrado correctamente en Tramo 6E
- Datos reales, semántica y separación de valor certificados
- POTENCIAL excluido de realizado/ROI/precio
- Gobierno post-6D (G1–G4, `auto_execution_blocked`) preservado
- **P0 = 0, P1 = 0**

---

*Certificación independiente Agente A — modo solo lectura. Rama central no modificada.*
