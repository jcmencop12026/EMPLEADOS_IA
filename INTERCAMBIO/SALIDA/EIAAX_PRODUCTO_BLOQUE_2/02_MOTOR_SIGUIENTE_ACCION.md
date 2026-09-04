# 02 — Motor de siguiente acción

**Servicio:** `evaluacion_siguiente_accion_service.py`
**API:** `GET /api/evaluaciones/{id}/siguiente-accion`

## Principio

No botones estáticos. Las acciones sugeridas dependen de:

- Estado del expediente y % información
- Hallazgos y confianza global
- Acciones externas pendientes
- Proveedores disponibles
- Permisos RBAC del usuario

## Acciones posibles (ejemplos)

`solicitar_informacion`, `ejecutar_evaluacion`, `profundizar_analisis`, `detectar_oportunidad`, `cuantificar_impacto`, `solicitar_capacidad_externa`, `solicitar_aprobacion`, `proveedor_no_disponible`, `continuar_evaluacion`

## Respuesta

```json
{
  "principal": { "codigo", "titulo", "descripcion", "intencion", "pestaña", "prioridad" },
  "alternativas": [...],
  "contexto": { "proveedores", "hallazgos_count", ... }
}
```

Persistencia opcional en `evaluaciones_expediente.siguiente_accion_json`.

## UI

`SiguienteAccionPanel.tsx` en pestaña Resumen — navegación a pestaña sugerida.
