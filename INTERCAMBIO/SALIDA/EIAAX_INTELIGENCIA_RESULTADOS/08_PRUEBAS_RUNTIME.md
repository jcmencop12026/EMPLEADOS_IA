# 08 — Pruebas y runtime

## Pruebas backend

Archivo: `tests/test_bloque_inteligencia_resultados.py` (10 casos)

| Caso | Verificación |
|------|----------------|
| Crear indicador APR | ANTES/PROY sin REAL |
| Medición REAL | Permiso validate |
| REAL < PROYECTADO | No maquilla |
| Sync línea base | Puente 1200 |
| Drill-down | Dimensiones |
| Informe narrativo | Versiones 1 y 2 |
| Trazabilidad | Cadena completa |
| Multitenant | Org B no ve Org A |
| Impacto evaluación | Integración 1405 |
| Recorrido demo | Servicio end-to-end |

**Ejecución (BD migrada):**

```bash
cd /workspace/backend && alembic upgrade head  # con DATABASE_URL
DATABASE_URL=sqlite:////tmp/ir_test.db python -m pytest tests/test_bloque_inteligencia_resultados.py -q
```

Resultado: **10 passed**

## Frontend

- `npm run build` — PASS

## Runtime verificado

| Servicio | URL |
|----------|-----|
| Backend | `http://127.0.0.1:8011` |
| Frontend | `http://127.0.0.1:5186` |
| BD demo | `/tmp/ir-runtime/data/ir.db` |

Login: `admin` / `Admin2026*`

Semilla: `python scripts/inteligencia-resultados-demo.py`

## Capturas

- `ir_hub_indicadores.png`
- `ir_informe_narrativo.png`
- `ir_eval_impacto_link.png`

Ruta: `/opt/cursor/artifacts/screenshots/`
