# 07 — Visibilidad y trazabilidad

## Visibilidad

- Indicadores: flag `visible_entidad` (patrón BP1)
- Informes: `visibilidad` INTERNO vs VISIBLE_ENTIDAD
- Backend es autoridad — no expone notas internas en vista entidad

## Trazabilidad

`GET /api/resultados/expediente/{expediente_id}/trazabilidad`

Cadena: expediente → indicadores → informes → acciones, con `correlation_id` del expediente.

## Evidencias

`POST /api/resultados/evidencias` — vincula título, fuente, referencia a indicador o informe.

## Integración futura

- Gobierno transversal (rama A): puntos en `correlation_id` y permisos existentes
- Motor económico (rama B): consumir `valor_economico_tipo` de línea base sin duplicar ROI
