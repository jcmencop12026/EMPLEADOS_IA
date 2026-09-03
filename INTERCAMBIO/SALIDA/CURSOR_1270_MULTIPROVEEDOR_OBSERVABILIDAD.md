# EMPLEADOS_IA — BLOQUE 1270 MULTIPROVEEDOR Y OBSERVABILIDAD

## Base verificada

| Campo | Valor |
|-------|-------|
| Rama base | `cursor/1210-valoracion-economica-roi-85e4` |
| SHA base | `076bca6` |
| Justificación | Post-V1 con FinOps 1110 integrado, sin convergencias 1230/1250 |

## Rama entregada

`cursor/1270-multiproveedor-observabilidad-9a85`

## Arquitectura

```
PLATAFORMA → GATEWAY IA → CATÁLOGO → ADAPTADORES → MODELOS → EMPLEADOS IA
```

Contrato común en `BaseLlmAdapter`:
- `complete` / `validate_credentials` / `health`
- `list_models` / `capabilities` / `usage` / `normalize_error`

## Proveedores

| Proveedor | Estado |
|-----------|--------|
| OpenAI | Operativo (sin ruptura V1) |
| Anthropic | Preparado — HTTP adapter, `NO CONFIGURADO` sin credencial |
| Gemini | Preparado — HTTP adapter |
| Azure OpenAI | Preparado — endpoint + deployment requeridos |
| Ollama | Opcional preservado |

## Componentes nuevos

- Adaptadores: `anthropic_adapter.py`, `gemini_adapter.py`, `azure_openai_adapter.py`
- Modelos: `LlmModelCatalog`, `LlmRoutingPolicy`
- Servicios: `llm_routing_service`, `llm_observability_service`, `llm_health_service`
- Migración: `1270a1b2c3d4e`
- API: `/api/llm/observability`, `/health`, `/routing/*`, `/models`
- UI: `AdminLlmProvidersPage` con pestañas Proveedores / Salud / Consumo / Enrutamiento

## FinOps

- Registro por inferencia preservado vía `registrar_consumo`
- Costo sincronizado en `LlmInferenceLog` cuando FinOps calcula tarifa
- Sin inventar costos si proveedor no reporta/configura tarifa

## Pruebas

- `tests/test_bloque_1270_multiproveedor.py` — 16 tests
- Regresión `test_llm_gateway_v1.py` — PASS
- Frontend `npm run build` — PASS

## Salida estándar

```
EMPLEADOS IA — BLOQUE 1270 TERMINADO

RAMA: cursor/1270-multiproveedor-observabilidad-9a85
BASE: 076bca6
HEAD: <SHA>

OPENAI: PASS
ANTHROPIC: PREPARADO
GEMINI: PREPARADO
AZURE OPENAI: PREPARADO
OLLAMA OPCIONAL: PASS
CATÁLOGO: PASS
ENRUTAMIENTO: PASS
FALLBACK: PASS
FINOPS: PASS
OBSERVABILIDAD: PASS
SALUD: PASS
ERRORES NORMALIZADOS: PASS
CREDENCIALES: PASS
RBAC: PASS
MULTIEMPRESA: PASS
UI: PASS
TESTS: 33 passed (1270 + gateway v1 focal)
FRONTEND: PASS
P0: 0
P1: 0
P2: 0
VEREDICTO: APTO
NO MERGE
```
