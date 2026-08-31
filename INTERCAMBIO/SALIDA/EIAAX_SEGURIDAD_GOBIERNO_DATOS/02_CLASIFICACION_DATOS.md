# 02 — Clasificación de información

## Modelo conceptual

| Concepto | Código persistido | Alias aceptados |
|----------|-------------------|-----------------|
| Pública | `PUBLICO` | `PUBLICA` |
| Interna | `INTERNO` | `INTERNA` |
| Confidencial | `CONFIDENCIAL` | `CONFIDENCIAL` |
| Restringida | `RESTRINGIDO` | `RESTRINGIDA` |

## Implementación

- **Fuente canónica:** `gov_classification_levels` (bloque 1350) vía `ensure_org_defaults`
- **Asignación transversal:** tabla `empresa_objeto_clasificacion`
- **Tipos soportados:** documento, evidencia, informe, resultado, dato, artefacto, salida_ia, hallazgo, indicador, catalogo

## API

```
GET  /api/empresa-seguridad/clasificaciones/niveles
POST /api/empresa-seguridad/clasificaciones
GET  /api/empresa-seguridad/clasificaciones
GET  /api/empresa-seguridad/clasificaciones/{tipo}/{id}
```

## Permisos

- `gobierno.clasificacion.view`
- `gobierno.clasificacion.assign`

## Backend como autoridad

La clasificación se valida en servidor contra niveles existentes; el frontend no decide sensibilidad.
