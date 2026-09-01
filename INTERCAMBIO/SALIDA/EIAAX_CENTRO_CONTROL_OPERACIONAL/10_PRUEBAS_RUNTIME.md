# 10 — Pruebas y runtime

## Suites

```bash
python3 -m pytest tests/test_centro_control_mb08_operacional.py \
  tests/test_centro_control_tramo6e.py \
  tests/test_fabrica_mb06_bridge.py \
  tests/test_arquitecto_transformacion.py -q
# 26 passed
cd frontend && npm run build  # OK
```

## Casos runtime MB-08

| Caso | Test | Resultado |
|------|------|-----------|
| 1 Operación normal | `test_caso1_operacion_normal_empleado_y_ejecucion` | Empleado visible en fuerza laboral |
| 2 Error | `test_caso2_error_en_atencion` | Fallida en atención + detalle |
| 4 Aprobación | `test_caso4_aprobacion_pendiente_en_centro` | Bloque aprobaciones |
| 6 Multiempresa | `test_caso6_multitenant_operacional` | Aislamiento estricto |

## Migraciones

**Ninguna nueva** — MB-08 es capa de lectura sobre esquema existente (1410/1420/1430 heredados).
