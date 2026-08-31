# 01 — Contrato → Implementación (B01)

## Objetivo

Corregir la conversión contrato→proyecto para transferir el compromiso real contratado, no solo alcance genérico.

## Implementación

- **Servicio:** `backend/app/services/negocio_service.py` → `convert_to_implementacion`
- **Enriquecimiento:** `backend/app/services/continuidad_comercial_service.py` → `enrich_proyecto_from_contrato` vía `continuidad_comercial_service.build_compromiso_contractual_snapshot`
- **Endpoint:** `POST /api/centro-negocios/propuestas/{proposal_id}/convertir-implementacion` (body opcional `condiciones`)

## Qué se referencia vs snapshot

| Elemento | Estrategia |
|----------|------------|
| `proposal_id`, `opportunity_id`, `evaluacion_id`, `contract_id` | Referencia canónica en columnas FK |
| Versión contratada, documento PDF | Referencia + `version_contratada`, `documento_contrato_id` |
| Precio/modalidad/condiciones/alcance/indicadores | Snapshot inmutable en `compromiso_contractual_json` |
| Objetos completos de propuesta | No duplicados; solo IDs + snapshot contractual |

## Columnas nuevas en `impl_proyectos`

- `opportunity_id`, `evaluacion_id`, `contract_id`
- `version_contratada`, `documento_contrato_id`
- `compromiso_contractual_json`, `finops_budget_id`

## Brecha cerrada

**B01** — Conversión con compromiso contractual y referencias canónicas.
