# 06 — Causas y oportunidades

## Cadena causal (`dossier_causas`)

| Tipo | Significado |
|------|-------------|
| `SINTOMA` | Problema original declarado |
| `PROBLEMA` | Hallazgo estructurado |
| `CAUSA_PROBABLE` | Inferencia — no presentada como hecho |
| `CAUSA_VALIDADA` | Reservado validación humana (P1) |

Cada causa incluye `explicacion_confianza` y evidencia.

## Oportunidades

- **Internas:** alternativas de proceso, automatización, IA
- **Externas:** dominios `EXTERNO_*` en diagnósticos 1220 — puente vía expediente → `crear_oportunidad_desde_hallazgo`
- **NO** se reconstruye Centro de Oportunidades — se reutiliza 1030

## Detección problemas

Hallazgos BP1 cubren reprocesos, demoras, información pendiente, objetivos. Mapa tipo `PROBLEMA` complementa.
