# 07 — Impacto y oportunidades

## Impacto

- Indicadores `ANTES` / `PROYECTADO` / `REAL` — distinción estricta
- `PROYECTADO` ≠ resultado obtenido
- Gráficos dinámicos (`ImpactoGrafico.tsx`)
- Campo `fuente` preparado para datos externos (PIIAX / FinOps)

## Integración FinOps (agente B)

**Stub:** `evaluacion_integracion_finops.py` — `INTEGRACION_FINOPS_DISPONIBLE = False`

Punto de extensión: `obtener_indicadores_economicos()`, `enriquecer_impacto_desde_finops()`

## Oportunidades

Reutiliza motor 1030:

- `POST .../oportunidades/crear` desde hallazgo
- `POST .../oportunidades/vincular`
- Pipeline proactivo existente

No se reconstruye Centro de Oportunidades.
