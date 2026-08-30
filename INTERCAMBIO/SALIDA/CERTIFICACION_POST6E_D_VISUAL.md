# CERTIFICACIÓN INDEPENDIENTE POST-6E — AGENTE D (VISUAL / UX / ESPAÑOL)

**Tipo:** Solo lectura (sin modificar central)  
**HEAD exacto:** `3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b` (`3a8b7e7`)  
**Commit:** feat(tramo6e): Centro de Control Ejecutivo único integrado  
**Fecha:** 2026-08-30  
**Agente:** D  
**Entorno:** `http://127.0.0.1:5180` → API `http://127.0.0.1:8000` (worktree `/tmp/cert-post6e-d`)  
**Credenciales admin:** `admin` / `Admin2026*`  
**Usuario limitado:** `ccviewer` / `CCViewer2026*` (rol sin `control_center.view`)

---

## Método

- Aplicación levantada en SHA `3a8b7e7` (backend + frontend del worktree).
- Recorrido visual obligatorio con **Puppeteer + capturas** de las 6 pestañas.
- Complemento API (`GET /api/centro-control/resumen-ejecutivo`) y prueba RBAC usuario limitado.
- **Nota de ruta:** el Centro de Control vive en `/` (índice). `/centro-control` redirige al home autenticado (sin ruta dedicada).

---

## Salida estructurada

```
SHA: 3a8b7e7ee18f81564c3a9f97d9fdf16b289f9b0b

CENTRO CONTROL ÚNICO: PASS (parcial) — Una sola página con 6 pestañas ejecutivas integradas; sin duplicar pantallas CC legacy en el recorrido. Menú lateral conserva enlaces a módulos fuente (observación P2).

RESUMEN: FAIL (P1) — Pestaña operativa pero KPIs del «Resumen ejecutivo» se renderizan como bloque de texto concatenado (sin rejilla/tarjetas legibles). Clase metrics-grid usada sin estilos CSS definidos.

VALOR: PASS — Tarjetas Verificado / Estimado / Potencial / Realizado distinguibles (badges HECHO/INFERENCIA). Nota visible: «POTENCIAL no se suma al valor realizado ni entra en ROI/payback realizado». Potencial no se presenta como dinero obtenido.

OPERACIÓN: PASS — Tarjetas modulares legibles (Empleados IA, Oportunidades, Mi Trabajo, Mesa de Ayuda, etc.). Estados vacíos en español. Drill-down con enlaces «Ver…» / «Ir a…».

IA Y COSTOS: PASS (con P2) — FinOps, TCO, proveedores IA comprensibles. Sin JSON crudo. Estados técnicos NO_CONFIGURADO son veraces (sin credenciales), no placeholders ficticios.

IMPLEMENTACIÓN: PASS (vacío) — «Sin información disponible» + enlace Ver implementación. Espacio vacío amplio por ausencia de datos (P2 cosmético).

SALUD: FAIL (P1) — Estado API muestra «up» (inglés). Auditoría reciente lista acciones técnicas «auth.login» sin etiqueta humana.

ESPAÑOL: FAIL (P1 residual) — «up», «Schedulers», códigos auth.* visibles al ejecutivo. Sin Correlation/Fallback/Timeout/finding/run/cid/trace en UI CC.

NAVEGACIÓN: PASS (con P2) — 6 pestañas claras. Breadcrumb fijo «EMPLEADOS_IA · Centro de operaciones · Módulo Salud» no contextual (P2). /centro-control → / funcional.

DRILL-DOWN: PASS — Enlaces a módulos (/costos-valor, /empleados/:id, /soporte, etc.) comprensibles.

RESPONSIVE: PASS (1280px) — Sin scroll horizontal observado. Rejilla cc-grid-2 adaptable.

DATOS FICTICIOS: PASS — No se detectaron cifras demo engañosas. Valores 0 / «Sin información disponible» / estados reales de configuración (OpenAI NO_CONFIGURADO). Timestamps de empleados coherentes con seed.

USUARIO LIMITADO: PASS — UI: «No tiene permiso para ver el Centro de Control.» API: HTTP 403. Sin exposición de datos globales.

EVIDENCIA VISUAL: /opt/cursor/artifacts/screenshots/cc6e_{resumen,valor,operacion,ia_costos,implementacion,salud}.png

P0: 0

P1: 3
  - P1-CC-01: Resumen ejecutivo — KPIs ilegibles (metrics-grid sin CSS → texto concatenado).
  - P1-CC-02: Salud — «Estado API: up» en inglés (debería localizarse p. ej. «Activo» / «En línea»).
  - P1-CC-03: Salud — Auditoría reciente expone «auth.login» (código interno) sin traducción ejecutiva.

P2: 8
  - P2-01: Breadcrumb estático incorrecto para CC.
  - P2-02: Códigos módulo en títulos (1210, 1280, MB-07, 1270).
  - P2-03: Término «Schedulers» en Salud.
  - P2-04: /centro-control sin alias dedicado (redirige a /).
  - P2-05: Duplicidad menú lateral vs contenido CC.
  - P2-06: Espacio vacío amplio en Implementación sin datos.
  - P2-07: Estados NO_CONFIGURADO en mayúsculas/técnicos (comprensible pero duro).
  - P2-08: ROI / FinOps / HECHO / INFERENCIA como siglas aceptables.

VEREDICTO: NO APTO PARA CONVERGENCIA FINAL
```

---

## Validación por criterio (15 puntos)

| # | Criterio | Resultado |
|---|----------|-----------|
| 1 | Una sola experiencia CC | **PASS** — 6 pestañas en una página |
| 2 | Jerarquía ejecutiva clara | **PARCIAL** — títulos OK; KPIs Resumen fallan |
| 3 | Comprensible sin código | **FAIL** — auth.login, up |
| 4 | Sin JSON crudo | **PASS** |
| 5 | Sin UUID innecesarios | **PASS** |
| 6 | Sin nombres técnicos internos | **FAIL** — auth.login, códigos módulo (P2/P1) |
| 7 | Sin inglés residual esencial | **FAIL** — «up» |
| 8 | Sin tarjetas gigantes injustificadas | **PASS** |
| 9 | Sin espacios vacíos absurdos | **PARCIAL** — Implementación vacía (P2) |
| 10 | Sin scroll horizontal | **PASS** @1280px |
| 11 | Estados sin datos correctos | **PASS** |
| 12 | Indicadores distinguibles | **FAIL** en Resumen; **PASS** en Valor |
| 13 | Drill-down comprensible | **PASS** |
| 14 | Navegación sin duplicidades | **PARCIAL** (P2 menú lateral) |
| 15 | Responsive razonable | **PASS** |

---

## Valor — Verificado / Estimado / Potencial

**PASS visual.** Pestaña Valor:

- Cuatro tarjetas con borde cromático distinto (verificado / estimado / potencial / realizado).
- Badges semánticos HECHO / INFERENCIA.
- Disclaimer explícito sobre exclusión del potencial del realizado y del ROI/payback realizado.
- Clase CSS `potential-excluded` en potencial secundario.

---

## Evidencia visual por pestaña

| Pestaña | Captura | Observación clave |
|---------|---------|-------------------|
| Resumen | `cc6e_resumen.png` | 6 pestañas visibles; KPIs concatenados (P1) |
| Valor | `cc6e_valor.png` | Distinción valor por naturaleza OK |
| Operación | `cc6e_operacion.png` | Módulos operativos en rejilla 2 col |
| IA y costos | `cc6e_ia_costos.png` | FinOps + proveedores; sin JSON |
| Implementación | `cc6e_implementacion.png` | Empty state correcto |
| Salud | `cc6e_salud.png` | «up» + auth.login (P1) |

---

## Usuario limitado

| Prueba | Resultado |
|--------|-----------|
| Login `ccviewer` | OK |
| GET `/api/centro-control/resumen-ejecutivo` | **403** |
| UI en `/` | **«No tiene permiso para ver el Centro de Control.»** |

---

## Datos / placeholders

No se identificaron tarjetas con cifras inventadas que simulen negocio real. Los ceros y mensajes «Sin información disponible» reflejan módulos sin datos en SQLite de prueba. OpenAI «NO CONFIGURADO — sin credenciales» es estado real, no demo.

---

## Notificación gate

### NO APTO PARA CONVERGENCIA FINAL

**P0 = 0 · P1 = 3**

El Centro de Control Ejecutivo post-6E consolida correctamente las 6 dimensiones en una sola experiencia con pestañas y buena pestaña Valor/Operación, pero **requiere corrección de legibilidad del Resumen ejecutivo y localización de estados/auditoría en Salud** antes de convergencia final.

---

*Documento generado en modo solo lectura. Sin cambios en central.*
