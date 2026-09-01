# EIAAX — Flujo Comercial V1 (Prospecto → Contratación)

## Identificación

| Campo | Valor |
|-------|-------|
| **SHA inicial** | `f0f8cf5` (continuidad 1720) |
| **SHA final** | `0dafb67` |
| **Rama** | `cursor/flujo-comercial-v1-3581` |
| **Base** | `cursor/continuidad-comercial-operacional-3581` |
| **Migración** | `1730a1b2c3d4e` |

## Reutilización (sin reconstruir)

| Módulo | Uso |
|--------|-----|
| **Evaluación 1405** (`EvaluacionExpediente`) | Dossier / expediente |
| **Oportunidades 1030** | Pipeline, clasificación valor |
| **Motor Económico 1600** | Precio privado, POTENCIAL excluido |
| **Centro de Negocios 1700/1710** | Propuesta, contrato, PDF |
| **Inteligencia externa 1240** | Importación a hallazgos |
| **Continuidad 1720** | Post-contrato (sin cambios) |

## Brechas cerradas (1730)

| ID | Brecha | Solución |
|----|--------|----------|
| B-FC01 | Catálogo información universal rígido | Catálogo contextual por sector/problema (ej. salud+glosas) |
| B-FC02 | Sin validación suficiencia pre-propuesta | `GET .../suficiencia` + gate en `generar-propuesta` |
| B-FC03 | Oportunidades sin origen/clasificación presentación | `origen_comercial`, `presentar_cliente`, `clasificacion_valor` |
| B-FC04 | Sin presentación ejecutiva interna | `ComercialPresentacionEjecutiva` |
| B-FC05 | Propuesta sin contenido dossier completo | `generar_propuesta_desde_dossier` enriquece documento cliente |
| B-FC06 | Sin instrumentos contractuales modulares | `ComercialInstrumentoContractual` (NDA, SLA, etc.) |
| B-FC07 | Sin clasificación garantías | `ComercialCompromisoGarantia` (CONTROL/SHARED/EXTERNO) |
| B-FC08 | Inteligencia externa desconectada del dossier | `importar-inteligencia-externa` → hallazgos |
| B-FC09 | Sin recorrido demo orquestado | `POST /demo/recorrido` |

## Modelos nuevos

- `comercial_presentaciones_ejecutivas`
- `comercial_instrumentos_contractuales`
- `comercial_compromisos_garantia`
- Columnas: `evaluaciones_expediente.sector`, `opportunities.origen_comercial`, `opportunities.presentar_cliente`

## API (`/api/flujo-comercial`)

```
POST /demo/recorrido
GET  /expedientes/{id}/catalogo-informacion
POST /expedientes/{id}/sync-informacion
GET  /expedientes/{id}/suficiencia
POST /expedientes/{id}/importar-inteligencia-externa
GET  /expedientes/{id}/oportunidades
POST /expedientes/{id}/oportunidades/seleccion-presentacion
PATCH /oportunidades/{id}/clasificacion
POST /expedientes/{id}/presentacion-ejecutiva
POST /expedientes/{id}/generar-propuesta
GET  /instrumentos/catalogo
GET|POST /propuestas/{id}/instrumentos
GET|POST /propuestas/{id}/compromisos-garantia
```

## Permisos

- `flujo_comercial.view`
- `flujo_comercial.manage`

## Tests

`tests/test_flujo_comercial_v1_1730.py` — **5 passed**

Cubre: catálogo contextual salud, propuesta dossier, instrumentos/garantías, POTENCIAL≠realizado, demo recorrido.

## Frontend

- `EvaluacionConsolePage`: sincronizar info contextual + generar propuesta → Centro de Negocios
- `npm run build` OK

## Recorrido funcional

1. **Demo:** `POST /flujo-comercial/demo/recorrido`
2. **Manual:** evaluación → sync contextual → evaluar → oportunidades → selección → presentación → generar propuesta → instrumentos → contratar (CN existente)

## Priorización

- **P0:** Catálogo contextual, propuesta desde dossier, clasificación POTENCIAL
- **P1:** Presentación ejecutiva, instrumentos modulares, garantías
- **P2:** Demo recorrido, UI expediente, import inteligencia externa

## Pendiente GENERAL

- Portal cliente / e-sign
- Plantillas jurídicas completas por sector
- Wizard UI guiado único (hoy orquestación API + consola evaluación)
- Gobierno Operacional aprobaciones (B14)

## NO hecho (explícito)

- NO Windows / PIIAX
- NO nuevo Centro de Negocios
- NO CRM prospecto separado (`entidad_nombre` en expediente)
- NO software jurídico gigante
