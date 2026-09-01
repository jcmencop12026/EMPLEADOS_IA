# 02 — Modelo de lecturas (mismo dossier)

## Cinco lecturas sobre una fuente

| ID | Audiencia | Contenido |
|----|-----------|-----------|
| `resumen` | Todos | Etapa, entidad, completitud, confianza, alternativas |
| `gerencia` | Dirección | Valor, riesgos, prioridades, oportunidades, impacto |
| `operacion` | Operaciones | Cuellos de botella, automatización, impacto — enlace MB-08 |
| `sistemas` | TI | Integraciones, gobierno, continuidad (alto nivel) |
| `financiero` | Finanzas | Valoración, comercial, TCO, economía privada |

## Modo comité

- Parámetro `modo_comite=true` en API
- Checkbox en UI
- Permite recorrer lecturas sin duplicar datos — `lecturas_preview` apunta al mismo dossier

## API

```
GET /api/centro-estrategico/cockpit?lectura=gerencia&modo_comite=false
GET /api/centro-estrategico/lecturas
```

## Campos de respuesta clave

- `mismo_dossier: true`
- `dossier_id` estable (solo lectura, sin crear filas)
- `organization_id` tenant
- `contenido` según lectura activa
- `trazabilidad.cadena_ejecutiva`
- `vista_entidad` si `evaluacion.vista_entidad`
- `separacion_mb08` documenta frontera operacional
