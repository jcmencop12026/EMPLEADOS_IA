# 09 — Pruebas Bloque Producto 2

## Ejecución

```bash
python3 -m pytest tests/test_bloque_producto_2_piiax_prep.py -v
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py -v
python3 -m pytest tests/test_migration_control.py -q
cd frontend && npm run build
```

## Resultado (cierre BP2)

| Suite | Resultado |
|-------|-----------|
| BP2 (`test_bloque_producto_2_piiax_prep.py`) | 10/10 PASS |
| BP1 regresión | 8/8 PASS |
| Migraciones | 7/7 PASS |
| Frontend build | PASS |

## Casos BP2 cubiertos

1. Catálogo capacidades
2. PIIAX no conectado (estado controlado)
3. Acción externa → `PIIAX_NO_DISPONIBLE`
4. Aprobación tipo EJECUCIÓN
5. Resultado compatible posterior
6. Indicadores impacto + resumen
7. Clasificación intención
8. Preguntar con intención
9. Trazabilidad con acciones
10. Multitenant aislamiento acciones

## Recorrido E2E representativo

Expediente → hallazgo → solicitar `consultar_datos` → aprobación → estado PIIAX → registrar resultado → ver trazabilidad e impacto.

RBAC: permisos `evaluacion.accion.request`, `evaluacion.accion.approve`, `evaluacion.indicadores.manage`.
