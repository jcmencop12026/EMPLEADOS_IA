# 11 — Pruebas y runtime

## Suites ejecutadas

```bash
python3 -m pytest tests/test_fabrica_mb06_bridge.py \
  tests/test_employee_lifecycle_factory_mb06.py \
  tests/test_arquitecto_transformacion.py -q
# 32 passed
```

```bash
cd frontend && npm run build
# ✓ built
```

## Casos runtime MB-06

| Caso | Test | Resultado |
|------|------|-----------|
| 1 — Arquitecto→Fábrica | `test_caso1_arquitecto_a_fabrica_borrador` | Borrador DRAFT, trazabilidad ARQUITECTO, requerimiento CONSUMIDO |
| 2 — Creación guiada | `test_caso2_creacion_guiada_biblioteca_y_estimacion` | Biblioteca + estimación FinOps |
| 3 — Falla controlada | `test_caso3_falla_controlada_proveedor` | validate-provider=false, publish bloqueado |
| 4 — Multiempresa | `test_caso4_multitenant_empleado_aislamiento` | Tenant B: 403/404, no en biblioteca |
| Clon borrador | `test_clone_como_borrador_no_activa` | PLANTILLA_CLON, DRAFT |
| Gobierno frontera | `test_gobierno_operacional_boundary` | FRONTERA_PREPARADA |

## Cobertura adicional (reutilizada)

- Ciclo vida completo: `test_employee_lifecycle_factory_mb06.py` (19 casos)
- Arquitecto regresión: `test_arquitecto_transformacion.py`
- Multitenant, RBAC, versionado, publicación: incluidos en lifecycle suite

## Migración

`1430a1b2c3d4e` — down_revision `1420a1b2c3d4e` (rama local).

**Nota:** revisiones `1410`/`1420` colisionan con Partners/BP2. GENERAL reconciliará cadena.
