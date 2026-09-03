# 06 — Pruebas

## Suite Bloque 1

**Archivo:** `tests/test_bloque_producto_1_evaluacion.py`

| Test | Resultado |
|------|-----------|
| Crear expediente + información adaptativa | PASS |
| Evaluación preliminar genera hallazgos | PASS |
| Visibilidad backend + vista entidad | PASS |
| Multitenant aislamiento (2 orgs) | PASS |
| Preguntar sin proveedor (estado controlado) | PASS |
| RBAC sin permiso (viewer → 403) | PASS |
| E2E recorrido completo | PASS |
| Persistencia servicio | PASS |

**Total:** 8/8 PASS

## Otras validaciones

| Suite | Resultado |
|-------|-----------|
| `test_migration_control.py` | 7/7 PASS |
| `frontend npm run build` | PASS |

## Cómo ejecutar

```bash
python3 -m pytest tests/test_bloque_producto_1_evaluacion.py -v
cd frontend && npm run build
```

## P0/P1/P2 detectados

| ID | Severidad | Estado |
|----|-----------|--------|
| — | P0 | Ninguno abierto |
| Logo oficial EIAAX no disponible en repo | P2 | Documentado; identidad textual mínima |
| Gráficos impacto dinámicos requieren línea base vinculada | P2 | Base tabular implementada |
