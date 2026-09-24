# EMPLEADOS_IA — BLOQUE 1230 — CENTRO DE CONTROL EJECUTIVO

**Agente:** D
**Base:** `4c03cbe`
**Rama:** `cursor/1230-centro-control-ejecutivo`
**Alcance:** Capa de consolidación ejecutiva (solo consulta/agregación/presentación)
**Restricción:** Sin duplicar persistencia, sin tocar bloques 1100/1110/1120/1200/1210/1220, V1, PR #32

---

## Principio fundamental

El Centro de Control **no almacena** información operativa. Consulta módulos existentes, agrega en backend y presenta en una vista ejecutiva única.

**Fuente única de verdad:** módulos operativos (`operations`, `oportunidades`, `finops`, `automations`, `notifications`, `audit`, `health`, `llm`).

---

## Componentes implementados

### API agregadora

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/centro-control/resumen-ejecutivo` | Resumen consolidado (una llamada) |
| `GET /api/centro-control/indicadores-config` | Registro de indicadores ejecutivos configurables |

**Permiso:** `control_center.view`

**Filtros:** `periodo` (mtd/7d/30d), `employee_id`, `proceso`, `estado`, `organization_id` (SuperAdmin/plataforma)

### Servicio (`control_center_service.py`)

- Reutiliza: `operations_center.get_summary`, `proactive_service.business_summary`, `finops_service.dashboard_summary`, `build_health_report`
- Agrega: empleados IA + última actividad, atención requerida, automatizaciones fallidas, señales `proactive_signals`, LLM derivado de logs
- Sin auditoría masiva en consultas de lectura

### Adaptadores (`control_center_adapters.py`)

Contratos de integración futura **sin duplicar modelos**:

| Bloque | Adaptador | Estado en base 4c03cbe |
|--------|-----------|------------------------|
| 1100 | `OportunidadesAdapter` | PREPARADO — datos 1030 + nota integración UI 1100 |
| 1110 | `FinOpsExtendidoAdapter` | PREPARADO — FinOps base en sección finops |
| 1120 | `SenalesAdapter` | PARCIAL — `proactive_signals` consolidado |
| 1200 | `ImpactoAdapter` | PREPARADO — contrato `/api/lineas-base` |
| 1210 | `ValorRetornoAdapter` | PREPARADO — sin motor económico |
| 1220 | `DiagnosticoAdapter` | PREPARADO — sin duplicar diagnóstico |

### UI

- Ruta principal: `/` — Centro de Control ejecutivo
- Secciones: resumen, atención requerida, empleados IA, oportunidades, impacto, FinOps, valor/retorno, diagnóstico, señales, salud plataforma
- Estados controlados: «Sin información disponible» (no ceros engañosos)
- Enlaces a módulos origen en cada tarjeta/fila

---

## Integración futura (sin duplicar código)

1. **1100** — Enlazar cadenas UI oportunidad→ejecución vía enlaces existentes; backend ya expuesto en adaptador oportunidades.
2. **1110** — Extender `FinOpsExtendidoAdapter.fetch()` para consumir endpoints del bloque 1110.
3. **1120** — Completar `SenalesAdapter` con fuentes/errores de ingesta del bloque 1120.
4. **1200** — Desplegar bloque 1200; adaptador detecta `baseline_models` y activa panel impacto automáticamente.
5. **1210** — Implementar `ValorRetornoAdapter.fetch()` con motor de valoración cuando exista.
6. **1220** — Implementar `DiagnosticoAdapter.fetch()` con hallazgos/riesgos del bloque 1220.

---

## Verificación

### Pruebas focales bloque 1230

```
16 passed in 4.39s (SQLite)
```

### Frontend build

```
vite build — PASS (82 modules)
```

---

## SALIDA

```
EMPLEADOS_IA — BLOQUE 1230 TERMINADO

RAMA:
cursor/1230-centro-control-ejecutivo

BASE:
4c03cbe

HEAD:
b285f54

RESUMEN EJECUTIVO:
PASS

ATENCIÓN REQUERIDA:
PASS

EMPLEADOS IA:
PASS

OPORTUNIDADES:
PASS

IMPACTO:
PREPARADO

FINOPS:
PASS

VALOR/RETORNO:
PREPARADO

DIAGNÓSTICO:
PREPARADO

SEÑALES:
PASS

SALUD PLATAFORMA:
PASS

RBAC:
PASS

MULTIEMPRESA:
PASS

API AGREGADORA:
PASS

UI:
PASS

TESTS:
16 passed

FRONTEND:
PASS

P0:
0

P1:
0

VEREDICTO:
APTO

NO MERGE
```

---

## No modificado

- Bloques 1100, 1110, 1120, 1200, 1210, 1220 (código)
- Candidata V1 / PR #32
- PostgreSQL harness, Docker, OpenAI, Ollama, pricing
