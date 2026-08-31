# 09 — Pruebas y runtime

## Suite ejecutada

```bash
pytest tests/test_empresa_seguridad_gobierno_datos.py \
       tests/test_gobierno_operacional.py \
       tests/test_bloque_producto_1_evaluacion.py -q
```

**Resultado: 29/29 PASS**

## Cobertura

| Área | Tests |
|------|-------|
| Clasificación alias PUBLICA→PUBLICO | `test_clasificacion_transversal_alias` |
| Visibilidad niveles + versión | `test_visibilidad_niveles_transversal` |
| Evidencia vinculada | `test_evidencia_vinculo` |
| Trazabilidad correlation_id | `test_trazabilidad_por_correlation_id` |
| Auditoría español | `test_auditoria_consulta_espanol` |
| Centro Confianza grupos | `test_centro_confianza_empresarial_grupos` |
| Cross-tenant | `test_cross_tenant_clasificacion_denied` |
| RBAC viewer | `test_viewer_sin_asignar_clasificacion` |
| Exportación | `test_exportar_gobierno` |
| Regresión gobierno op. | `test_regresion_gobierno_operacional` |
| Regresión BP1 | `test_regresion_bp1_visibilidad` |

## Recorrido runtime

1. `POST /api/empresa-seguridad/clasificaciones` — CONFIDENCIAL en documento
2. `POST /api/empresa-seguridad/visibilidad` — VISIBLE_ENTIDAD → RESTRINGIDO
3. `POST /api/empresa-seguridad/evidencias` — vincular knowledge/doc
4. `GET /api/empresa-seguridad/trazabilidad/{correlation_id}`
5. `GET /api/empresa-seguridad/confianza` — grupos IMPLEMENTADO/CONFIGURADO/PENDIENTE
6. `GET /api/empresa-seguridad/exportar`
7. UI `/centro-confianza` y `/auditoria` con filtros español
