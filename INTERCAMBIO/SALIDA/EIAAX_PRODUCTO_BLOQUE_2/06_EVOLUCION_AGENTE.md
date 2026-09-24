# 06 — Evolución agente «Preguntar a EIAAX»

## Clasificación de intención A–F

Servicio: `evaluacion_intent_service.classify_intent()`

| Código | Significado |
|--------|-------------|
| A | Respuesta con información existente |
| B | Necesita información adicional |
| C | Requiere análisis IA |
| D | Consulta fuente externa (lectura) |
| E | Ejecutar acción externa |
| F | Requiere aprobación humana |

## Comportamiento `ask_eiaax`

- Devuelve `intencion`, `piiax`, `contexto_expediente`
- Estados de respuesta: `respuesta_local`, `informacion_adicional`, `sin_proveedor`, `requiere_capacidad_externa`, `ok`
- **`ejecutar_externo_automatico`: siempre `false`** en BP2
- Sugiere `capacidad_sugerida` y `requiere_aprobacion` cuando aplica

## Panel frontend

`EiaaxAskPanel.tsx` muestra badge de intención y mensaje orientado a acción manual (solicitud desde hallazgo).

Próximo bloque: ejecución automática condicionada por política (fuera de BP2).
