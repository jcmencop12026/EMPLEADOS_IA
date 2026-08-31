# 11 — Pruebas y runtime

## Suite automatizada

Archivo: `tests/test_continuidad_comercial_1720.py` (9 tests)

| Test | Cobertura |
|------|-----------|
| `test_conversion_persiste_compromiso_y_referencias` | B01, referencias, snapshot |
| `test_entregables_y_subentidades` | B04, B05, tareas/bloqueadores |
| `test_vista_continuidad_compromiso_resultado` | B09 |
| `test_finops_budget_desde_contrato` | B06 |
| `test_cambio_alcance_flujo` | B10 |
| `test_renovacion_crea_oportunidad` | B07-B08 |
| `test_offboarding_cierre_contrato` | B16 |
| `test_multiempresa_aislamiento` | RBAC multi-tenant |
| `test_privacidad_economia_no_en_vista_cliente` | Economía privada |

**Regresión:** + `test_centro_negocios_1710.py` + `test_implementacion_1340.py` = **37 passed**

## Recorrido runtime 1 — Flujo comercial completo

1. POST `/api/evaluaciones`
2. POST `/api/oportunidades/pipeline-proactivo`
3. POST `/api/centro-negocios/propuestas/desde-expediente`
4. PUT ia-consumo → transición APROBADA → precio → ENVIADA → PDF
5. POST contratar / convertir-implementacion
6. Verificar proyecto con compromiso + referencias
7. POST entregables, hitos, piloto, go-live
8. GET vista continuidad
9. POST renovación con oportunidad

## Recorrido runtime 2 — Cambio de alcance

1. Contrato activo + proyecto
2. POST cambios-alcance
3. POST avanzar (analizar → impacto → decidir → implementar)
4. Verificar versión comercial si aplica

## Recorrido runtime 3 — Offboarding

1. POST cierre contractual
2. POST confirmar
3. Verificar histórico preservado (contrato, proyecto, auditoría)

## Frontend build

```
cd frontend && npm run build  # OK
```
