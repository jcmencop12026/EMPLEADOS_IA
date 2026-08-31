# 10 — Brechas restantes

## P0

Ninguno identificado en alcance 1410.

## P1

| Brecha | Nota |
|--------|------|
| Exportación PDF/Word de informes | Reutilizar generación documental existente cuando GENERAL integre |
| Filtros avanzados en UI (periodo, agrupación) | API lista; UI muestra filtro por expediente |
| Consumo Motor Económico (ROI/ahorro) | Interfaces preparadas vía línea base; integración rama B pendiente |

## P2

| Brecha | Nota |
|--------|------|
| Gráficos dinámicos | Solo cuando haya datos suficientes — tabla prioritaria |
| IA para redacción narrativa | Estructura determinística lista; mejora opcional posterior |
| `conftest` SQLite sin Alembic | Suite global usa `create_all`; tests 1410 requieren BD migrada o fix transversal |
| Informes INSTITUCIONAL/regulatorios | No certificados — requiere plantillas y validación legal |

## Para GENERAL

- Merge desde `cursor/eiaax-inteligencia-resultados-9a85` → base de integración
- Migración `1410a1b2c3d4e`
- Verificar `bootstrap_permissions` en despliegues existentes
