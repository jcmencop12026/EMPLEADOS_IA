# 05 — Mapa empresarial

## Modelo `dossier_mapa_nodos`

Tipos: `AREA`, `PROCESO`, `SUBPROCESO`, `ACTIVIDAD`, `ROL`, `SISTEMA`, `FUENTE_INFO`, `INDICADOR`, `PROBLEMA`, `DEPENDENCIA`.

## Construcción progresiva

`construir_mapa_desde_expediente()` deriva:

- Área desde `area_proceso`
- Procesos desde ítem `procesos_afectados`
- Problema desde `necesidad`

Mapa **incompleto por diseño** — evoluciona con cada diagnóstico. No es modelador BPMN.

## Jerarquía

`parent_id` permite árbol simple área → proceso → problema.
