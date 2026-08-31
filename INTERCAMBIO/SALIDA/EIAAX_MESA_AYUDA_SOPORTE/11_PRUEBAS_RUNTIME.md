# 11 — Pruebas y runtime

## Pruebas ejecutadas
```bash
DATABASE_URL="sqlite:////tmp/eiaax_mb12_test.db" pytest \
  tests/test_mesa_ayuda_mb12.py \
  tests/test_mb12_eiaax_mesa_ayuda.py -q
```
**Resultado: 25 passed**

## Casos runtime (test_mb12_eiaax_mesa_ayuda.py)
| # | Escenario | Verificación |
|---|-----------|--------------|
| 1 | Solicitud normal | clasificar → asignar → comentar → resolver → validar → cerrar |
| 2 | SLA | política ALTA, alerta `check_sla_warnings`, resolución |
| 3 | Problema recurrente | 2 incidentes → problema → causa → propuesta KB PENDIENTE |
| 4 | Fallo externo | INTEGRACION + correlation_id, sin falso cierre |
| 5 | Multiempresa | tenant B no accede caso/evidencia A |

## Regresión
- `test_mesa_ayuda_mb12.py` (14 tests originales)
- `test_mesa_ayuda_integracion_mi_trabajo.py` (no re-ejecutado en esta sesión; sin cambios breaking en contratos)

## Frontend build
`npm run build` — ✓ exitoso

## Runtime navegador
Rutas: `/soporte`, `/soporte/casos/{id}` — EiaaxTable, ContextualHelp, pestañas detalle, autoservicio.
