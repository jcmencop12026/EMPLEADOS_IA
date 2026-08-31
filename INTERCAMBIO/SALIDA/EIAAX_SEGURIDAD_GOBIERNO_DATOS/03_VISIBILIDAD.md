# 03 — Visibilidad transversal

## Niveles

| Nivel | Descripción |
|-------|-------------|
| `INTERNO_EIAAX` | Solo uso interno EIAAX |
| `VISIBLE_ENTIDAD` | Visible para la entidad evaluada |
| `COMPARTIDO_ESPECIFICO` | Compartido con destinatario específico |
| `RESTRINGIDO` | Acceso restringido |

## Registro de cambios

Tabla `gobierno_visibilidad_log` extendida (migración `1420a1b2c3d4e`):

- `nivel_visibilidad`
- `estado_anterior`
- `motivo`
- `version`

## Compatibilidad BP1

`evaluacion_service.set_visibilidad` mantiene `EvaluacionVisibilidadLog` + dual-write a gobierno con nivel automático (`VISIBLE_ENTIDAD` / `INTERNO_EIAAX`).

## API

```
POST /api/empresa-seguridad/visibilidad
GET  /api/gobierno-operacional/visibilidad  (legacy, enriquecido)
```
