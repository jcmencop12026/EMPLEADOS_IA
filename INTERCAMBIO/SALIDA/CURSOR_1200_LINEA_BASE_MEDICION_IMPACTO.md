# EMPLEADOS_IA — BLOQUE 1200 — LÍNEA BASE Y MEDICIÓN ANTES/DESPUÉS

**Agente:** D
**Base:** `4c03cbe`
**Rama:** `cursor/1200-linea-base-impacto`
**Alcance:** B2.1 línea base → intervención → medición → comparación → impacto real
**Restricción:** Sin tocar bloque 1100, V1, PR #32, ROI, pricing, FinOps 1110, señales 1120

---

## Objetivo cumplido

Modelo transversal reutilizable para demostrar con datos cuánto cambió una situación después de una acción, automatización, Empleado IA, plan u oportunidad — con comparación determinística, dirección de indicador parametrizable, distinción impacto esperado/real y atribución manual (sin IA generativa ni causalidad automática).

---

## Arquitectura implementada

```
OPORTUNIDAD (referencia opcional)
    ↓
LÍNEA BASE (valor base + periodo + dirección indicador)
    ↓
ACCIÓN / INTERVENCIÓN (referencias opcionales: plan, empleado IA, proceso)
    ↓
MEDICIÓN POSTERIOR (múltiples, con evidencia)
    ↓
COMPARACIÓN DETERMINÍSTICA (variación absoluta / % / mejora-deterioro)
    ↓
IMPACTO (esperado vs real vs cambio observado vs valor atribuido)
```

---

## Componentes

### Modelos (`backend/app/baseline_models.py`)

| Entidad | Propósito |
|---------|-----------|
| `LineaBase` | Línea base con indicador, valor base, periodo, fuente, dirección, impacto esperado, referencias |
| `LineaBaseMedicion` | Mediciones posteriores múltiples |
| `LineaBaseImpacto` | Instantánea de comparación (congelada al validar) |
| `LineaBaseHistorial` | Trazabilidad de cambios |

### Servicio (`backend/app/services/baseline_service.py`)

- Cálculo determinístico: `calculate_variation`, `evaluate_direction`
- Direcciones: `MAYOR_ES_MEJOR`, `MENOR_ES_MEJOR`, `INFORMATIVO`
- Tipos impacto: `IMPACTO_ESPERADO`, `IMPACTO_REAL`, `CAMBIO_OBSERVADO`, `VALOR_ATRIBUIDO`
- Atribución: `NO_ATRIBUIBLE`, `PARCIALMENTE_ATRIBUIBLE`, `ATRIBUIBLE` (manual, sin IA)
- Historial inmutable tras validación

### API (`backend/app/routers/linea_base.py`)

| Endpoint | Permiso |
|----------|---------|
| `GET/POST /api/lineas-base` | view / manage |
| `GET/PATCH /api/lineas-base/{id}` | view / manage |
| `POST .../mediciones` | manage |
| `POST .../mediciones/{id}/validar` | validate |
| `PATCH .../mediciones/{id}/atribucion` | validate |
| `GET /api/lineas-base/oportunidad/{id}` | view |

### Permisos RBAC

- `linea_base.view` — consultar
- `linea_base.manage` — crear línea base y registrar mediciones
- `linea_base.validate` — validar impacto y atribución

### UI

- `/lineas-base` — listado, filtros, creación
- `/lineas-base/:id` — detalle, mediciones, comparación, evolución, historial, validación y atribución

### Migración

- `1200a1b2c3d4e_linea_base_medicion_impacto_1200.py`
- Ledger actualizado: `baseline_head = 1200a1b2c3d4e`

---

## Verificación

### Pruebas focales bloque 1200

```
14 passed in 10.22s
```

### Regresión 1030 + 1200

```
52 passed in 33.48s
```

### Frontend build

```
vite build — PASS (84 modules)
```

---

## SALIDA

```
EMPLEADOS_IA — BLOQUE 1200 TERMINADO

RAMA:
cursor/1200-linea-base-impacto

BASE:
4c03cbe

HEAD:
<SHA>

LÍNEA BASE:
PASS

MEDICIONES:
PASS

ANTES/DESPUÉS:
PASS

VARIACIÓN:
PASS

DIRECCIÓN INDICADOR:
PASS

IMPACTO ESPERADO/REAL:
PASS

ATRIBUCIÓN:
PASS

OPORTUNIDAD↔IMPACTO:
PASS

HISTÓRICO:
PASS

RBAC:
PASS

MULTIEMPRESA:
PASS

AUDITORÍA:
PASS

UI:
PASS

TESTS:
52 passed (1200 + 1030)

FRONTEND:
PASS

VEREDICTO:
APTO

NO MERGE
```

---

## No modificado

- Bloque 1100 / candidata V1 / PR #32
- PostgreSQL harness, scheduler R2, Docker, OpenAI, Ollama
- FinOps 1110, señales 1120, ROI completo, pricing, Centro de Control
