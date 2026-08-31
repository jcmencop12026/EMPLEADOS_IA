# 06 — Agente EIAAX

## Panel «Preguntar a EIAAX»

Clasifica intención A–H y responde según estado:

| Intención | Estado respuesta |
|-----------|------------------|
| A | `respuesta_local` |
| B | `informacion_adicional` |
| C | `ok` (gateway IA) / `sin_proveedor` |
| D/E/F | `requiere_capacidad_externa` |
| G | `oportunidad_sugerida` |
| H | `tarea_seguimiento` |

## Gateway IA

Usa `route_task` existente — sin acoplar proveedor directamente. Sin inventar respuestas si no hay LLM.

## Motor de siguiente acción

Complementa al agente con sugerencias estructuradas en consola.
