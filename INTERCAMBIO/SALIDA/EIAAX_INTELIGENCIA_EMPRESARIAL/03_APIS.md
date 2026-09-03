# 03 — APIs

## Prefijo `/api/inteligencia-empresarial`

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/contratos` | view |
| GET | `/panorama` | view |
| GET | `/expedientes/{id}/panorama` | view |
| GET | `/expedientes/{id}/suficiencia` | view |
| GET | `/expedientes/{id}/plan-adaptativo` | view |
| POST | `/expedientes/{id}/evaluar-adaptativo` | manage |
| GET | `/expedientes/{id}/cadena-analitica` | view |
| GET | `/oportunidades/{id}/panorama` | view |
| POST | `/evidencia` | manage |

## Delegado evaluaciones

`GET /api/evaluaciones/{id}/suficiencia` — misma lógica unificada.
