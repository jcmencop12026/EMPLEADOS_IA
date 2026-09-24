# 01 — Reutilización

## Patrón adapter/orquestador

`backend/app/modules/inteligencia_empresarial/` — capa de lectura/orquestación que **delega** a:

- `evaluacion_service`
- `transformacion_service`
- `proactive_service`
- `diagnostic_service`

## Extensiones mínimas en código existente

| Archivo | Cambio |
|---------|--------|
| `transformacion_models.py` | `ESCENARIO_TIPOS` ampliado |
| `transformacion_service._generar_escenarios` | 5 escenarios sin asumir automatización total |
| `evaluaciones.py` | `GET /{id}/suficiencia` delegado |
| `permissions.py` | `inteligencia_empresarial.view/manage` |
| `main.py` | Router registrado |

## Sin migración nueva

Reutiliza tablas 1405, 1420, 1030, 1220, 1240 existentes.
