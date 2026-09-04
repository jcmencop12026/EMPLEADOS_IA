# EIAAX — Corrección integral post-rechazo Windows (abd505f)

**Fecha:** 2026-09-03
**Rama:** `cursor/convergencia-comercial-v1-85e4`
**Candidato rechazado:** `abd505f2d9ab66d08f97e37ad8cdb9369214d7a3`

---

## Causa raíz — pantalla blanca Horizonte (P0)

**Archivo:** `frontend/src/components/centroControl/CentroControlEmpresaPanel.tsx`

`useMemo` se invocaba **después** de `return` condicionales (`loading` / `error`). Al seleccionar `?expediente=<uuid>` el componente montaba, retornaba temprano sin hooks, y al completar la carga React lanzaba *Rendered more hooks than during the previous render* → **pantalla en blanco** sin layout ni error visible.

**Corrección:** mover `useMemo` antes de cualquier `return` condicional.

---

## Causa del falso 36/36 Playwright

| Defecto | Por qué no se detectó |
|---|---|
| Pantalla blanca Horizonte | `cert_visual_audit.mjs` línea 114: `status: ... ? "PASS" : "PASS"` — **siempre PASS** |
| Hooks / pageerror | Solo filtraba `ReferenceError` explícitos; no `Rules of Hooks` |
| Logo texto vs oficial | No verificaba `img.brand-mark--hero` |
| Ciclo incompleto | No asertaba las 15 etapas |
| Menú truncado | No inspeccionaba `.nav-label` |
| Scroll excesivo | Umbral inexistente |
| Presentación demo | Enlace a `/presentacion/` en expediente `[DEMO]` → API 403 |

**Corrección:** `scripts/cert_visual_audit.mjs` reescrito con aserciones reales + screenshots 1440×900. Nuevo `scripts/cert_horizonte_e2e.mjs` (recorrido completo).

---

## Correcciones producto (integral)

### P0
- Hooks `CentroControlEmpresaPanel` — pantalla blanca Horizonte
- Rutas presentación demo → `/demo/presentacion/` para expedientes `[DEMO]`

### Login / identidad
- Logo oficial vía ruta directa (`identityAssets.ts`) sin fallback async en Windows
- `BrandMark` inicializa con asset empaquetado
- Login: una sola línea de copy (sin descriptor duplicado)
- Topbar: `productLine` en lugar del descriptor largo truncado

### Centro de Control
- Ciclo **15 etapas** (`lib/cicloOperativo.ts`)
- Primer viewport: situación, KPIs, atención, oportunidades/valor
- `MasterAccess` colapsado en `<details>` (no bloque índice dominante)
- Modo `compact` con empresa en contexto (menos scroll duplicado)

### Menú
- Etiquetas acortadas; ítems secundarios movidos a avanzado
- `.nav-label` con hasta 2 líneas (sin truncado `...`)
- Sidebar 236px

### Densidad / CSS
- `cc-first-viewport`, `cc-ciclo-scroll`, estilos marca login

---

## Windows startup

**Sin cambios de lógica** en `scripts/windows/**`. Solo metadato `integration_sha` actualizado al nuevo SHA.

---

## Evidencia GENERAL

| Prueba | Resultado |
|---|---|
| `cert_visual_audit.mjs` (estricto) | **11/11 PASS** |
| `cert_horizonte_e2e.mjs` | **13/13 PASS** |
| Horizonte `/?expediente=` | Layout + menú + contenido PASS |
| Login logo oficial | PASS |
| Ciclo 15 etapas | PASS |
| Screenshots | `data/evidence/cert-visual/`, `data/evidence/horizonte-e2e/` |

---

## P0 / P1 / P2

| Prioridad | Estado |
|---|---|
| P0 pantalla blanca Horizonte | **0** |
| P0 presentación demo rota | **0** |
| P1 CC primer viewport / ciclo / densidad | **Corregido** |
| P1 login identidad | **Corregido** |
| P1 menú truncado | **Corregido** |
| P2 refinamientos visuales menores | Post-certificación humana |

---

## Comando usuario (sin cambios de startup)

```powershell
Set-Location "D:\EMPLEADOS_IA_CONVERGENCIA"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows\arrancar_convergencia_windows.ps1"
```

**Credenciales:** `org_a_admin` / `DemoA2026!`
**Horizonte:** Centro de Control → `[DEMO] Clínica Demo Horizonte — EVA-2026-0002`
