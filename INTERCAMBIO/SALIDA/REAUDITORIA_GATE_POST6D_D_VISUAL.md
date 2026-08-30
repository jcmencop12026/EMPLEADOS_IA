# REAUDITORÍA VISUAL/UX POST-6D — AGENTE D

**Tipo:** Solo lectura (sin modificar central)  
**SHA congelado:** `7ce2f343e35ebc75850570af7a1fa071f089bb7a`  
**Fecha:** 2026-08-30  
**Agente:** D (visual/UX)  
**Entorno de prueba:** `http://127.0.0.1:5180` → API `http://127.0.0.1:8000` (worktree `/tmp/reaudit-post6d-d`, SQLite `data/reaudit.db`)  
**Credenciales:** `admin` / `Admin2026*`

---

## Resumen ejecutivo

Revalidación de los **6 P1 visuales/UX** reportados en certificación Tramo 6B. **Cinco de seis están cerrados** con evidencia visual y de código. **Persiste 1 P1 nuevo** en `/comunicaciones` (`Correlation:` en detalle de mensaje), lo que **impide certificar P1=0** para gate 6E.

---

## Salida estructurada

```
SHA: 7ce2f343e35ebc75850570af7a1fa071f089bb7a

ESPAÑOL: PARCIAL — 5/6 P1 originales cerrados; 1 P1 residual en /comunicaciones (Correlation:). Resto de rutas en alcance sin Correlation/Correlation ID/Fallback/Timeout sin traducir.

TRABAJO: PASS — Columna y detalle usan «Correlación» / «ID de correlación». Sin «Correlation» ni «Correlation ID» visibles. Bandeja vacía en entorno de prueba; inspección visual de cabeceras y patrón de detalle confirmada.

SOPORTE: PASS — Listado «Mesa de Ayuda y Soporte» en español. Caso SUP-00001 creado para prueba. Sin términos prohibidos en vista principal.

SELECTOR USUARIO: PASS — En /soporte/casos/:id la asignación usa <select id="responsable-select"> con opciones legibles «admin (admin) — superadmin». No hay campo UUID manual. Botón «Asignar» probado con éxito visual.

AISLAMIENTO TENANT SELECTOR: PASS (servicio + UI) — GET /api/soporte/agentes-asignables filtra por organization_id del usuario (support_service.list_assignable_agents). UI muestra solo agentes de la org actual. Sin usuarios de otro tenant en el desplegable.

OPTIMIZACIÓN: PASS — Título «Optimización y recomendaciones». Columna de tabla «Correlación» (no «Correlation»). Tooltip «?» presente con texto en español. Simulador vacío; sin términos prohibidos.

AUDITOR: PASS — Banner de contexto en detalle empleado usa «Hallazgo:», «Ejecución:», «Correlación:», «Traza:» (no finding:/run:/cid:/trace:). Página /empleados/auditoria con 9 filas; sin prefijos técnicos en banner.

DETALLE EMPLEADO: PASS — Pestaña Modelo: «Modelo de respaldo». Pestaña Límites: «Tiempo límite». Sin «Fallback» ni «Timeout» visibles al usuario.

COMUNICACIONES: FAIL (P1) — En detalle de mensaje (tarjeta «Detalle de comunicación») la etiqueta visible es «Correlation:» (inglés). Confirmado visualmente con mensaje «Prueba reauditoría D» (msg 75546acc-61fc-4b99-850a-f86d2fb2601f). Código: ComunicacionesPage.tsx L283.

COSTOS/VALOR: PASS — Título «Costos y valor». Pestañas y métricas en español (Resumen, Consumos, Capacidad, Concurrencia máxima, Ejecuciones / día, etc.). Sin Correlation/Fallback/Timeout.

P2 VISUALES RESTANTES:
  - P2-1: Densidad de botones en banner Auditor → Fábrica (3 acciones en fila: Capacitar, Ejecutar pruebas, Solicitar reauditoría) — cosmético, no bloquea funcionalidad.
  - P2-2: Tooltip «?» en /optimizacion — presente y útil; no es defecto.
  - P2-3: Bloques JSON visibles (simulador optimización, pestañas Pruebas/Validación empleado) — legibilidad técnica, no P1.
  - P2-4: Layout 1024px — no evaluado en profundidad; sin fallo funcional grave observado.
  - P2-5: Columna «Regla» en /empleados/auditoria muestra códigos internos en inglés (ACTIVE_WITHOUT_CERTIFICATION, NO_KNOWLEDGE_GRANTS).
  - P2-6: Historial de caso soporte puede mostrar «Responsable: <uuid truncado>» tras asignación (formatHistorialDetalle).
  - P2-7: Comunicaciones detalle — «Plantilla v:» (abreviatura técnica menor, distinta de P1 Correlation).

P0: 0

P1: 1
  - P1-D-POST6D-01: Etiqueta «Correlation:» en detalle de comunicación (/comunicaciones → Ver mensaje). Debe ser «Correlación:» o «ID de correlación:».

P2: 7 (clasificados arriba; ninguno exige rediseño para gate salvo observación)

VEREDICTO: NO APTO PARA 6E — P1=1 (umbral gate: P0=0, P1=0). Requiere corrección mínima en ComunicacionesPage.tsx antes de revalidar.
```

---

## Matriz de revalidación — 6 P1 originales (Tramo 6B)

| # | Hallazgo 6B | Estado post-6D | Evidencia |
|---|-------------|----------------|-----------|
| 1 | «Correlation» / «Correlation ID» en `/trabajo` | **CERRADO** | Visual: columna «Correlación», detalle «ID de correlación». Código: `TrabajoPage.tsx` L25, L405. |
| 2 | Términos correlación en `/soporte/casos/:id` | **CERRADO** | Visual: «ID de correlación». Código: `SoporteCasoDetailPage.tsx` L71. |
| 3 | «Correlation» en `/optimizacion` | **CERRADO** | Visual: columna «Correlación». Código: `OptimizacionPage.tsx` L149. |
| 4 | «Fallback» / «Timeout» en detalle Empleado IA | **CERRADO** | Visual: «Modelo de respaldo», «Tiempo límite: 120s». Código: `EmployeeDetailPage.tsx` L446, L461. |
| 5 | Asignación soporte exige UUID manual | **CERRADO** | Visual: selector humano + prueba Asignar. Código: `SoporteCasoDetailPage.tsx` L82-94; API `GET /api/soporte/agentes-asignables`. |
| 6 | Prefijos `finding:`/`run:`/`cid:`/`trace:` en banner Auditor | **CERRADO** | Visual: «Hallazgo:», «Ejecución:», «Correlación:», «Traza:». Código: `EmployeeDetailPage.tsx` L277-281. |

---

## Hallazgo P1 residual (fuera del listado 6B, dentro de alcance)

| ID | Ruta | Texto visible | Severidad |
|----|------|---------------|-----------|
| P1-D-POST6D-01 | `/comunicaciones` → detalle mensaje | `Correlation:` | **P1** |

**Reproducción:**
1. Login como admin.
2. Ir a `/comunicaciones` → pestaña con mensaje «Prueba reauditoría D».
3. Clic «Ver» → tarjeta «Detalle de comunicación» muestra `Correlation: corr-visual-post6d-001`.

**Corrección sugerida (no aplicada — solo lectura):** sustituir `<strong>Correlation:</strong>` por `<strong>Correlación:</strong>` o `<strong>ID de correlación:</strong>` en `frontend/src/pages/ComunicacionesPage.tsx` L283.

---

## Mesa de ayuda — selector y tenant

| Criterio | Resultado |
|----------|-----------|
| Nombre legible | Sí — `nombre` + `username` + `rol` |
| Identificación útil | Sí — formato `admin (admin) — superadmin` |
| Organización correcta | Sí — solo usuarios `organization_id` del solicitante |
| Permisos | Requiere `support.assign`; opciones filtradas por permisos soporte |
| Sin usuarios otro tenant | Sí — verificado en `list_assignable_agents(db, org_id)` |

---

## Recorrido visual (evidencia)

| Paso | Ruta | Resultado |
|------|------|-----------|
| 1 | `/trabajo` | PASS — español correcto |
| 2 | `/soporte` | PASS |
| 3 | `/soporte/casos/4c0241c9-6749-411f-a400-79cdd2c8d255` | PASS — selector + asignación |
| 4 | `/optimizacion` | PASS — «Correlación», tooltip ? |
| 5 | `/empleados/auditoria` | PASS — sin prefijos finding/run/cid/trace |
| 6 | `/empleados/6a30d1e2…?finding_id=af8f87ab…` | PASS — banner español; Modelo/Límites OK |
| 7 | `/comunicaciones` | **FAIL** — `Correlation:` en detalle |
| 8 | `/costos-valor` | PASS — interfaz español |

Screenshots de subagente visual: `/tmp/computer-use/*.webp` (entorno efímero).

---

## Notificación gate

**NO APTO PARA 6E** — permanece **P1=1** (`Correlation:` en `/comunicaciones`). Los 6 P1 de Tramo 6B están resueltos; falta cerrar el residual de comunicaciones para alcanzar P1=0.

---

*Documento generado en modo solo lectura. Sin cambios en `cursor/fase2-central-integracion`, `main` ni `V1`.*
