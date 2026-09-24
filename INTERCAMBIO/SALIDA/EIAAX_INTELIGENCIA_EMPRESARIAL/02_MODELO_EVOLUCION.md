# 02 — Modelo de evolución

## Cadena analítica

```
EVIDENCIA → ANÁLISIS → HALLAZGO → CAUSA → IMPACTO → OPORTUNIDAD → RECOMENDACIÓN → ACCIÓN
```

Implementada en `cadena_analitica.construir_cadena_expediente` y `construir_cadena_oportunidad`.

## Evaluación adaptativa

| Nivel | Profundidad |
|-------|-------------|
| PRELIMINAR | Evaluación base + catálogo reducido |
| DIAGNOSTICA | + hallazgo métricas si disponibles |
| PROFUNDA | + hallazgo evidencia documental |

## Priorización

| Decisión | Origen motor 1030 |
|----------|-------------------|
| HACER | ACTUAR / aprobada / en ejecución |
| ESTUDIAR | OBSERVAR / SOLICITAR_DATOS |
| ESPERAR | POSPONER / seguimiento |
| DESCARTAR | DESCARTADA |

## Motor proactivo

Nueva evidencia → señal (`create_signal`) — **sin** decisión automática.

## Contratos futuros

`contracts.CONTRATOS_FUTUROS` — motor económico B, Centro Control, Asistente, PIIAX, resultados.
