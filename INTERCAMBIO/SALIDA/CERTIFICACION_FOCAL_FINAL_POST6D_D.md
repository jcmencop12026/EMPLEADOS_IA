# CERTIFICACIÓN FOCAL FINAL POST-6D — AGENTE D

**Tipo:** Solo lectura (sin modificar central)  
**SHA exacto:** `1db7a7e5b0947cf89108b4cf8606a20497d21385`  
**Commit:** `1db7a7e` — fix(gate-post6d): concurrencia CAS auditor/fábrica y cierre P1 B/C/D  
**Fecha:** 2026-08-30  
**Agente:** D (visual/UX focal)  
**Entorno:** `http://127.0.0.1:5180` → API `http://127.0.0.1:8000` (worktree `/tmp/cert-focal-post6d-d`)  
**Credenciales:** `admin` / `Admin2026*`

---

## Objetivo

Cerrar **P1-D-POST6D-01** (`Correlation:` en detalle de comunicaciones) y confirmar que las traducciones ya certificadas **no regresaron**.

---

## Salida estructurada

```
SHA: 1db7a7e5b0947cf89108b4cf8606a20497d21385

COMUNICACIONES: PASS

ID DE CORRELACIÓN: PASS — Tarjeta «Detalle de comunicación» muestra etiqueta «ID de correlación:» (mensaje «Cert focal post-6D D», id bd2da83d-fca3-498f-a176-f4cb373d1355). Valor: corr-focal-post6d-001.

INGLÉS RESIDUAL P1: NINGUNO — No se observó «Correlation:» ni «Correlation ID» en rutas del alcance.

TRABAJO: PASS — Columna «Correlación» y detalle «ID de correlación». Sin regresión.

SOPORTE: PASS — Caso SUP-00001 / id 1de0fcf8-dcbb-44cf-ab58-02300d88b1ba. Sin términos prohibidos.

SELECTOR USUARIO: PASS — Sección Asignación con desplegable «Responsable» y opción legible «admin (admin) — superadmin». Sin entrada manual UUID.

OPTIMIZACIÓN: PASS — Cabecera «Correlación» en tabla (sin datos en entorno de prueba). Sin «Correlation».

AUDITOR: PASS — /empleados/auditoria sin prefijos finding:/run:/cid:/trace:. Banner código: Hallazgo/Ejecución/Correlación/Traza.

DETALLE EMPLEADO: PASS — Modelo: «Modelo de respaldo». Límites: «Tiempo límite». Sin Fallback/Timeout visibles.

REGRESIONES VISUALES: NINGUNA P1/P0 — P2 previos persisten (códigos regla EN en auditoría, JSON técnico, densidad botones fábrica); no bloqueantes.

P0: 0

P1: 0

P2: 7 (heredados; sin nueva regresión funcional)

VEREDICTO: APTO PARA 6E
```

---

## Prueba crítica — P1-D-POST6D-01

| Criterio | Esperado | Observado | Resultado |
|----------|----------|-----------|-----------|
| Etiqueta correlación en detalle | `ID de correlación:` | `ID de correlación:` | **PASS** |
| Etiqueta prohibida | No `Correlation:` | Ausente (búsqueda Ctrl+F: 0 coincidencias) | **PASS** |

**Reproducción visual:**
1. Login `admin` / `Admin2026*`
2. `/comunicaciones` → mensaje «Cert focal post-6D D» → **Ver**
3. Tarjeta «Detalle de comunicación» → etiqueta **`ID de correlación:`** con valor `corr-focal-post6d-001`

**Código (SHA 1db7a7e):** `frontend/src/pages/ComunicacionesPage.tsx` L283:
```tsx
<p><strong>ID de correlación:</strong> {detail.correlation_id ?? "—"}</p>
```

---

## Regresión rápida — traducciones certificadas

| Ruta | Términos prohibidos | Estado |
|------|---------------------|--------|
| `/trabajo` | Correlation, Correlation ID | **PASS** — Correlación / ID de correlación |
| `/soporte/casos/:id` | Correlation, UUID manual | **PASS** — selector humano |
| `/optimizacion` | Correlation | **PASS** — columna Correlación |
| `/empleados/auditoria` | finding:, run:, cid:, trace: | **PASS** |
| Detalle Empleado IA | Fallback, Timeout | **PASS** — Modelo de respaldo / Tiempo límite |

---

## Mesa de ayuda — selector

| Criterio | Resultado |
|----------|-----------|
| Selector humano | **PASS** — desplegable Responsable |
| Sin UUID manual | **PASS** |
| Opción legible | `admin (admin) — superadmin` |

---

## Evidencia visual

| Evidencia | Descripción |
|-----------|-------------|
| Screenshot comunicaciones | `/tmp/computer-use/ef1cb.webp` — «ID de correlación:» visible |
| Screenshot soporte asignación | `/tmp/computer-use/f8e94.webp` — selector humano |

*(Grabación de pantalla solicitada; entorno efímero — evidencia principal en capturas de subagente visual.)*

---

## P2 heredados (no bloqueantes)

- Códigos regla en inglés en tabla Hallazgos (`ACTIVE_WITHOUT_CERTIFICATION`, etc.)
- Bloques JSON en simulador optimización / pestañas pruebas empleado
- Densidad botones banner Auditor → Fábrica
- Historial soporte puede mostrar UUID truncado en detalle de asignación
- Abreviatura «Plantilla v:» en comunicaciones

Ninguno reclasificado como P1 en esta certificación focal.

---

## Notificación gate

### APTO PARA 6E

**P0 = 0 · P1 = 0**

P1-D-POST6D-01 **cerrado**. Traducciones previamente certificadas **sin regresión** en el alcance revisado.

---

*Documento generado en modo solo lectura. Sin cambios en central (`cursor/fase2-central-integracion`, `main`, `V1`).*
