# Pruebas ejecutadas

| Suite | Resultado |
|-------|-----------|
| Regresión Lote 2 + Lote 3 | **170 passed** |
| `test_puesta_en_marcha_journeys` | **8 passed** |
| `test_migration_control` | PASS |
| Frontend `npm run build` | PASS |

## Recorridos API (demo DB)

| Recorrido | Test | Resultado |
|-----------|------|-----------|
| A — Comercial | `test_recorrido_a_*` | PASS |
| B — Transformación | `test_recorrido_b_*` | PASS |
| C — Gobierno | `test_recorrido_c_*` | PASS |
| D — Resultados | `test_recorrido_d_*` | PASS |
| E — Comms/Soporte | `test_recorrido_e_*` | PASS |
| F — Vista entidad | `test_vista_entidad_*` | PASS |
| G — Multiempresa | `test_recorrido_g_*` | PASS |

## SKIP

Journeys demo requieren `DATABASE_URL=sqlite:////workspace/data/eiaax_integrado_demo.db` (8 skipped en regresión sin esa BD).
