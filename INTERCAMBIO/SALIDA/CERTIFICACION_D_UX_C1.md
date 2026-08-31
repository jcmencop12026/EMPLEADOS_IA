# CERTIFICACIÓN D — UX C1

> **NOTIFICACIÓN VISIBLE**  
> **EIAAX — CERTIFICACIÓN UX C1 FINALIZADA**  
> **SHA:** `25ad1021ee6ea0322aceb0622252e7b748706d32`  
> **VEREDICTO:** **C1 UX NO APTO**  
> **P0=0 · P1=1 · P2 nuevos=0** (9 P2 preintegración permanecen registrados)  
> **Estado agente:** EN RESERVA  
> **Voz/TTS:** No disponible (no bloqueante)

---

## Metadatos

| Campo | Valor |
|-------|-------|
| Agente | D (visual / UX / español) |
| Protocolo | `INTERCAMBIO/SALIDA/GATE_D_UX_C1.md` |
| Baseline UX | `INTERCAMBIO/SALIDA/AUDITORIA_D_UX_PREINTEGRACION.md` |
| V2 referencia | `dc1e6cda8d3de6695d9a052a2a13afdb5f431077` |
| SHA certificado | `25ad1021ee6ea0322aceb0622252e7b748706d32` |
| Commit | `feat(c1): base segura convergencia V1+V2 con hotfix login selectivo` |
| Fecha UTC | 2026-08-31 (re-ejecución gate 12:43 UTC) |
| Método | Gate 17 controles: diff C1↔V2 + API + Puppeteer 1280×900 (2 corridas) |

---

## Alcance C1 (diff real vs V2)

C1 **no altera** navegación, CC, sidebar ni páginas V2. Solo integra hotfix login selectivo:

| Archivo | Cambio |
|---------|--------|
| `frontend/src/api.ts` | Lee `text` antes de `!res.ok`; 401 login con mensaje por `path` |
| `frontend/src/pages/LoginPage.tsx` | Toggle contraseña + panel «¿Olvidó su contraseña?»; **MFA/SSO V2 intactos** |
| `frontend/src/styles.css` | `.password-field`, `.login-forgot-panel` |
| `backend/scripts/*` | Recuperación admin (fuera UX gate visual) |
| `tests/test_v1_hotfix_login.py`, `tests/test_convergencia_c1.py` | Regresión focal |

---

## Resultado por control (PASS/FAIL)

| # | Control | Resultado | Evidencia / notas |
|---|---------|-----------|-------------------|
| 1 | Login C1 | **PASS** | `admin`/`Admin2026*` → 200 + token |
| 2 | Hotfix visual integrado | **PASS** | Toggle 👁, panel olvidó, estilos CSS |
| 3 | MFA/SSO preservados | **PASS** | `verifyMfaLogin`, `discoverLogin`, `beginPublicOidc` en código |
| 4 | Ruta inicial `/` | **PASS** | Post-login navega a `/` |
| 5 | CON `control_center.view` → CC | **PASS** | `admin` y `viewer` ven «Centro de Control ejecutivo» |
| 6 | SIN `control_center.view` → fallback determinístico | **FAIL** | Sin redirect a ruta accesible; ver P1-D-UX-01 |
| 7 | Sin loop redirección | **PASS** | `admin`, `viewer`, restringido: URL estable, no rebote `/login` |
| 8 | Sin 403 experiencia inicial | **PASS** (admin/viewer) / **FAIL** (restringido) | Restringido: pantalla de denegación CC (no HTTP 403, pero UX bloqueante) |
| 9 | `CentroControlPage` preservado | **PASS** | Ruta index sin cambios vs V2 |
| 10 | Mi Trabajo preservado | **PASS** | `/trabajo` operativo; menú «Mi trabajo» |
| 11 | Sidebar preservado | **PASS** | «Sistema empresarial de IA», secciones colapsables |
| 12 | Páginas V2 preservadas | **PASS** | 70 rutas en `App.tsx` (≥ 65) |
| 13 | Labels español | **PASS** | Auditoría: «Inicio de sesión»; login en español |
| 14 | `metrics-grid` | **PASS** | Regla CSS presente |
| 15 | `compact-*` | **PASS** | `.compact-tabs`, `.compact-panel`, `.compact-toolbar` |
| 16 | `localStorage` | **PASS** | Sidebar collapse/secciones; `trabajo_cols_v1` |
| 17 | Sin regresiones materiales C1 | **PASS** | Diff C1→V2 limitado a api/login/styles (+3 archivos frontend) |

**Resumen:** 15/17 PASS · 2/17 FAIL (ambos ligados a P1-D-UX-01)

---

## P1-D-UX-01 — Resultado específico

| Campo | Valor |
|-------|-------|
| ID | P1-D-UX-01 |
| Origen | Auditoría preintegración |
| Expectativa C1 | Fallback funcional en `/` para usuarios sin `control_center.view` |
| Estado en C1 | **NO RESUELTO** |

### Prueba ejecutada

1. Rol custom `restricted_cc` con permisos: `operations.view`, `notification.view`, `employee.view` (**sin** `control_center.view`).
2. Usuario `restrux_7160f84d` / `Restricted2026*`.
3. Login OK → navegación a `/`.

### Observado

- URL permanece en `/` (sin loop).
- Contenido principal: **«No tiene permiso para ver el Centro de Control.»**
- Sidebar **sí** muestra rutas accesibles (Mi trabajo, Directorio, Notificaciones).
- **No** hay redirect automático a `/trabajo`, `/directorio` ni panel reducido.
- `CentroControlPage.tsx` L65-70: bloqueo estático sin `Navigate` fallback.

### Fallback determinístico (control #6)

| Criterio | Esperado | Observado C1 |
|----------|----------|--------------|
| Destino predecible sin CC | Redirect a primera ruta permitida (`/trabajo`, `/directorio` o `/operaciones`) | **No** — permanece en `/` |
| Sin mensaje bloqueante CC | Sin texto de denegación en contenido principal | **No** — muestra error CC |
| Repetibilidad | Mismo resultado en re-ejecuciones | **Sí** — 2 corridas gate idénticas (`restrux_7160f84d`) |

`deterministic = false` · `redirected = false` · `noPerm = true`

### Conclusión P1-D-UX-01

**FAIL** — La política de roles estándar (`viewer`/`operator` incluyen `control_center.view`) mitiga el caso mayoritario, pero **no implementa** fallback determinístico para usuarios sin CC. El hallazgo preintegración **permanece abierto**.

---

## Regresiones

### P0
*Ninguna.*

### P1 (bloqueante gate)

| ID | Descripción |
|----|-------------|
| **P1-D-UX-01** | Landing `/` sin fallback para usuarios sin `control_center.view` |

### P2 nuevos en C1
*Ninguno introducido por C1.*

Los **9 P2** de `AUDITORIA_D_UX_PREINTEGRACION.md` (`Schedulers`, `bootstrap.admin_created`, densidad sidebar, etc.) **permanecen registrados** y no se exigen para este gate.

### Regresiones vs V2 certificado

| Área | ¿Regresión C1? |
|------|----------------|
| CC / sidebar / rutas V2 | **No** — sin cambios |
| Login hotfix | **Mejora** — 401 correcto, toggle, panel olvidó |
| MFA/SSO | **No** — preservados |
| P1-D-UX-01 | **Sin cambio** — ya presente en V2, no corregido en C1 |

---

## Evidencia visual

| Archivo | Descripción |
|---------|-------------|
| `c1_login_bad_password.png` | Error español credenciales incorrectas |
| `c1_login_forgot.png` | Panel «¿Olvidó su contraseña?» |
| `c1_admin_home.png` | CC ejecutivo — admin |
| `c1_admin_trabajo.png` | Bandeja Mi trabajo |
| `c1_admin_auditoria.png` | Auditoría con «Inicio de sesión» |
| `c1_viewer_home.png` | Viewer con CC (rol incluye permiso) |
| `c1_restricted_home.png` | **FAIL P1** — mensaje sin permiso CC |

Ruta: `/opt/cursor/artifacts/screenshots/`

---

## Veredicto obligatorio

# C1 UX NO APTO

**Motivo:** P1-D-UX-01 no resuelto — usuario sin `control_center.view` recibe experiencia bloqueante en `/` en lugar de fallback funcional.

**Apto parcialmente para:** hotfix login C1 (controles 1–3, 17) y preservación integral V2 (controles 9–16) para roles con `control_center.view`.

---

## Acción recomendada (fuera de alcance D — no implementar aquí)

Implementar en convergencia posterior (no C2 aún): componente `HomeEntry` o redirect en `App.tsx`/`CentroControlPage` hacia primera ruta accesible (`/trabajo`, `/directorio`, `/operaciones`) cuando falte `control_center.view`.

---

*Agente D — certificación UX C1. Sin modificación de producto. EN RESERVA.*
