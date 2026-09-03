# EMPLEADOS_IA — BLOQUE 1220
## Diagnóstico transversal multidominio

**Rama:** `cursor/1220-diagnostico-transversal`
**Base:** `5eaad7e4e605465a6ba4145b03c7ec043a5f62b4` (1120 APTO)
**HEAD:** _(ver commit final)_

---

## Objetivo cumplido

Motor de diagnóstico transversal sobre señales 1120, evolucionando el flujo:

**DATOS/SEÑALES → INDICADORES → HALLAZGOS → RELACIONES → DIAGNÓSTICO → CAUSAS PROBABLES → IMPACTO → OPORTUNIDADES → ACCIONES RECOMENDADAS**

Arquitectura genérica (no exclusiva IPS/salud), preparada para señales externas futuras.

---

## Componentes

### Dominios soportados
FINANCIERO, OPERATIVO, COMERCIAL, SERVICIO, CALIDAD, TALENTO_HUMANO, TECNOLOGÍA, LOGÍSTICA, CUMPLIMIENTO, ASISTENCIAL_SALUD, EXTERNO_MERCADO, EXTERNO_REGULACION, EXTERNO_TECNOLOGIA, EXTERNO_DEMANDA, OTRO.

### Modelos (`diagnostic_models.py`)
- `DiagnosticIndicatorDefinition` — dominio, proceso, subproceso, umbrales, periodicidad
- `DiagnosticIndicatorValue` — consolidación desde señales 1120
- `DiagnosticFinding` — HECHO vs INTERPRETACIÓN
- `DiagnosticCorrelation` — correlación sin causalidad automática
- `DiagnosticProbableCause` — CONFIRMADA / PROBABLE / HIPÓTESIS
- `Diagnostic` — diagnóstico versionable y auditable
- `DiagnosticItem` — ítems priorizados con acción recomendada
- `DiagnosticOpportunityLink` — trazabilidad hacia motor 1030

### Servicio (`diagnostic_service.py`)
Pipeline determinístico:
1. Consolidar indicadores desde señales
2. Detectar hallazgos (umbrales + evidencia)
3. Detectar correlaciones transversales
4. Inferir causas probables/hipótesis
5. Generar diagnóstico con explicación estructurada
6. Priorizar ítems (impacto, urgencia, riesgo, magnitud, probabilidad, facilidad, valor)
7. Crear/enlazar oportunidades con deduplicación

### API (`/api/diagnosticos`)
- `GET /dominios`
- `GET|POST /config/indicadores`
- `GET /` — listar diagnósticos
- `POST /generar` — generar diagnóstico
- `GET /{id}` — detalle completo
- `POST /{id}/validar`
- `GET /{id}/trazabilidad`

### Permisos RBAC
- `diagnosticos.view`
- `diagnosticos.generate`
- `diagnosticos.validate`
- `diagnosticos.manage`

### UI (español)
- `/diagnosticos` — lista y generación
- `/diagnosticos/:id` — detalle con hallazgos, causas, correlaciones, oportunidades

### Migración
`1220a1b2c3d4e` (down: `1120a1b2c3d4e`)

---

## Pruebas

```
tests/test_diagnostico_transversal_1220.py — 15 passed
tests/test_senales_reales_1120.py — 11 passed (regresión 1120)
frontend npm run build — PASS
```

---

## Certificación

| Criterio | Resultado |
|----------|-----------|
| DOMINIOS | PASS |
| INDICADORES | PASS |
| HALLAZGOS | PASS |
| CORRELACIONES | PASS |
| CAUSAS | PASS |
| DIAGNÓSTICO | PASS |
| PRIORIZACIÓN | PASS |
| SEÑALES 1120 | PASS |
| OPORTUNIDADES | PASS |
| TRAZABILIDAD | PASS |
| VALOR INTERNO | PASS |
| PREPARACIÓN VALOR EXTERNO | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| UI | PASS |
| TESTS | 26/26 PASS |
| FRONTEND | PASS |
| ALEMBIC | 1220a1b2c3d4e |
| P0 | 0 |
| P1 | 0 |

**VEREDICTO: APTO**

**NO MERGE**
