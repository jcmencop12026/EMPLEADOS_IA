# 03 — Economía privada

## Principio

La empresa/prospecto **no recibe automáticamente** costos internos, margen, consumo IA ni precio sugerido.

## Permiso

- `strategic_control.economia_privada` — solo usuarios internos autorizados
- Sin permiso: bloque `economia_privada.restringido = true`

## Contenido interno (lectura financiero)

- Costo periodo / tokens (vía `FinOpsExtendidoAdapter` si `finops.view`)
- Enlace a `/costos-valor`
- Nota: no publicable sin autoridad de publicación

## Publicación a entidad

- Autoridad existente: `evaluacion.visibility` + `evaluacion.vista_entidad`
- `publicacion.economia_privada_publicable: false` en cockpit
- Hallazgos visibles solo con `visible_entidad`

## Prueba

`test_economia_privada_restringida_sin_permiso` — usuario con `strategic_control.view` sin economía privada no ve bloque interno.
