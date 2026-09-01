# 07 — Pruebas runtime

## Suite V1

```bash
python3 -m pytest tests/test_centro_estrategico_v1.py -q
```

| Test | Verifica |
|------|----------|
| `test_cockpit_estructura_y_lecturas` | 5 lecturas, mismo_dossier, separación MB-08 |
| `test_lecturas_comparten_dossier` | organization_id y dossier_id estables |
| `test_modo_comite` | modo_comite + lecturas_preview |
| `test_semantica_antes_proyectado_real` | semántica API lecturas |
| `test_economia_privada_restringida_sin_permiso` | privacidad economía |
| `test_multitenant_aislamiento` | tenant |
| `test_sin_permiso_denegado` | RBAC |
| `test_mb08_no_sustituido` | MB-08 sigue con fuerza_laboral |

**Resultado:** 8 passed

## Regresión MB-08

```bash
python3 -m pytest tests/test_centro_control_mb08_operacional.py -q
```

**Resultado:** 6 passed (incluido en corrida conjunta 14 passed)

## Build frontend

```bash
cd frontend && npm run build
```

**Resultado:** ✓ built
