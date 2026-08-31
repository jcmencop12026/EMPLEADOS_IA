# 07 — Cambios de alcance (B10)

## Modelo

`ContinuidadCambioAlcance` — flujo:

```
SOLICITADO → EN_ANALISIS → IMPACTO_EVALUADO → DECIDIDO/APROBADO/RECHAZADO → IMPLEMENTANDO → CERRADO
```

## API

```
POST /api/continuidad-comercial/cambios-alcance
POST /api/continuidad-comercial/cambios-alcance/{id}/avanzar
GET  /api/continuidad-comercial/propuestas/{id}/cambios-alcance
```

Acciones `avanzar`: `analizar`, `impacto`, `decidir`, `implementar`, `cerrar`

## Impacto

`impacto_json` soporta alcance, tiempo, costo/precio, dependencias, riesgos (estructura libre JSON).

## Integración comercial

Al `implementar` con `crear_version_comercial: true`:

- Nueva versión vía `create_version_snapshot` (Centro de Negocios)
- Entrada de negociación vinculada

No se creó otro Centro de Negocios.

## Brecha cerrada

**B10** — Solicitud→análisis→impacto→decisión→versión→implementación.
