# 02 — Arquitectura intención / capacidad

## Principio EIAAX ↔ PIIAX

| EIAAX | PIIAX |
|-------|-------|
| Contexto, intención, negocio | Integración, ejecución técnica |
| Decisión y aprobación humana | Automatización y transformación |
| Trazabilidad empresarial | Trazabilidad técnica |
| Experiencia del usuario | Conectores e interoperabilidad |

El expediente **nunca** codifica APIs, BD ni SFTP. Solo declara **qué capacidad** necesita.

## Catálogo de capacidades

Definido en `backend/app/evaluacion_models.py` (`CAPACIDADES_EXTERNAS`):

- `consultar_datos`
- `enviar_informacion`
- `validar_registros`
- `sincronizar`
- `transformar`
- `obtener_documento`
- `ejecutar_proceso`
- `notificar`
- `consultar_estado`

API: `GET /api/evaluaciones/capacidades`
Servicio: `piiax_bridge_service.list_capacidades_catalog()`

## Flujo conceptual

```
Hallazgo / pregunta usuario
    → clasificación intención (A–F)
    → (opcional) solicitud acción externa con capacidad + tipo
    → aprobación si PROPUESTA/EJECUCIÓN
    → handoff stub PIIAX (sin conector real)
    → estado + resultado compatible + evidencia
    → actualización expediente / indicadores
```

## Tipos de acción (negocio)

`LECTURA` | `ANALISIS` | `PROPUESTA` | `EJECUCION`

La resolución técnica (qué conector, qué endpoint) queda exclusivamente en PIIAX cuando exista integración.
