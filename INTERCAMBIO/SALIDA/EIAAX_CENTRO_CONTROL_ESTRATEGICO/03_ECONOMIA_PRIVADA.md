# 03 — Economía privada (completa V1)

## Motor reutilizado

`strategic_economy_service.build_economia_privada` compone:

| Fuente | Bloque | Datos |
|--------|--------|-------|
| `commercial_service.proposal_to_detail` | 1280 | Valores por categoría, costos, precio sugerido, ROI, payback, margen |
| `commercial_service.suggest_price` | 1280 | Simulación si falta precio persistido |
| `ValorRetornoAdapter` | 1210 | Valor verificado/estimado/potencial org |
| `TcoAdapter` | 1320 | Inversión, desglose, FinOps IA |
| `FinOpsExtendidoAdapter` | 1110 | Consumo periodo, tokens |
| `Mb07PlanificadorAdapter` | MB-07 | Margen bruto estimado |

## Fórmula precio (Motor Económico 1280)

```
max(valor_atribuible_realizable × fracción, costo_total × (1 + margen_mínimo), precio_base_plan)
```

No es simple `costo + margen`. Considera valor, complejidad (costos), escenarios (riesgo/urgencia), plan (reutilización/soporte).

## Separación POTENCIAL

- `separacion_potencial.potencial_no_realizado: true`
- POTENCIAL excluido de `valor_atribuible_precio` y precio sugerido
- Advertencia explícita en motor comercial

## Permiso

`strategic_control.economia_privada` — sin él: `restringido: true`

Margen detallado adicionalmente requiere `comercial.approve`.

## Privacidad

- No aparece en `vista_entidad`
- `publicacion.economia_privada_publicable: false`
- Prospecto/cliente sin permiso estratégico: 403 en cockpit
