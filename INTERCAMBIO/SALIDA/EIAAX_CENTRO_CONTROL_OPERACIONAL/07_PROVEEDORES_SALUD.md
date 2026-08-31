# 07 — Proveedores y salud

## Proveedores IA

Bloque `proveedores` consume `LlmProviderConfig` + logs 24h:

- Disponibilidad / degradado / no disponible
- Errores, latencia, modelo
- **Sin monitoreo ficticio**

## Salud de servicios

Pestaña Salud reutiliza:

- `build_health_report()` — API, DB, schedulers
- Continuidad, aprendizaje, optimización (adapters existentes)
- Multiproveedor adapter (1270)

## Frontera Inteligencia de Resultados

`resultados_frontera`: ANTES / PROYECTADO / REAL — integrado=false, sin fabricar ROI.
