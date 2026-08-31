# 04 — ANTES / PROYECTADO / REAL

## Regla fundamental

1. **ANTES** — línea base o valor histórico registrado.
2. **PROYECTADO** — expectativa, objetivo o inferencia; **nunca** resultado conseguido.
3. **REAL** — solo vía `register_medicion_real` con `evidencia_ref` (permiso `resultados.validate`).

## UI

- ANTES: badge `estado-recibido`
- PROYECTADO: clase `tag-proyectado` + tooltip
- REAL ausente: texto *Sin medición posterior*

## Caso demo (REAL < PROYECTADO)

Indicador **Recuperación cartera glosada**: ANTES 58 %, PROYECTADO 82 %, REAL 69 % — desviación visible, sin maquillar.

Indicador **Reducción costo reproceso**: PROYECTADO 20M sin REAL — muestra pendiente de medición.

## Endpoint

`GET /api/resultados/antes-proyectado-real?expediente_id=…`
