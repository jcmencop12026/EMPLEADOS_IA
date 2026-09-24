# Capacidades descartadas o no portadas

## Descartado explícitamente (por autoridad / riesgo)

| Elemento | Motivo |
|----------|--------|
| Sobrescritura `CentroConfianzaPage.tsx` (rama A) | Incompatibilidad API con base Lote 3 — se preservó versión `d034566` |
| Migraciones literales A/B/C/D con IDs históricos colisionantes | Reconstruidas como `1780`–`1820` post-`1770` |
| Segundo scheduler comercial de informes | MB-11 permanece autoridad; D usa `informes_comerciales_adapter` |
| Tercer centro de control | Solo MB-08 operacional + Centro Estratégico |
| PostgreSQL / PIIAX / OpenAI real | Fuera de alcance convergencia |
| Rediseño masivo pantalla por pantalla | Backlog post-convergencia |
| Migración ciega de todas las tablas a `EiaaxTable` | Solo patrón establecido; migración completa en segundo recorrido |

## No re-portado (ya existía en base `d034566`)

- `motor_economico`, `centro_negocios`, `continuidad_comercial`
- `transformacion` (Arquitecto), `resultados`, `control_center` (MB-08)
- `gobierno_operacional`, `empresa_seguridad`, `partners`
- `evaluaciones`, `implementacion`, `comunicaciones`, `soporte`
- Migraciones base hasta `1770a1b2c3d4e`

## Parcial / pendiente visual

- UI dedicada flujo comercial pantalla completa (flujo vía API + centros existentes)
- Cockpit empresa unificado MB-08 + Estratégico (navegación preparada, UX final post-V1)
- Login/logo EIAAX, mensajes sesión, gráficos impacto (backlog humano)
