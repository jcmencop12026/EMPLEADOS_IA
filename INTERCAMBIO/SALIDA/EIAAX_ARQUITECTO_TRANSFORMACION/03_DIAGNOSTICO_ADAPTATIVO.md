# 03 — Diagnóstico adaptativo

## Sin cuestionario universal

La información requerida proviene del catálogo BP1 (`_INFO_CATALOGO` en `evaluacion_service`) filtrado por **nivel**:

- `PRELIMINAR` — contexto, problema, procesos
- `DIAGNOSTICA` — + métricas, sistemas, restricciones
- `PROFUNDA` — + evidencias, stakeholders

## Flujo API

1. `POST /api/transformacion/necesidad` — interpreta necesidad, crea expediente, sincroniza ítems
2. `GET .../suficiencia` — evalúa faltantes sin bloquear
3. `POST .../diagnosticar` — ejecuta evaluación preliminar + mapa + causas + transformación

## Estados información (español)

`RECIBIDO`, `INCOMPLETO`, `PENDIENTE`, `OPCIONAL` — heredados de BP1.

## Continuidad con información incompleta

Diagnóstico preliminar procede con confianza `BAJA`/`MEDIA` y hallazgo explícito de información pendiente.
