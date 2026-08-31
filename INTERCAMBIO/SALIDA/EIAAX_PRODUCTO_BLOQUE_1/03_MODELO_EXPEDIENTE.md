# 03 — Modelo expediente

## Tablas (migración `1405a1b2c3d4e`)

### `evaluaciones_expediente`
Contenedor principal: entidad, necesidad, objetivo, estado, nivel, confianza, % información, vínculos a diagnóstico/oportunidades, notas internas.

### `evaluaciones_informacion`
Requisitos adaptativos por nivel (PRELIMINAR / DIAGNÓSTICA / PROFUNDA).

### `evaluaciones_hallazgos`
Hallazgos con tipo HECHO/INFERENCIA/PROYECCIÓN, confianza ALTA/MEDIA/BAJA, evidencia, `visible_entidad`.

### `evaluaciones_oportunidad_links`
Vínculo expediente ↔ oportunidad existente.

### `evaluaciones_visibilidad_log`
Auditoría: quién, cuándo, objeto, visible_entidad.

## Estados expediente

`BORRADOR`, `EN_CURSO`, `PRELIMINAR`, `DIAGNOSTICA`, `PROFUNDA`, `CERRADO`, `ARCHIVADO`

## API principal

| Método | Ruta | Permiso |
|--------|------|---------|
| GET | `/api/evaluaciones` | evaluacion.view |
| POST | `/api/evaluaciones` | evaluacion.manage |
| GET/PATCH | `/api/evaluaciones/{id}` | view/manage |
| PATCH | `.../informacion/{item_id}` | evaluacion.manage |
| POST | `.../evaluar` | evaluacion.evaluate |
| POST | `.../visibilidad` | evaluacion.visibility |
| GET | `.../vista-entidad` | evaluacion.vista_entidad |
| GET | `.../impacto`, `.../trazabilidad` | evaluacion.view |
| POST | `.../oportunidades/crear` | evaluacion.manage |
| POST | `.../preguntar` | evaluacion.view |
