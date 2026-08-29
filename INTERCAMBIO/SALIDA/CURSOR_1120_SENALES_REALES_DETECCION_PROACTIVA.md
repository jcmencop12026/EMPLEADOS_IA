# EMPLEADOS_IA — BLOQUE 1120
## Señales reales y detección proactiva (B1.5)

**Rama:** `cursor/1120-senales-reales-deteccion`  
**Base:** `4c03cbe`  
**HEAD:** `ed8dcf97b3c92d4c2d862a1644ec1c80022d8c18`

---

## Objetivo cumplido

Base genérica para recibir y procesar **datos internos reales** de una empresa, conectada al motor de oportunidades 1030, sin conector completo ni análisis externo de mercado.

---

## Componentes implementados

### 1. Fuentes de datos (`SignalSource`)

Abstracción parametrizable por empresa con tipos:

| Código API | Tipo interno |
|------------|--------------|
| `api` | API |
| `base_datos` | DATABASE |
| `archivo` | FILE |
| `evento` | EVENT |
| `automatizacion` | AUTOMATION |
| `integracion_externa` | EXTERNAL_FUTURE |

Tabla `signal_sources`, configuración JSON sanitizada, código único por `organization_id`.

### 2. Señal normalizada (`ProactiveSignal` extendido)

Campos añadidos: `source_id`, `modo_ingesta` (REAL/SINTETICO/PRUEBA), `proceso`, `metrica`, `valor_metrica`, `unidad`, `dimension`, `evidencia_resumen`, `metadata_json`, `estado_procesamiento`, `rejection_reason`, `signal_at`.

### 3. Ingesta controlada

- `POST /api/senales/fuentes` — registrar fuente
- `GET /api/senales/fuentes` — listar fuentes
- `POST /api/senales/ingesta` — ingesta de señal real
- `GET /api/senales` — señales recientes (filtro `modo`)
- `GET /api/senales/{id}/trazabilidad` — trazabilidad completa

Validaciones: empresa activa, permisos RBAC, estructura, duplicados (ventana 24h + `idempotency_key`), metadata sin secretos.

### 4. Detección

`signal_ingestion_service.ingest_real_signal()` → `proactive_service.process_signal()` → oportunidad.

Detección sintética del scheduler marcada con `modo_ingesta=SINTETICO` y `origen=proactive_scheduler_sintetico`.

### 5–8. Trazabilidad, idempotencia, multiempresa, auditoría

- Trazas `OpportunityTrace` + endpoint de trazabilidad
- Deduplicación por `dedupe_key` / `idempotency_key`
- Aislamiento por `organization_id`; empresa inactiva → 403
- Auditoría: `signal.source.created`, `signal.received`, `signal.duplicate`, `signal.processed`, `signal.rejected`, `opportunity.detected`

### 9. Interfaz mínima (español)

- `/senales` — fuentes y señales recientes
- `/senales/:signalId` — trazabilidad y enlace a oportunidad

---

## Archivos principales

| Archivo | Rol |
|---------|-----|
| `backend/app/opportunity_models.py` | Modelos `SignalSource` + campos señal |
| `backend/alembic/versions/1120a1b2c3d4e_senales_reales_deteccion.py` | Migración |
| `backend/app/services/signal_ingestion_service.py` | Lógica ingesta/dedup/auditoría |
| `backend/app/routers/senales.py` | API REST |
| `backend/app/services/proactive_service.py` | `modo_ingesta` en pipeline |
| `backend/app/services/proactive_scheduler.py` | Origen sintético diferenciado |
| `tests/test_senales_reales_1120.py` | 11 pruebas |
| `frontend/src/pages/SenalesPage.tsx` | UI administrativa mínima |

---

## Resultados de pruebas

```
tests/test_senales_reales_1120.py — 11 passed
frontend npm run build — PASS
```

---

## Certificación

| Criterio | Resultado |
|----------|-----------|
| MODELO SEÑALES | PASS |
| INGESTA | PASS |
| DETECCIÓN | PASS |
| SEÑAL→OPORTUNIDAD | PASS |
| DEDUPLICACIÓN | PASS |
| TRAZABILIDAD | PASS |
| MULTIEMPRESA | PASS |
| RBAC | PASS |
| AUDITORÍA | PASS |
| TESTS | 11/11 PASS |
| FRONTEND | PASS |

**VEREDICTO: APTO**

**NO MERGE** — entrega en rama independiente según instrucciones.
