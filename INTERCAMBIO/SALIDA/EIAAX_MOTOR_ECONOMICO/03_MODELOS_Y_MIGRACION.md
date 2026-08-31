# 03 — Modelos y migración

## Migración Alembic

| Campo | Valor |
|---|---|
| Revision | `1600a1b2c3d4e` |
| Archivo | `backend/alembic/versions/1600a1b2c3d4e_motor_economico_eiaax.py` |
| down_revision | `1405a1b2c3d4e` |
| Head resultante | `1600a1b2c3d4e` |

## Tablas nuevas

### `economic_cost_entries`

Registro unificado de costo con `cost_class`, `amount_kind`, `cost_source`, `scope_type`, FK opcional `finops_record_id`.

### `economic_value_entries`

Valor unificado con `value_nature` (VERIFICADO/ESTIMADO/POTENCIAL), FK opcional `finops_value_id`.

### `economic_private_economy`

Economía operador: costos reales/estimados, margen, ROI, payback, riesgo comercial. **No en Vista Entidad.**

### `economic_price_recommendations`

Recomendaciones de precio siempre `BORRADOR` hasta revisión humana.

## Archivos modelo

- `backend/app/economic_motor_enums.py`
- `backend/app/economic_motor_models.py`

## Permisos nuevos (extensión FinOps)

| Permiso | Uso |
|---|---|
| `finops.economy.private` | Economía privada operador |
| `finops.economy.recommend` | Generar precio recomendado (borrador) |

`finops.view` / `finops.manage` cubren Vista Entidad y registro costos/valores.
