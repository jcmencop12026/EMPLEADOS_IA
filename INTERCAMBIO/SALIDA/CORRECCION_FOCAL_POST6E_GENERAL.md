# Corrección focal post-6E — Agente General

## BASE

| Campo | Valor |
|---|---|
| Rama base | `cursor/fase2-central-integracion` |
| Rama trabajo | `cursor/correccion-focal-post6e-85e4` |
| HEAD certificado post-6E | `3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b` |

## HEAD FINAL

`7d36b43a06888d051fdee74277905becadaae0fb` (rama `cursor/correccion-focal-post6e-85e4`)

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `frontend/src/styles.css` | Estilos `.metrics-grid`, `.metric-card`, `.metric-label`; hover CC |
| `frontend/src/lib/labels.ts` | `HEALTH_STATUS`, `formatHealthStatus()` |
| `frontend/src/pages/CentroControlPage.tsx` | Traducción presentacional salud y auditoría |
| `tests/test_correccion_focal_post6e_p1.py` | Pruebas focales anti-regresión |

## P1-CC-01 — Resumen ejecutivo ilegible

**Causa raíz:** El bloque "Resumen ejecutivo" usaba clases `metrics-grid`, `metric-card` y `metric-label` sin reglas CSS globales efectivas. Solo existía `.centro-control-page .cc-metric-card { text-decoration; color }`, por lo que los KPI se renderizaban como texto inline concatenado.

**Solución:** Añadir estilos de grid y tarjeta compacta reutilizando el patrón visual de `.dashboard-grid` / `.dashboard-card` (display grid, flex column, etiqueta pequeña, valor destacado, separación y responsive `auto-fill/minmax(140px,1fr)`). Hover sutil en tarjetas enlazables del Centro de Control.

## P1-CC-02 — "Estado API: up"

**Causa raíz:** `CentroControlPage` mostraba el valor canónico técnico (`up`, `down`, `degraded`) directamente en la UI de Salud.

**Solución:** Función presentacional `formatHealthStatus()` en `labels.ts` con mapeo: `up`→Operativa, `down`→No disponible, `degraded`→Degradada, `unknown`→Desconocido. Aplicada a Estado API, Base de datos y Schedulers en la misma vista. Valores canónicos del backend/API sin cambios.

## P1-CC-03 — "auth.login"

**Causa raíz:** La tabla "Auditoría reciente" renderizaba `row.accion` sin pasar por el mecanismo de etiquetas ya existente (`formatAuditAction` en `labels.ts`), usado en otras vistas de auditoría.

**Solución:** Importar y aplicar `formatAuditAction(row.accion)`. Códigos desconocidos usan fallback legible (`auth.login` → puntos/espacios) sin alterar persistencia ni API.

## P2 tocados incidentalmente

Ninguno. Los 8 P2 reportados por Agente D quedan registrados para convergencia final sin campaña correctiva en este gate.

## Tests focales

`tests/test_correccion_focal_post6e_p1.py` — 6 pruebas:

- CSS `metrics-grid` / `metric-card` / `metric-label` presente
- Estructura Resumen ejecutivo en `CentroControlPage`
- `formatHealthStatus` y ausencia de render crudo de `status`
- `formatAuditAction` en auditoría reciente
- Valores canónicos API de salud y auditoría sin alteración

## Regresión

| Métrica | Resultado |
|---|---|
| PASSED | 1235 |
| FAILED | 0 |
| ERRORS | 0 |
| SKIPPED | 4 |

Baseline post-6E: 1229 passed → +6 tests focales nuevos.

## Frontend build

`npm run build` — **PASS**

## Validación visual

Aplicación real en `http://127.0.0.1:5180` (backend `8010`).

| Área | Resultado | Evidencia |
|---|---|---|
| Resumen — KPI legibles y separados | **PASS** | `/opt/cursor/artifacts/screenshots/cc-resumen-kpis.png` |
| Salud — Estado API en español ("Operativa") | **PASS** | `/opt/cursor/artifacts/screenshots/cc-salud-estado.png` |
| Salud — Auditoría sin `auth.login` crudo ("Inicio de sesión") | **PASS** | `/opt/cursor/artifacts/screenshots/cc-auditoria.png` |

## Alembic

| Campo | Valor |
|---|---|
| Heads | 1 |
| Head | `1341a1b2c3d4e` |

## P0 / P1 / P2

| Nivel | Antes (D post-6E) | Después |
|---|---|---|
| P0 | 0 | 0 |
| P1 | 3 (CC-01, CC-02, CC-03) | 0 (corregidos) |
| P2 | 8 (documentados, sin campaña) | 8 (sin cambio) |
