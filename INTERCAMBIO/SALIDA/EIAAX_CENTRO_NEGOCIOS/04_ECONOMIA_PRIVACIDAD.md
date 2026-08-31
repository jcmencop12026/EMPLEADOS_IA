# 04 — Economía y privacidad

## Motor Económico reutilizado

- `recommend_price()` — siempre **BORRADOR**, `auto_published: false`
- `sum_values_by_nature()` — dashboard separa realizado vs potencial
- `get_private_economy()` — costos/horas/margen internos por organización

## Decisión humana de precio

`POST /api/centro-negocios/propuestas/{id}/precio`

| Acción | Comportamiento |
|--------|----------------|
| `ACEPTAR` | Aplica precio recomendado del motor |
| `MODIFICAR` | Usuario define `precio_decidido` |
| `DESCARTAR` | Registra decisión sin aplicar precio |

Cada decisión persiste en `negocio_price_decisions`.

## Clasificación VERIFICADO / ESTIMADO / POTENCIAL

Heredada del Motor Económico y modelo comercial 1280:

> **POTENCIAL** puede mostrarse como oportunidad potencial; **NO** cuenta como beneficio realizado ni en ROI/payback realizado.

## Separación backend

| Interno EIAAX | Compartible con cliente |
|---------------|-------------------------|
| `margen_pct`, `costo_total`, `precio_sugerido` | `precio_final` autorizado |
| `documento_interno_json` | `documento_cliente_json` |
| Economía privada org | Nunca auto-publicada |

`get_proposal_negocio(include_internal=False)` elimina campos sensibles en API.
