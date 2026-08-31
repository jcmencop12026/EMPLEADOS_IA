# GATE D — UX C1 (protocolo mínimo)

**Baseline:** `INTERCAMBIO/SALIDA/AUDITORIA_D_UX_PREINTEGRACION.md`  
**SHA objetivo:** `25ad1021ee6ea0322aceb0622252e7b748706d32`  
**Modo:** Solo certificación — sin rediseño EIAAX

## Controles (17)

| # | Control | Método |
|---|---------|--------|
| 1 | Login C1 | API `POST /api/auth/login` + UI formulario |
| 2 | Hotfix visual integrado | Código `api.ts` + `LoginPage.tsx` + `styles.css` |
| 3 | MFA/SSO preservados | Presencia `verifyMfaLogin`, `discoverLogin` en LoginPage |
| 4 | Ruta inicial `/` | Navegación post-login |
| 5 | Usuario CON `control_center.view` → CC | `admin` / `viewer` en `/` |
| 6 | Usuario SIN `control_center.view` → fallback determinístico | Rol custom sin CC en `/`; destino predecible |
| 7 | Sin loop redirección | URL estable post-login |
| 8 | Sin 403 como experiencia inicial | Texto/código en landing |
| 9 | `CentroControlPage` preservado | Import/ruta en `App.tsx` |
| 10 | Mi Trabajo preservado | `/trabajo` + menú |
| 11 | Sidebar preservado | `AppShell.tsx` marca española |
| 12 | Páginas V2 preservadas | Conteo rutas `App.tsx` ≥ 65 |
| 13 | Labels español | Auditoría `Inicio de sesión` |
| 14 | `metrics-grid` | `.metrics-grid` en `styles.css` |
| 15 | `compact-*` | `.compact-tabs`, `.compact-panel` |
| 16 | Persistencia `localStorage` | Sidebar + columnas trabajo |
| 17 | Sin regresiones materiales C1 | `git diff dc1e6cd..25ad102 -- frontend/src/` |

## Criterio P1-D-UX-01

Usuario autenticado **sin** `control_center.view` que navega a `/` debe obtener **fallback funcional** (p. ej. `/trabajo`, `/directorio` o panel reducido), **sin** mensaje bloqueante de CC y **sin** 403 inicial.

## Evidencia

Capturas en `/opt/cursor/artifacts/screenshots/c1_*.png`
