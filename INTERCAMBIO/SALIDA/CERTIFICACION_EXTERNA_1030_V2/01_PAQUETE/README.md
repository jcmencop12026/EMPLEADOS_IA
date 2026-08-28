# OPORTUNIDADES PROACTIVAS 1030 — CERTIFICACIÓN EXTERNA V2

Paquete sustitutivo creado porque la recuperación forense concluyó que el paquete externo original y su oráculo canónico no estaban disponibles.

## Contenido
- `CASOS/`: entradas ciegas de 12 casos nuevos.
- `ORACULO_SELLADO/`: resultados/reglas esperados. NO consultar antes de congelar brutos.
- `MATRIZ_EVALUACION_V2.csv`: 12 controles bloqueantes.
- `PROTOCOLO_CERTIFICACION_CIEGA_V2.md`: secuencia obligatoria.
- `CONTROL/HASHES_ORACULO_ANTES_ENTREGA.csv`: huellas del oráculo antes de la ejecución.

## Principio
Cursor debe ejecutar primero los casos sin consultar el oráculo. La comparación se realiza únicamente después de congelar y hashear las salidas brutas.
