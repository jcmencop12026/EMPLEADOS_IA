# 07 — Motor de transformación

## Alternativas (`transformacion_alternativas`)

Tipos: eliminar, simplificar, estandarizar, reorganizar, digitalizar, integrar, automatizar, aplicar IA, empleado IA, capacidad externa, rediseñar control, medir, mantener humano.

## Motor de decisión

Score ordinal basado en impacto, esfuerzo, riesgo y confianza disponible:

```
score = impacto×3 + (4-esfuerzo) + (4-riesgo) + confianza
```

Una alternativa marcada `recomendada` con `explicacion` del porqué.

## No asume IA siempre

Incluye `MANTENER_HUMANO` y `MEDIR` cuando confianza es baja.

## API

`POST /api/transformacion/expedientes/{id}/diagnosticar` ejecuta el motor completo.
