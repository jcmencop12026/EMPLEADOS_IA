# CURSOR 1240 — Inteligencia externa y oportunidades estratégicas

**Fecha:** 2026-08-29
**Rama:** `cursor/1240-inteligencia-externa-85e4`
**Base:** `5eaad7e` (bloque 1120)
**HEAD:** _pendiente commit_
**Estado:** **BLOQUE 1240 TERMINADO**
**NO MERGE**

---

## Objetivo

Desarrollar de forma controlada la capacidad **EXTERNA** preparada en 1120 (`EXTERNAL_FUTURE`), convirtiendo:

**FUENTE EXTERNA → EVIDENCIA → SEÑAL → HALLAZGO → OPORTUNIDAD/RIESGO**

sin buscador web genérico, sin scraping, sin datos ficticios como reales.

---

## Arquitectura

```
ExternalSource (catálogo enriquecido)
     │ vincula SignalSource (1120, EXTERNAL_FUTURE)
     ▼
ingest_external_signal()
     ├── signal_ingestion_service.ingest_real_signal() → ProactiveSignal
     ├── ExternalSignalExtension (clasificación, relevancia, hecho/interpretación)
     └── ExternalEvidence (procedencia, dedupe hash)

OrganizationExternalContext → relevancia y umbrales de frescura

Contratos futuros:
  valuation_contract_ref → bloque 1210
  diagnostic_contract_ref → bloque 1220
```

---

## Alcance implementado

### Fuentes externas

Tipos: MERCADO, COMPETENCIA, CLIENTES, REGULACIÓN, TECNOLOGÍA, ECONOMÍA, DEMOGRAFÍA, PROVEEDORES, SOCIOS/ALIADOS, TENDENCIAS, OTRAS.

Canales: API, ARCHIVO, CARGA MANUAL, WEBHOOK/EVENTO, INTEGRACIÓN FUTURA, FUENTE DOCUMENTAL.

Campos: nombre, tipo, URL, sector, país/región, frecuencia, confiabilidad, método ingesta.

### Evidencia y frescura

- `ExternalEvidence` con referencia, fechas, contenido, dedupe
- Frescura: ACTUAL / RECIENTE / DESACTUALIZADA / SIN FECHA VERIFICABLE (umbrales configurables por empresa)

### Señales externas (reutiliza ProactiveSignal 1120)

- `modo_ingesta = REAL`, origen `externo:{code}`
- Clasificación: OPORTUNIDAD, RIESGO, CAMBIO, TENDENCIA, EVENTO, INFORMACIÓN
- Relevancia: RELEVANTE / POSIBLEMENTE RELEVANTE / NO RELEVANTE

### Hecho vs interpretación (obligatorio)

- `hecho_observado` (HECHO OBSERVADO)
- `interpretacion` (INTERPRETACIÓN)
- `hipotesis` (HIPÓTESIS)
- `oportunidad_propuesta` (OPORTUNIDAD PROPUESTA)

### Dominios especializados (JSON estructurado)

- Competencia, regulación, tecnología, clientes/demanda

### Oportunidad y riesgo

- Crear oportunidad vía `process_signal` (motor 1030)
- Registrar riesgo sin forzar oportunidad
- Sin ROI/ingresos inventados

### RBAC

| Permiso | Uso |
|---------|-----|
| `inteligencia_externa.view` | Consultar |
| `inteligencia_externa.manage` | Fuentes, clasificación |
| `inteligencia_externa.ingest` | Ingesta |
| `inteligencia_externa.validate` | Validar análisis |

### API `/api/inteligencia-externa`

- GET/PUT `/contexto`
- GET/POST/PATCH `/fuentes`
- POST `/ingesta`
- GET `/senales`, GET `/senales/{id}`
- PATCH clasificación/relevancia, POST validar/oportunidad/riesgo

### UI (español)

- `/inteligencia-externa` — fuentes y señales con filtros
- `/inteligencia-externa/senales/:id` — detalle con evidencia y capas hecho/interpretación

---

## Archivos

| Archivo | Cambio |
|---------|--------|
| `backend/app/external_intelligence_enums.py` | Enumeraciones |
| `backend/app/external_models.py` | Modelos |
| `backend/app/services/external_intelligence_service.py` | Servicio |
| `backend/app/schemas_external.py` | Schemas |
| `backend/app/routers/inteligencia_externa.py` | API |
| `backend/app/permissions.py` | Permisos |
| `backend/alembic/versions/1240c3d4e5f6a_inteligencia_externa_1240.py` | Migración |
| `frontend/src/pages/InteligenciaExternaPage.tsx` | Lista |
| `frontend/src/pages/InteligenciaExternaDetailPage.tsx` | Detalle |
| `tests/test_inteligencia_externa_1240.py` | 14 pruebas |

---

## Validación

| Prueba | Resultado |
|--------|-----------|
| `pytest tests/test_inteligencia_externa_1240.py` | 14/14 PASS |
| `pytest tests/test_senales_reales_1120.py` | 11/11 PASS (regresión) |
| `npm run build` | PASS |

---

## Restricciones respetadas

- NO rama 1120 modificada
- NO V1 / PR #32
- NO bloques 1110/1200/1210/1220/1230
- NO OpenAI / scraping / datos ficticios como reales

**P0:** 0 | **P1:** 0

---

## Veredicto

```
EMPLEADOS_IA — BLOQUE 1240 TERMINADO

RAMA: cursor/1240-inteligencia-externa-85e4
BASE: 5eaad7e

FUENTES EXTERNAS: PASS
INGESTA: PASS
EVIDENCIA: PASS
FRESCURA: PASS
CLASIFICACIÓN: PASS
RELEVANCIA: PASS
MERCADO: PASS
COMPETENCIA: PASS
REGULACIÓN: PASS
TECNOLOGÍA: PASS
CLIENTES/DEMANDA: PASS
OPORTUNIDAD: PASS
RIESGO: PASS
HECHO VS INTERPRETACIÓN: PASS
DEDUPLICACIÓN: PASS
RBAC: PASS
MULTIEMPRESA: PASS
AUDITORÍA: PASS
UI: PASS

TESTS: 25 passed (14×1240 + 11×1120)
FRONTEND: PASS
ALEMBIC: 1240c3d4e5f6a

P0: 0
P1: 0

VEREDICTO: APTO
NO MERGE
```
