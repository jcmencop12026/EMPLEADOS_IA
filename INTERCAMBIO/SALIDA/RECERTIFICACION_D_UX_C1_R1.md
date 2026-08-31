# RECERTIFICACIÓN D — UX C1-R1

> **NOTIFICACIÓN VISIBLE**  
> **EIAAX — RECERTIFICACIÓN UX C1-R1 FINALIZADA**  
> **SHA:** `3226ba5ee9b998547c7026c98b69972dfacd2d3d`  
> **Candidato anterior:** `25ad1021ee6ea0322aceb0622252e7b748706d32`  
> **VEREDICTO:** **C1-R1 UX APTO**  
> **P0=0 · P1=0 · P2 nuevos=0** (P2 históricos no exigidos)  
> **Estado agente:** EN RESERVA  
> **Voz/TTS:** No disponible (no bloqueante)

---

## Metadatos

| Campo | Valor |
|-------|-------|
| Agente | D (visual / UX / español) |
| Protocolo base | `INTERCAMBIO/SALIDA/GATE_D_UX_C1.md` |
| Commit | `fix(c1-r1): fallback determinístico ruta inicial / (P1-D-UX-01)` |
| Fecha UTC | 2026-08-31 |
| Método | Diff C1→C1-R1 + gate focal 15 controles + Puppeteer 1280×900 + revisión código |

---

## Corrección verificada (GENERAL)

| Componente | Función |
|------------|---------|
| `frontend/src/navigation/menu.ts` | Fuente única menú sidebar |
| `frontend/src/navigation/homeRoute.ts` | `resolveHomeRoute()` — primera ruta accesible |
| `frontend/src/pages/HomePage.tsx` | CC si `control_center.view`; si no, `<Navigate>`; si null → `NoModulesPage` |
| `frontend/src/pages/NoModulesPage.tsx` | Pantalla segura español + cerrar sesión |
| `frontend/src/App.tsx` | `index` y `centro-control` → `HomePage` |
| `frontend/src/AppShell.tsx` | Importa `MENU` desde `navigation/menu.ts` |

**Diff C1 → C1-R1:** 13 archivos, +584/−87 líneas. **No toca** hotfix login (`api.ts`, `LoginPage.tsx`, `styles.css` login).

---

## Resultado por control obligatorio

| # | Control | Resultado | Evidencia |
|---|---------|-----------|-----------|
| 1 | CON `control_center.view` → `/` = CC | **PASS** | `admin` ve «Centro de Control ejecutivo» |
| 2 | SIN CC, con módulos → primera ruta accesible | **PASS** | `restricted_cc` → `/trabajo` |
| 3 | `restricted_cc` ya no bloqueado en `/` | **PASS** | Sin mensaje denegación CC |
| 4 | Sin módulos navegables → `NoModulesPage` español | **PASS** | «Sin módulos habilitados» |
| 5 | Sin loops redirección | **PASS** | Hops estables (`/trabajo` sin rebote) |
| 6 | Sin 403 como experiencia inicial | **PASS** | UI sin 403 en landing |
| 7 | `NoModulesPage` permite cerrar sesión | **PASS** | Botón «Cerrar sesión» |
| 8 | Sin módulos no autorizados en menú | **PASS** | `restricted_cc`: sin Empresas/Oportunidades |
| 9 | Sidebar + home usan `navigation/menu.ts` | **PASS** | `AppShell` + `homeRoute` importan `MENU` |
| 10 | `CentroControlPage` preservado | **PASS** | Renderizado vía `HomePage` con permiso CC |
| 11 | Mi Trabajo preservado | **PASS** | `/trabajo` operativo |
| 12 | Login / hotfix visual preservado | **PASS** | Toggle, olvidó, 401 español (sin diff C1) |
| 13 | MFA/SSO preservados | **PASS** | `verifyMfaLogin`, `discoverLogin` en código |
| 14 | Labels español, metrics-grid, compact-*, localStorage | **PASS** | Sin regresión vs C1 |
| 15 | Sin regresión visual material vs C1 | **PASS** | Cambio acotado a navegación/home |

**Gate focal:** **19/19 PASS**

---

## P1-D-UX-01 — Estado definitivo

| Campo | C1 (`25ad102`) | C1-R1 (`3226ba5`) |
|-------|----------------|-------------------|
| Usuario `restricted_cc` en `/` | Mensaje bloqueante CC | Redirect a `/trabajo` |
| Fallback determinístico | **No** | **Sí** — `resolveHomeRoute` → `/trabajo` |
| Loop | No | No |
| API CC sin permiso | 403 backend (correcto) | 403 backend (correcto) |

### Prueba reproducida

- Usuario: `restricted_cc` / `Restricted2026*`
- Permisos: `operations.view`, `notification.view`, `employee.view` (**sin** `control_center.view`)
- URL final: `http://127.0.0.1:5184/trabajo`
- Contenido: bandeja «Mi trabajo» — **sin** «No tiene permiso para ver el Centro de Control»

### Conclusión

**P1-D-UX-01: CERRADO**

---

## Clasificación regresiones

### P0
*Ninguna.*

### P1
*Ninguna.* (P1-D-UX-01 cerrado)

### P2 nuevos
*Ninguno introducido por C1-R1.*

Los 9 P2 históricos de preintegración (`Schedulers`, densidad sidebar, etc.) **permanecen registrados** y no se exigen en este gate.

### Regresiones vs candidato anterior (C1)

| Área | Evaluación |
|------|------------|
| Hotfix login | **Preservado** — sin cambios en archivos login |
| MFA/SSO | **Preservado** |
| CC / Mi trabajo / sidebar V2 | **Preservado** + mejora home |
| P1-D-UX-01 | **Corregido** |

### Observación no bloqueante

`no_modules_user` conserva en sidebar **Mi seguridad** (`/mi-seguridad` sin permisos requeridos en `ROUTE_PERMISSIONS`). Es coherente con RBAC actual y excluido de destino home (`HOME_ROUTE_EXCLUDE`). No constituye P1/P2 nuevo.

---

## Evidencia visual

| Archivo | Descripción |
|---------|-------------|
| `c1r1_admin_home.png` | Admin — Centro de Control ejecutivo |
| `c1r1_admin_trabajo.png` | Admin — Mi trabajo |
| `c1r1_admin_auditoria.png` | Labels «Inicio de sesión» |
| `c1r1_restricted_home.png` | **P1 cerrado** — `restricted_cc` en `/trabajo` |
| `c1r1_nomodules.png` | `NoModulesPage` + cerrar sesión |

Ruta: `/opt/cursor/artifacts/screenshots/`

---

## Veredicto obligatorio

# C1-R1 UX APTO

La corrección de fallback determinístico cierra P1-D-UX-01 sin regresiones UX materiales respecto al candidato C1 anterior.

---

*Agente D — recertificación UX C1-R1. Sin modificación de producto. EN RESERVA.*
