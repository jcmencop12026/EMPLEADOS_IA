# 10 — Guía visual

## Acceso

Menú **Análisis y control → Evaluaciones EIAAX** → abrir expediente.

## Elementos clave

1. **Barra PIIAX** — disponible / no conectado (EIAAX sigue operando)
2. **Siguiente acción sugerida** — panel en Resumen con intención y navegación
3. **Pestaña Análisis** — hallazgos + solicitud capacidad externa por hallazgo
4. **Estados en español** — badges `NO DISPONIBLE`, `EN COLA`, etc.
5. **Impacto** — barras ANTES / PROYECTADO / REAL
6. **Vista Entidad** — datos estructurados (no JSON)
7. **Preguntar a EIAAX** — panel lateral con intención A–H

## Componentes reutilizados (experiencia transversal)

- `AsyncState` (Loading/Empty/Error)
- Patrones `EstadoBadge` / badges semánticos
- `HelpTooltip` (comercial/optimización) donde aplica
- Sidebar y tema claro/oscuro existentes

## Permisos relevantes

`evaluacion.view`, `evaluacion.manage`, `evaluacion.evaluate`, `evaluacion.accion.request`, `evaluacion.accion.approve`, `evaluacion.indicadores.manage`
