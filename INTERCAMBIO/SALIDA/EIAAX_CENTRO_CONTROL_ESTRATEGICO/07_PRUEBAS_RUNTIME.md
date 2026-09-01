# 07 — Pruebas runtime

## Suite V1 (continuación)

```bash
python3 -m pytest tests/test_centro_estrategico_v1.py -q
```

**18 passed** — cubre:

| Área | Tests |
|------|-------|
| 5 lecturas misma fuente | `test_cinco_lecturas_misma_fuente` |
| Economía privada autorizada | `test_economia_privada_completa_autorizada` |
| Economía denegada | `test_economia_privada_denegada` |
| POTENCIAL ≠ realizado | `test_potencial_no_como_realizado` |
| Precio sugerido motor 1280 | `test_precio_sugerido_no_es_costo_mas_margen_simple` |
| Privacidad vista entidad | `test_vista_entidad_sin_economia_privada` |
| Prospecto/cliente | `test_prospecto_*`, `test_cliente_*` |
| Tenant cruzado | `test_tenant_cruzado_economia` |
| Persistencia dossier | `test_persistencia_dossier_escritura` |
| Sin duplicar dossier | `test_escritura_sin_duplicar_dossier` |
| Trazabilidad audit | `test_trazabilidad_decision_audit` |
| MB-08 intacto | `test_mb08_intacto` |
| ContinuidadAdapter | `test_continuidad_adapter_degradados_lista` |
| Gráficos semántica | `test_graficos_no_mezclan_proyectado_real` |

## Regresión MB-08

```bash
python3 -m pytest tests/test_centro_control_mb08_operacional.py -q
```

**6 passed** — total conjunto: **24 passed**

## Build frontend

```bash
cd frontend && npm run build
```

**PASS**
