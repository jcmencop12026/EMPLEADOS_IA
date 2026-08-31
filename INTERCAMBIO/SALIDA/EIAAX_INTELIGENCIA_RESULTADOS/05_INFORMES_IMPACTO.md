# 05 — Informes de impacto

## Estructura versionable

Tabla `resultados_informes`:

- `tipo`: EJECUTIVO, SEGUIMIENTO, IMPACTO, MEJORAMIENTO, INSTITUCIONAL
- `version` incremental por expediente
- `visibilidad`: INTERNO | VISIBLE_ENTIDAD
- `contenido_json` + `narrativa` determinística

## Preguntas respondidas (sin IA obligatoria)

| Sección narrativa | Fuente |
|-------------------|--------|
| Qué ocurrió | Expediente + hallazgos |
| Por qué | `necesidad` / causas |
| Quién intervino | Entidad, área |
| Cómo | Nivel, % información |
| Cuándo | Fechas expediente |
| Cuánto | Tabla ANTES/PROY/REAL por indicador |
| Qué hicimos | Plan de acciones |
| Qué mejoró | Conteo indicadores con REAL |
| Qué sigue | Proyecciones sin medición |

## API

- `POST /api/resultados/informes/generar`
- `GET /api/resultados/informes`, `GET /api/resultados/informes/{id}`

## Frontend

- Hub: `/resultados`
- Detalle: `/resultados/informes/:informeId`

**Nota:** No se certifica cumplimiento de formatos regulatorios específicos no implementados.
