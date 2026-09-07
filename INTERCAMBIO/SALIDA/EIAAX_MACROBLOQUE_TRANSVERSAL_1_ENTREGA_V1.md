# EIAAX — Macrobloque Transversal 1 — Entrega visual V1 (reorganización estructural)

**Fecha:** 2026-09-07  
**Rama:** `cursor/ajuste-transversal-1-85e4`  
**PR:** #171 — feat(ui): Macrobloque Transversal 1 — normalización visual V1  
**SHA certificado visual anterior:** `8d2a4c3c06bc6bcbe14f8a85be1211f1901b902e`

---

## A. SHA inicial exacto

`47facfca17b17ac78249d793d8980100062258f5`

## B. SHA final exacto

`20dcfd139d687123fc9f707e1bdc15081584ac44`

## C. Archivos modificados (exactos)

| Archivo | Acción |
|---|---|
| `frontend/src/AppShell.tsx` | Modificado |
| `frontend/src/components/centroControl/CentroControlEmpresaPanel.tsx` | Modificado |
| `frontend/src/lib/navIcons.ts` | **Nuevo** |
| `frontend/src/pages/CentroControlPage.tsx` | Modificado |
| `frontend/src/styles/eiaax-experience-v1.css` | Modificado (+266 líneas) |

**Diff:** 5 archivos, +413 / −52 líneas.

## D. Resumen de cambios visuales

| Área | Cambio |
|---|---|
| **Sidebar** | Azul marino con gradiente, ancho 248px, estado activo con borde acento, iconos Unicode legibles (no puntos decorativos) |
| **Login** | Panel marca oscuro con identidad visible, contraste comercial, toggle contraseña proporcionado, enlace “¿Olvidó su contraseña?” como acción secundaria |
| **Centro de Control — cabecera** | Fusión de título, contexto sesión/análisis, selector empresa y acciones (Presentar / Ver empresa) en `cc-unified-header` (2 filas horizontales) |
| **Centro de Control — empresa** | Cuadrícula ejecutiva 4 columnas: Qué sabemos, Qué falta, Lo que encontró EIAAX, Siguiente acción |
| **KPI / ciclo / tabs** | Reglas experience consolidadas: stepper compacto, KPI sin ellipsis forzado, tabs legibles 14–15px |
| **Acciones** | `title` descriptivos en Actualizar, Presentar, Ver empresa y enlaces de siguiente acción |

## E. Cambios estructurales (no solo CSS)

1. **Eliminación de filas apiladas redundantes** en `CentroControlPage`: se retiró `ContextBar` duplicado; contexto migrado a pills horizontales dentro de la cabecera unificada.
2. **Reorden visual empresa**: cabecera → hero empresa (ExecutiveCard existente) → KPI → ciclo → tabs → contenido; resumen ejecutivo en grid 2×2 antes del hero.
3. **Navegación lateral**: mapa de iconos por ruta (`navIcons.ts`) integrado en `AppShell` sin nuevas dependencias.
4. **Consolidación CSS** en `eiaax-experience-v1.css` bajo `.layout.eiaax-v1-transversal.eiaax-v1-experience` para evitar capas `!important` adicionales.

## F. Preservación funcional

- Handlers, rutas, APIs y permisos **sin cambios**.
- Selectores empresa/expediente, periodo, tabs de sección, Presentar, Ver empresa, navegación menú y logout conservan comportamiento previo.
- Datos mostrados provienen de expediente real (`porcentaje_informacion`, `hallazgos`, `confianza_global`, `estado`, `valor_potencial`); **no se inventaron métricas**.

## G. Pruebas realizadas

| Prueba | Resultado |
|---|---|
| Login / logout | PASS (manual + cert) |
| Menú expandir/colapsar | PASS (screenshot 1440) |
| Navegación menú | PASS |
| Selector organización (SUPERADMIN) | No aplicable en sesión admin demo |
| Selector empresa | PASS |
| Centro de Control global | PASS |
| Centro de Control empresa seleccionada | PASS |
| Tabs principales CC | PASS |
| Tabs Cabina (10) | PASS 10/10 |
| Tabs Oportunidad (8) | PASS 8/8 |
| KPI navegables | PASS (sin regresión) |
| Presentar / Ver empresa | PASS (enlaces preservados) |
| `cert_transversal_visual.mjs` | **48/48 PASS** |
| `cert_vista_empresa_flow.mjs` (admin) | **PASS** |
| `test_macrointegral_v1_correcciones.py` | **7/7 PASS** |
| Seed demo comercial | `POST /api/demo-comercial/semilla` |

## H. Resultados build

```
cd frontend && npm run build
✓ built in 1.48s
dist/assets/index-CvLrPom5.css   68.40 kB
dist/assets/index-D2RfhRuX.js   973.01 kB
```

## I. Resultados E2E

| Suite | Resultado | Notas |
|---|---|---|
| `cert_transversal_visual.mjs` | **48/48 visual + 18/18 tabs** | Login configurado/fallback, ciclo 1366/1920, scroll inicial CC empresa = 0 |
| `cert_vista_empresa_flow.mjs` | **PASS** | Requiere `EIAAX_USER=admin EIAAX_PASS='Admin2026*'` |
| `cert_macrointegral_v1.mjs` (orquestador) | **Parcial** | PASS transversal visual; FAIL vista-empresa por credenciales por defecto `org_a_admin`; FAIL build/pytest por invocación `python`/`npm` del orquestador en este entorno (suites individuales PASS) |

## J. Screenshots (evidencia real runtime)

### Certificación principal (`data/evidence/transversal-visual/`)

- 48 capturas @ **1366×768** y **1920×1080**
- Login configurado + fallback
- CC global + empresa seleccionada
- 22 vistas operativas (Cabina, Oportunidades, Empresas)

### Complemento 1440×900 (`data/evidence/transversal-visual-1440/`)

| Archivo | scrollY inicial |
|---|---|
| `1440x900_00-login-configurado.png` | 0 |
| `1440x900_01-centro-control-global.png` | 0 |
| `1440x900_02-centro-control-empresa-seleccionada.png` | 0 |
| `1440x900_07-menu-navegacion.png` | 0 |
| `1440x900_08-tab-valor-empresa.png` | 0 |

**CC empresa 1366×768:** `pageScrollY` inicial y final = **0** (report.json).

## K. Artifact exacto ligado al SHA final

- `data/evidence/transversal-visual/report.json` → `sha: 20dcfd139d687123fc9f707e1bdc15081584ac44`
- `data/evidence/transversal-visual/sha-manifest.json`
- `data/evidence/vista-empresa-flow/` (suite PASS admin)
- `data/evidence/transversal-visual-1440/` (complemento viewport)

## L. Workflow / run

- **Entorno local Cloud Agent:** backend `uvicorn` :8000, frontend Vite :5180
- **Certificación:** `EIAAX_PASS='Admin2026*' EIAAX_BASE='http://127.0.0.1:5180' node scripts/cert_transversal_visual.mjs`
- **CI GitHub:** pendiente re-ejecución post-push en PR #171

## M. Defectos encontrados durante autocontrol

| # | Defecto | Causa |
|---|---|---|
| 1 | Cert fallaba “Sin expediente demo” | BD vacía sin semilla comercial |
| 2 | Login cert con password incorrecta | Default script `Admin2026!` vs bootstrap `Admin2026*` |
| 3 | Filas verticales desperdiciadas en CC | `PageHeader` + `ContextBar` + toolbar + banner apilados |
| 4 | Iconos menú como puntos | `AppShell` usaba `●`/`○` genéricos |
| 5 | Identidad login débil | Contraste/escala insuficiente en panel marca |

## N. Defectos corregidos

- Semilla demo vía API antes de certificación
- Reorganización `cc-unified-header` + grid resumen ejecutivo
- CSS experience: sidebar, login, stepper compacto, pills contexto
- Iconos `navIcons.ts` + integración AppShell
- Tooltips en acciones principales

## O. Regresiones revisadas

- Navegación tabs Cabina/Oportunidad: **sin regresión** (18/18)
- KPI Empresa y Valor potencial en Cabina: **PASS**
- Ciclo 15 etapas: **PASS** 1366 y 1920
- Aislamiento DEMO/REAL: preservado (enlaces Presentar demo vs real)
- Backend / scripts Windows: **no modificados**

## P. Pendientes reales

1. Orquestador `cert_macrointegral_v1.mjs`: alinear credenciales vista-empresa (`admin`) y comando `python3` en entornos Linux.
2. Captura 1440×900 login fallback (disponible en cert @ 1366/1920; complemento 1440 solo configurado).
3. CI PR #171: verificar run post-push.

## Q. Declaración

**NO MERGE — ESPERANDO AUDITORÍA INDEPENDIENTE DE CHATGPT**

---

## Auditoría causal (supervivencia de defectos previos)

| Defecto reportado | Por qué sobrevivía | Corrección aplicada |
|---|---|---|
| Espacio arriba desperdiciado en CC empresa | Layout con 4–5 bloques verticales independientes (`PageHeader`, `ContextBar`, toolbar, banner) | Unificación en `cc-unified-header` + grid resumen antes del hero |
| Identidad login invisible | Panel marca con contraste bajo y escala reducida | Gradiente navy, tipografía 1rem+, logo configurado con área visible |
| Menú con puntos | Implementación literal `●` en `AppShell` | Mapa `navIconFor()` con iconos Unicode por ruta |
| CSS no reflejado en runtime | Reglas dispersas y especificidad insuficiente vs `styles.css` | Consolidación bajo `.layout.eiaax-v1-transversal.eiaax-v1-experience` en capa experience (última cargada) |
