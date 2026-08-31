# 09 — Guía visual

## Navegación

Menú **Análisis y control** → **Inteligencia de resultados** (`/resultados`)

Desde expediente: pestaña **Impacto e Indicadores** → enlace **Inteligencia de resultados →**

## Hub de indicadores

- Tabla `EiaaxTable` con columnas ANTES / PROYECTADO / REAL
- Filtro por `?expediente_id=`
- Botón **Generar informe de impacto** (permiso `resultados.informe.generate`)

## Informe narrativo

- Secciones en español con encabezados `##`
- Nota de advertencia cuando hay PROYECTADO sin REAL
- Enlace de retorno a indicadores del expediente

## Tokens y tema

- `tag-proyectado` — proyección en cursiva ámbar
- `informe-narrativa` — tipografía compacta, compatible tema claro/oscuro
- `ContextualHelp` en hub e informe

## Ayuda contextual

`frontend/src/lib/resultadosHelp.ts`
