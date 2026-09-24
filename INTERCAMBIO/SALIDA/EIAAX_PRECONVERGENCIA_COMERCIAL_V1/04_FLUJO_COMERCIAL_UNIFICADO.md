# 04 — Flujo comercial unificado (reconstrucción esperada)

Flujo objetivo post-convergencia A+B+C+D sobre central `75fc689`.

---

## Diagrama de tramos

```
DEMO ──► área/problema ──► prospecto ──► acceso externo ──► información ──► evidencias
  │           │                │              │                  │              │
  D           D+B              A              A                  A              A
  │           │                │              │                  │              │
  ▼           ▼                ▼              ▼                  ▼              ▼
validación ──► suficiencia ──► evaluación ──► hallazgos ──► oportunidades ──► Centro Estratégico
  A+B          A+B              central+C      central+B        B+C            C
  │                                                                              │
  ▼                                                                              ▼
selección presentar ──► presentación ejecutiva ──► propuesta ──► instrumentos ──► cliente
  B+C+D                   B+D                      B              B               A+B
  │                                                                              │
  ▼                                                                              ▼
implementación ──► Empleados IA ──► resultados ──► informes ──► soporte ──► expansión
  central+A          central+A+C      D+central      MB-11+A+D     A+central    B 1720
```

---

## Tramo por tramo

| # | Tramo | Rama principal | Reutiliza | Hueco |
|---|-------|----------------|-----------|-------|
| 1 | DEMO / selección área | **D** | `demo_comercial_service`, seeds | Aislamiento demo/prod OK |
| 2 | Prospecto identidad | **A** | `EntidadEmpresa`, acceso externo | — |
| 3 | Solicitud información contextual | **B** | catálogo contextual `flujo_comercial` | Merge con ítems evaluación central |
| 4 | Evidencias/adjuntos | **A** | `evidencia_entrega_service` | — |
| 5 | Validación / complemento | **A** | estados entrega + gobierno | — |
| 6 | Suficiencia mínima | **A+B** | expediente % + `SuficienciaEvaluacion` B | Una sola autoridad suficiencia |
| 7 | Evaluación / hallazgos | **central** | `evaluacion_service` | C enriquece diagnóstico |
| 8 | Oportunidades | **B+C** | `opportunity_models` + mapa C | Clasificación origen B |
| 9 | Centro Estratégico / comité | **C** | `strategic_control_service`, 4 lecturas | — |
| 10 | Selección qué presentar | **B+C** | `ComercialPresentacionEjecutiva` + cockpit | **?** unificar con D |
| 11 | Presentación ejecutiva / PDF | **D+B** | `presentacion_pdf_service` | Publicación única (A) |
| 12 | Propuesta / economía | **B** | centro negocios + motor 1600 | — |
| 13 | Instrumentos contractuales | **B** | `ComercialInstrumentoContractual` | No software jurídico completo |
| 14 | Prospecto → cliente | **A+B** | `promote_to_cliente` + contrato B | — |
| 15 | Implementación externa | **A** | adapter `implementacion_service` | Requiere `proyecto_id` link |
| 16 | Empleados IA externos | **A** | adapter `agent_factory` | Asignación por contrato |
| 17 | Resultados publicados | **A+D** | vista entidad + resultados 1410 | POTENCIAL ≠ REAL |
| 18 | Informes | **A+D** | MB-11 + adapters | Sin scheduler D autónomo |
| 19 | Soporte externo | **A** | adapter `support_service` | — |
| 20 | Expansión / renovación | **B** | continuidad 1720 | Post-V1 |

---

## Dependencias críticas del flujo

1. **D → expediente** debe crear/usar mismo dossier que B/A (correlation_id).
2. **B flujo comercial** asume motor económico y centro negocios — ya en central, B los extiende.
3. **C cockpit** asume dossier + hallazgos visibles — depende de evaluación + gobierno A.
4. **A portal cliente** asume publicación paquetes + contrato capacidades — depende de B contratación.
5. **D presentación** debe respetar publicación A para exposición externa.

---

## Estados coherentes (cadena externa)

```
SOLICITADO → RECIBIDO → EN_VALIDACION → VALIDADO | REQUIERE_COMPLEMENTO
```

- **A:** entrega + adjuntos.
- **B:** suficiencia evaluación.
- **Central:** expediente `porcentaje_informacion`, `estado_validacion` ítems.

**Hueco:** no hay evento único cross-módulo "suficiencia_global" — GENERAL debe definir contrato en `flujo_comercial_service` ↔ `espacio_externo_service`.
