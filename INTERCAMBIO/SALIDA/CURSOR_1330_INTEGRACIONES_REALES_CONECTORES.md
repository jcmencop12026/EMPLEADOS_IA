# EMPLEADOS_IA — BLOQUE 1330
## Integraciones reales + conectores empresariales

**Rama:** `cursor/1330-integraciones-reales-conectores`
**Base:** `origin/cursor/1120-senales-reales-deteccion` @ `5eaad7e4e605465a6ba4145b03c7ec043a5f62b4`
**Justificación base:** Rama POST-V1 estable con motor 1120 (`ProactiveSignal`, `ingest_real_signal`) y orquestación/automatizaciones, sin arrastrar convergencias de bloques prohibidos (1250–1320, 1280, 1310).

---

## Objetivo cumplido

Capa reutilizable de integraciones empresariales parametrizables para conectar EMPLEADOS_IA con fuentes externas (API, BD, archivos, SFTP, webhooks, correo, eventos) y alimentar señales, automatizaciones, conocimiento y procesos sin integración rígida por cliente.

---

## Componentes implementados

### Catálogo y modelos

- Tipos: API REST, Base de datos, Archivo, SFTP, Webhook, Correo, Evento (extensible vía `ConnectorType.ALL`)
- Estados en español: BORRADOR, CONFIGURANDO, VALIDANDO, ACTIVO, DEGRADADO, ERROR, INACTIVO
- Tablas: `integration_connectors`, `integration_executions`, `integration_webhook_events`
- Migración Alembic: `1330a1b2c3d4e` (down: `1120a1b2c3d4e`)

### API REST (`/api/integraciones`)

| Endpoint | Descripción |
|----------|-------------|
| `GET /catalogo` | Catálogo de tipos |
| `GET/POST /conectores` | Listar / crear |
| `GET/PUT /conectores/{id}` | Detalle / configurar |
| `POST /conectores/{id}/probar` | Probar conexión |
| `POST /conectores/{id}/ejecutar` | Ejecutar (manual) |
| `GET /conectores/{id}/ejecuciones` | Historial |
| `GET /conectores/{id}/salud` | Salud y métricas |
| `POST /webhook/{id}` | Webhook entrante con token y deduplicación |

### Seguridad

- SSRF: bloqueo de localhost, metadata cloud (`169.254.169.254`), redes privadas sin `allow_internal_urls`
- Secretos vía `secret_ref` (env) — UI/auditoría: CONFIGURADO / NO CONFIGURADO
- RBAC: `integraciones.view|create|configure|test|execute|manage_secrets`
- Multiempresa estricto por `organization_id`
- Auditoría sin secretos en `detail`

### Ejecutores (modo simulación en tests — sin llamadas externas reales)

- REST: GET/POST/PUT/PATCH/DELETE, mock_response, validación URL
- BD: consultas parametrizadas (`query_id` + allowlist)
- Archivo: CSV, JSON, TXT
- SFTP: list/download/upload mock
- Webhook entrante/saliente
- Correo IMAP/SMTP preparado
- Eventos internos/externos

### Resiliencia

- Reintentos configurables (`retry_max`, backoff lineal)
- Circuit breaker (`circuit_breaker_threshold`, cooldown, estado DEGRADADO)
- Idempotencia en ejecuciones y webhooks (`dedupe_key`)

### Integración 1120

- Destino `SENALES` → `signal_ingestion_service.ingest_real_signal()` con `modo_ingesta=REAL`
- Sin duplicar motor 1120

### Frontend (español)

- `/integraciones` — listado y catálogo
- `/integraciones/nueva` — asistente 7 pasos
- `/integraciones/:id` — configuración, mapeo, ejecuciones, salud

---

## Archivos principales

| Archivo | Rol |
|---------|-----|
| `backend/app/integration_enums.py` | Tipos, estados, errores |
| `backend/app/integration_models.py` | Modelos SQLAlchemy |
| `backend/app/integration_security.py` | SSRF y redacción |
| `backend/app/services/integration_executors.py` | Ejecutores mock/simulación |
| `backend/app/services/integration_service.py` | CRUD, prueba, ejecución, 1120 |
| `backend/app/routers/integraciones.py` | API REST |
| `backend/alembic/versions/1330a1b2c3d4e_*.py` | Migración |
| `tests/test_integraciones_1330.py` | 14 pruebas |
| `frontend/src/pages/IntegracionesPage.tsx` | UI listado |
| `frontend/src/pages/IntegracionWizardPage.tsx` | Asistente |
| `frontend/src/pages/IntegracionDetailPage.tsx` | Detalle |

---

## Resultados de pruebas

```
tests/test_integraciones_1330.py — 14 passed
tests/test_migration_control.py — passed
tests/test_senales_reales_1120.py — 17 passed
Total regresión bloque — 32 passed
frontend npm run build — PASS
```

---

## Certificación

| Criterio | Resultado |
|----------|-----------|
| CATÁLOGO | PASS |
| API REST | PASS |
| BASE DE DATOS | PASS |
| ARCHIVOS | PASS (CSV/JSON/TXT; XLSX no requerido) |
| SFTP | PASS |
| WEBHOOK | PASS |
| CORREO | PASS |
| EVENTOS | PASS |
| MAPEO | PASS |
| VALIDACIÓN | PASS |
| PRUEBA CONEXIÓN | PASS |
| SALUD | PASS |
| REINTENTOS | PASS |
| CIRCUIT BREAKER | PASS |
| IDEMPOTENCIA | PASS |
| 1120 | PASS |
| SSRF | PASS |
| SECRETOS | PASS |
| RBAC | PASS |
| MULTIEMPRESA | PASS |
| AUDITORÍA | PASS |
| OBSERVABILIDAD | PASS |
| UI EN ESPAÑOL | PASS |
| ALEMBIC | PASS |
| ALEMBIC HEAD | `1330a1b2c3d4e` |
| FRONTEND | PASS |

**P0:** 0
**P1:** 0
**P2:** 0

**VEREDICTO:** APTO

**NO MERGE.**
